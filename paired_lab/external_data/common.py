"""Shared integrity and bounded-I/O primitives; no model imports."""
import hashlib
import json
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

CHUNK = 1024 * 1024
IDENTIFIER = re.compile(r'^[a-f0-9]{32}$')


class DataError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)


def fail(code, message):
    raise DataError(code, message)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path, check=lambda: None):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(CHUNK):
            check()
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def read_json(path, limit=16 * CHUNK):
    if Path(path).stat().st_size > limit:
        fail('METADATA_TOO_LARGE', 'Metadata exceeds the bounded JSON limit.')
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def identifier(value):
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        fail('INVALID_ID', 'Use a registered dataset, file or job ID.')
    return value


def safe_name(value):
    if not isinstance(value, str) or len(value) > 240 or not value or '\\' in value or ':' in value:
        fail('UNSAFE_PATH', 'Use a relative dataset name with forward slashes and no drive prefix.')
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in ('', '.', '..') for p in value.split('/')) or any(ord(c) < 32 for c in value):
        fail('UNSAFE_PATH', 'Absolute paths, traversal and control characters are not accepted.')
    return path.as_posix()


def contained(root, relative):
    root = Path(root).resolve()
    path = root / safe_name(relative)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
        fail('SYMLINK_NOT_ALLOWED', 'Dataset paths cannot traverse symbolic links.')
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        fail('UNSAFE_PATH', 'Path escapes the registered dataset.')
    return resolved


def copy_stream(source, target, check=lambda: None):
    with Path(source).open('rb') as src, Path(target).open('xb') as dst:
        while chunk := src.read(CHUNK):
            check()
            dst.write(chunk)


def require_space(root, incoming, reserve=256 * CHUNK):
    if shutil.disk_usage(root).free < incoming + reserve:
        fail('INSUFFICIENT_DISK', 'Not enough free disk for this operation plus the reserved safety margin.')
