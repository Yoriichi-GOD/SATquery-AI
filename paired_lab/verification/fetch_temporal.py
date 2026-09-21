from pathlib import Path
import json,zipfile,hashlib
from huggingface_hub import hf_hub_download,HfApi
D=Path('/root/satquery/paired-lab/levir-mci');D.mkdir(exist_ok=True)
repo='lcybuaa/LEVIR-MCI';rev=HfApi().dataset_info(repo).sha
p=Path(hf_hub_download(repo_id=repo,filename='LEVIR-MCI-dataset.zip',repo_type='dataset',revision=rev,local_dir=str(D)))
with zipfile.ZipFile(p) as z:
 names=z.namelist();(D/'archive-files.json').write_text(json.dumps(names,indent=2))
 for name in names:
  if name.endswith(('.json','.txt')) and not name.startswith('__MACOSX'):
   dest=D/'metadata'/Path(name).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(z.read(name))
(D/'manifest.json').write_text(json.dumps({'repo':repo,'revision':rev,'archive':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':len(names)},indent=2));print('DOWNLOADED',len(names),[n for n in names if n.endswith(('.json','.txt'))][:30],flush=True)
