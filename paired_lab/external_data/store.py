"""Private upload inventory; opaque IDs, resumable bounded chunks, safe ZIP intake."""
import os
import stat
import threading
import uuid
import zipfile
from pathlib import Path
from .common import CHUNK, contained, copy_stream, digest, fail, identifier, read_json, require_space, safe_name, utc, write_json
from .raster import inspect_raster

SUFFIXES={'.tif','.tiff','.zip','.json','.csv','.xml','.txt','.md'}
ROLES={'input','reference','prediction','metadata'}


class DatasetStore:
    def __init__(self, root, cap=None, reserve=256*CHUNK,recover=True):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.cap=int(cap or os.environ.get('SATQUERY_DATASET_MAX_BYTES',4*1024**3))
        self.reserve=reserve;self.upload_lock=threading.Lock();self.lock=threading.RLock()
        # Recover persistent job state; never label interrupted operations complete.
        for path in self.root.glob('*/dataset_manifest.json') if recover else []:
            try:
                value=read_json(path)
                if value['state'] in ('INSPECTING','PROCESSING'):
                    value.update(state='INTERRUPTED',message='Prior worker stopped. Re-run inspection; original files retained.')
                    write_json(path,value)
            except (OSError,ValueError,KeyError):continue

    def directory(self, did):
        return contained(self.root,identifier(did))

    def get(self, did):
        path=self.directory(did)/'dataset_manifest.json'
        if not path.is_file():fail('DATASET_NOT_FOUND','Dataset not found.')
        return read_json(path)

    def save(self, value):
        value['updated_utc']=utc();write_json(self.directory(value['id'])/'dataset_manifest.json',value)

    def create(self, name):
        if not isinstance(name,str) or not 1<=len(name.strip())<=120:fail('INVALID_NAME','Dataset name must have 1–120 characters.')
        require_space(self.root,0,self.reserve)
        did=uuid.uuid4().hex;directory=self.directory(did);directory.mkdir()
        value=dict(id=did,name=name.strip(),state='UPLOADING',created_utc=utc(),files=[],failures=[],revision=None,
            limits=dict(dataset_bytes=self.cap,chunk_bytes=8*CHUNK,files=256,disk_reserve_bytes=self.reserve),
            source_authenticity='Not independently verified; retain acquisition/licence records.')
        self.save(value);return value

    def list(self):
        return [dict(id=v['id'],name=v['name'],state=v['state'],files=len(v['files']),updated_utc=v['updated_utc'])
            for path in sorted(self.root.glob('*/dataset_manifest.json'),reverse=True) for v in [read_json(path)]]

    def register_file(self,did,name,size,role='input',expected_sha256=None):
        name=safe_name(name);suffix=Path(name).suffix.lower()
        if suffix not in SUFFIXES:fail('UNSUPPORTED_FILE','Only TIFF, ZIP and bounded companion metadata are accepted.')
        if role not in ROLES:fail('INVALID_ROLE','Choose input, reference, prediction or metadata.')
        if isinstance(size,bool) or not isinstance(size,int) or size<1:fail('INVALID_SIZE','Declare a positive file size.')
        if expected_sha256 is not None and (len(expected_sha256)!=64 or any(c not in '0123456789abcdef' for c in expected_sha256)):fail('INVALID_HASH','Expected SHA-256 must be 64 lowercase hexadecimal characters.')
        with self.lock:
            value=self.get(did)
            if value['state'] in ('INSPECTING','PROCESSING'):fail('DATASET_BUSY','Wait or cancel the current dataset operation.')
            if len(value['files'])>=256:fail('FILE_COUNT_LIMIT','The dataset has reached its 256-file limit.')
            if any(f['name']==name for f in value['files']):fail('DUPLICATE_NAME','This relative file name is already registered; resume its upload instead.')
            total=sum(f['bytes'] for f in value['files'])+size
            if total>self.cap:fail('DATASET_CAP','The configured dataset storage cap would be exceeded.')
            remaining=sum(max(0,f['bytes']-f.get('received',0)) for f in value['files'])+size
            require_space(self.root,remaining,self.reserve)
            fid=uuid.uuid4().hex;folder=self.directory(did)/'files'/fid;folder.mkdir(parents=True)
            row=dict(id=fid,name=name,bytes=size,role=role,state='UPLOADING',received=0,
                path='files/'+fid+'/original'+suffix,expected_sha256=expected_sha256)
            value['files'].append(row);value.update(state='UPLOADING',revision=None);self.save(value);return row

    def file(self,did,fid):
        identifier(fid);value=self.get(did)
        found=next((f for f in value['files'] if f['id']==fid),None)
        if found is None:fail('FILE_NOT_FOUND','File is not registered in this dataset.')
        return value,found,contained(self.directory(did),found['path'])

    def upload_target(self,did,fid,offset):
        value,row,path=self.file(did,fid)
        if value['state'] in ('INSPECTING','PROCESSING'):fail('DATASET_BUSY','Dataset is being read by a worker.')
        if row['state'] not in ('UPLOADING','INTERRUPTED'):fail('ORIGINAL_IMMUTABLE','Completed originals cannot be overwritten.')
        part=path.with_suffix(path.suffix+'.part')
        actual=part.stat().st_size if part.exists() else 0
        if offset!=actual:fail('OFFSET_MISMATCH',f'Resume this file at byte {actual}.')
        require_space(self.root,min(8*CHUNK,row['bytes']-actual),self.reserve)
        return row,part

    def record_chunk(self,did,fid,received):
        with self.lock:
            value,row,_=self.file(did,fid);row['received']=received;row['state']='UPLOADING';self.save(value)
        return row

    def finish_file(self,did,fid):
        with self.lock:
            value,row,path=self.file(did,fid)
            if row['state'] in ('STORED','INSPECTED'):return row
            part=path.with_suffix(path.suffix+'.part')
            if not part.is_file() or part.stat().st_size!=row['bytes']:fail('INCOMPLETE_UPLOAD','Uploaded bytes do not match the declared size.')
            os.replace(part,path);row.update(state='STORED',received=row['bytes']);self.save(value);return row

    def import_local(self,did,source,role='input'):
        source=Path(source)
        # Only the operator CLI accepts paths; HTTP never accepts a filesystem path.
        if source.is_symlink():fail('SYMLINK_NOT_ALLOWED','Local imports cannot use symbolic links.')
        paths=sorted(source.rglob('*')) if source.is_dir() else [source]
        for file in paths:
            if file.is_symlink():fail('SYMLINK_NOT_ALLOWED','Directory contains a symbolic link.')
            if not file.is_file():continue
            name=file.relative_to(source).as_posix() if source.is_dir() else file.name
            row=self.register_file(did,name,file.stat().st_size,role)
            _,part=self.upload_target(did,row['id'],0);copy_stream(file,part)
            self.record_chunk(did,row['id'],row['bytes']);self.finish_file(did,row['id'])
        return self.get(did)

    def cancel_uploads(self,did):
        if not self.upload_lock.acquire(False):fail('UPLOAD_BUSY','Wait for the current bounded chunk, then cancel.')
        try:
            with self.lock:
                value=self.get(did)
                for row in value['files']:
                    if row['state'] in ('UPLOADING','INTERRUPTED'):
                        path=contained(self.directory(did),row['path']);path.with_suffix(path.suffix+'.part').unlink(missing_ok=True)
                        row.update(state='CANCELLED',received=0)
                value['state']='CANCELLED';self.save(value);return value
        finally:self.upload_lock.release()


