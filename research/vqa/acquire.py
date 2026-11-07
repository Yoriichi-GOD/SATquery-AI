"""Bounded public native-file acquisition; no credentials, model or paid API calls."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import io
from pathlib import Path
import struct
import threading
import time
import zipfile
import zlib

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .core import DATASET_REVISION, image_name, sha256

BASE = f'https://huggingface.co/datasets/xiang709/VRSBench/resolve/{DATASET_REVISION}/'
SIZES = {'Images_train.zip': 8359313269, 'Images_val.zip': 3976656690,
         'VRSBench_train.json': 64923606, 'VRSBench_EVAL_vqa.json': 9358245}


class Budget:
    def __init__(self, maximum=6*1024**3):
        self.maximum, self.bytes = maximum, 0
        self.lock = threading.Lock()

    def consume(self, size):
        with self.lock:
            if self.bytes + size > self.maximum:
                raise ValueError('Declared download budget exhausted')
            self.bytes += size


def chunks(response, budget, maximum):
    total = 0
    for chunk in response.iter_content(1024*1024):
        total += len(chunk)
        if total > maximum:
            raise ValueError('Public source exceeds declared response bound')
        budget.consume(len(chunk))
        yield chunk


def fetch_file(name, destination, budget, progress=lambda message: None):
    if name not in SIZES:
        raise ValueError('Not an allowlisted dataset file')
    target = Path(destination)
    if target.exists():
        if target.stat().st_size != SIZES[name]:
            raise ValueError('Existing source has an unexpected length')
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix+'.part')
    if temporary.exists():
        raise FileExistsError('Incomplete earlier download retained; use an explicit recovery destination')
    with requests.get(BASE+name, stream=True, timeout=(20, 90)) as response:
        if response.status_code != 200:
            raise ValueError(f'Public source HTTP status {response.status_code}')
        with temporary.open('xb') as stream:
            total = 0
            for chunk in chunks(response, budget, SIZES[name]):
                stream.write(chunk)
                total += len(chunk)
                if total % (64*1024*1024) == 0:
                    progress(f'{name}: {total}/{SIZES[name]} bytes')
    if temporary.stat().st_size != SIZES[name]:
        raise ValueError('Incomplete public source')
    temporary.rename(target)
    return target


class RemoteZip(io.RawIOBase):
    def __init__(self, name, budget):
        if name not in ('Images_train.zip', 'Images_val.zip'):
            raise ValueError('Not an allowlisted native image archive')
        self.name, self.size, self.pos, self.budget = name, SIZES[name], 0, budget
        self.sessions = threading.local()

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos+offset if whence == 1 else self.size+offset
        if not 0 <= self.pos <= self.size:
            raise ValueError('ZIP seek exceeds source')
        return self.pos

    def at(self, start, length):
        end = min(start+length, self.size)-1
        if start < 0 or end < start or end-start+1 > 32*1024*1024:
            raise ValueError('Invalid bounded ZIP range')
        if not hasattr(self.sessions, 'session'):
            self.sessions.session = requests.Session()
            retries = Retry(total=4, connect=4, read=3, status=3, backoff_factor=.7,
                            status_forcelist=(429, 500, 502, 503, 504), allowed_methods=('GET',))
            self.sessions.session.mount('https://', HTTPAdapter(max_retries=retries))
        # A unique stable range query prevents signed-redirect cache collisions.
        url = BASE+self.name+f'?download=true&range_start={start}&range_end={end}'
        with self.sessions.session.get(url, headers={'Range': f'bytes={start}-{end}'},
                                       stream=True, timeout=(20, 90)) as response:
            expected = f'bytes {start}-{end}/{self.size}'
            if response.status_code != 206 or response.headers.get('Content-Range') != expected:
                raise ValueError('Source did not honour the exact bounded range')
            raw = b''.join(chunks(response, self.budget, end-start+1))
        if len(raw) != end-start+1:
            raise ValueError('Short ZIP range')
        return raw

    def read(self, length=-1):
        length = min(self.size-self.pos, length if length >= 0 else self.size-self.pos)
        if length <= 0: return b''
        raw = self.at(self.pos, length)
        self.pos += len(raw)
        return raw

    def member(self, info):
        if info.file_size > 16*1024*1024 or info.compress_size > 16*1024*1024:
            raise ValueError('Native image exceeds bounded member size')
        raw = self.at(info.header_offset, 30+len(info.filename.encode())+4096+info.compress_size)
        header = struct.unpack('<4s5H3I2H', raw[:30])
        if header[0] != b'PK\x03\x04' or header[2] & 1:
            raise ValueError('Invalid/encrypted ZIP member')
        start = 30+header[-2]+header[-1]
        end = start+info.compress_size
        if end > len(raw):
            raw += self.at(info.header_offset+len(raw), end-len(raw))
        payload = raw[start:end]
        if info.compress_type == zipfile.ZIP_STORED:
            decoded = payload
        elif info.compress_type == zipfile.ZIP_DEFLATED:
            decoder = zlib.decompressobj(-15)
            decoded = decoder.decompress(payload, info.file_size+1)
            if not decoder.eof:
                raise ValueError('Incomplete or oversized deflated image')
        else:
            raise ValueError('Unsupported native compression')
        if len(decoded) != info.file_size or zlib.crc32(decoded) & 0xffffffff != info.CRC:
            raise ValueError('Native image CRC/length mismatch')
        return decoded


def acquire_images(names, destination, budget, progress=lambda message: None, workers=3):
    """Read original selected PNG members, not re-encoded Dataset Viewer previews."""
    names = list(dict.fromkeys(image_name(n) for n in names))
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    remote = RemoteZip('Images_train.zip', budget)
    with zipfile.ZipFile(remote) as archive:
        mapping = {}
        for info in archive.infolist():
            name = Path(info.filename).name
            if name.endswith('.png'):
                if name in mapping:
                    raise ValueError('Ambiguous native image basename')
                mapping[name] = info
    if set(names)-set(mapping):
        raise ValueError('Selected training filename absent from pinned archive')

    def fetch(name):
        target, info = destination/name, mapping[name]
        if target.exists():
            raw = target.read_bytes()
            if len(raw) != info.file_size or zlib.crc32(raw) & 0xffffffff != info.CRC:
                raise ValueError('Existing native image differs from archive CRC')
        else:
            raw = remote.member(info)
            if not raw.startswith(b'\x89PNG\r\n\x1a\n'):
                raise ValueError('Native member is not PNG')
            target.write_bytes(raw)
        return name, {'path': str(target.resolve()), 'sha256': sha256(target),
                      'bytes': target.stat().st_size, 'zip_crc32': info.CRC,
                      'archive': remote.name, 'member': info.filename}

    records = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch, name): name for name in names}
        try:
            for future in as_completed(futures):
                name, receipt = future.result()
                records[name] = receipt
                if len(records) % 32 == 0 or len(records) == len(names):
                    progress(f'Native training images verified: {len(records)}/{len(names)}; {budget.bytes} bytes transferred')
        except Exception:
            for future in futures:
                future.cancel()
            raise
    return records


def fetch_native_evaluation_archive(destination, budget, expected_sha256, progress=print, deadline=None, stop_event=None):
    """Resumable exact ranges; partially transferred bytes are not accepted as data."""
    target = Path(destination)
    remote = RemoteZip('Images_val.zip', budget)
    if target.exists():
        if target.stat().st_size != remote.size or sha256(target) != expected_sha256:
            raise ValueError('Cached evaluation archive identity mismatch')
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix('.zip.part')
    offset = partial.stat().st_size if partial.exists() else 0
    if offset > remote.size:
        raise ValueError('Partial archive exceeds its pinned native size')
    with partial.open('ab') as stream:
        while offset < remote.size:
            if stop_event is not None and stop_event.is_set(): raise InterruptedError('Worker stopped; native partial archive retained')
            if deadline and time.monotonic() >= deadline: raise TimeoutError('Download wall-time ceiling reached')
            chunk = remote.at(offset, min(8*1024*1024, remote.size-offset))
            stream.write(chunk); stream.flush(); offset += len(chunk)
            progress(f'Native evaluation archive: {offset}/{remote.size} bytes')
    if sha256(partial) != expected_sha256:
        raise ValueError('Full native evaluation archive SHA-256 mismatch; partial retained')
    partial.rename(target)
    return target