def extract_zip(store,dataset,row,check):
    root=store.directory(dataset['id']);path=contained(root,row['path']);pending=[]
    try:
        with zipfile.ZipFile(path) as archive:
            members=archive.infolist()
            if len(members)>256:fail('ARCHIVE_ENTRY_LIMIT','ZIP exceeds 256 entries.')
            total=sum(f['bytes'] for f in dataset['files'])
            names={f['name'] for f in dataset['files']}
            for entry in members:
                check();name=safe_name(entry.filename.rstrip('/'))
                mode=(entry.external_attr>>16)&0xffff
                if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0,stat.S_IFREG,stat.S_IFDIR)):
                    fail('ARCHIVE_SYMLINK','ZIP links and special files are forbidden.')
                if entry.flag_bits&1:fail('ENCRYPTED_ARCHIVE','Encrypted ZIP files are not accepted.')
                if entry.is_dir():continue
                if Path(name).suffix.lower() not in SUFFIXES- {'.zip'}:fail('UNSUPPORTED_ARCHIVE_FILE','Nested archives/executables and unsupported members are forbidden.')
                if entry.file_size/max(1,entry.compress_size)>100:fail('ARCHIVE_RATIO','ZIP decompression ratio exceeds 100:1.')
                total+=entry.file_size
                if total>store.cap or len(dataset['files'])+len(pending)>=256:fail('ARCHIVE_EXPANSION_CAP','ZIP expansion exceeds the configured dataset cap.')
                archive_name=row['name']+'/'+name
                if archive_name in names:fail('DUPLICATE_ARCHIVE_PATH','ZIP contains duplicate member names.')
                names.add(archive_name);pending.append((entry,archive_name))
            require_space(root,total-sum(f['bytes'] for f in dataset['files']),store.reserve)
            created=[];original_count=len(dataset['files'])
            try:
                for entry,name in pending:
                    check();fid=uuid.uuid4().hex;folder=root/'files'/fid;folder.mkdir()
                    target=folder/('original'+Path(name).suffix.lower());written=0
                    created.append(target)
                    with archive.open(entry) as src,target.open('xb') as dst:
                        while chunk:=src.read(CHUNK):
                            check();written+=len(chunk)
                            if written>entry.file_size:fail('ARCHIVE_SIZE_MISMATCH','Expanded member exceeds declared size.')
                            dst.write(chunk)
                    if written!=entry.file_size:fail('ARCHIVE_SIZE_MISMATCH','Expanded member is truncated.')
                    dataset['files'].append(dict(id=fid,name=name,bytes=written,received=written,role=row['role'],state='STORED',
                        path=target.relative_to(root).as_posix(),archive_parent=row['id']))
            except BaseException:
                del dataset['files'][original_count:]
                for target in created:
                    target.unlink(missing_ok=True);target.parent.rmdir()
                raise
    except zipfile.BadZipFile:fail('CORRUPT_ARCHIVE','The ZIP directory or an expanded member failed integrity checks.')


def inspect_dataset(store,did,check=lambda:None,progress=lambda v:None,full=True):
    dataset=store.get(did);dataset.update(state='INSPECTING',failures=[]);store.save(dataset)
    try:
        if not dataset['files']:fail('EMPTY_DATASET','Register and finish at least one file before inspection.')
        if any(f['state'] not in ('STORED','INSPECTED','REJECTED') for f in dataset['files']):fail('INCOMPLETE_UPLOAD','Finish all registered uploads before inspection.')
        for row in list(dataset['files']):
            check()
            if Path(row['name']).suffix.lower()=='.zip' and not row.get('expanded'):
                extract_zip(store,dataset,row,check);row['expanded']=True;store.save(dataset)
        for i,row in enumerate(dataset['files']):
            check();progress(dict(stage='Hashing and inspecting '+row['name'],file=i+1,files=len(dataset['files'])))
            path=contained(store.directory(did),row['path'])
            row['sha256']=digest(path,check)
            try:
                if row.get('expected_sha256') and row['sha256']!=row['expected_sha256']:fail('DATASET_HASH_MISMATCH','Original bytes differ from the supplied SHA-256.')
                suffix=Path(row['name']).suffix.lower()
                if suffix in ('.tif','.tiff'):row['raster']=inspect_raster(path,check,progress,full)
                elif suffix!='.zip' and row['bytes']>16*CHUNK:fail('METADATA_TOO_LARGE','Companion metadata exceeds 16 MiB.')
                row['state']='INSPECTED';row.pop('error',None)
            except Exception as exc:
                if getattr(exc,'code',None)=='CANCELLED':raise
                row.update(state='REJECTED',error=dict(code=getattr(exc,'code','INSPECTION_FAILED'),message=str(exc)))
                dataset['failures'].append(dict(file_id=row['id'],**row['error']))
            store.save(dataset)
        import hashlib,json
        canonical=[dict(id=f['id'],sha256=f['sha256'],role=f['role']) for f in dataset['files']]
        dataset['revision']=hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()
        dataset['state']='INSPECTED_WITH_FAILURES' if dataset['failures'] else 'INSPECTED'
        store.save(dataset);return dataset
    except BaseException as exc:
        dataset['state']='CANCELLED' if getattr(exc,'code',None)=='CANCELLED' else 'PROCESSING_FAILED'
        dataset['failures'].append(dict(code=getattr(exc,'code','INSPECTION_FAILED'),message=str(exc)));store.save(dataset);raise
