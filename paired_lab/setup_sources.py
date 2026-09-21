from pathlib import Path
import requests,subprocess,json
D=Path('/root/satquery/paired-lab')
if not (D/'ConfigILM').exists():subprocess.run(['git','clone','--depth','1','https://github.com/lhackel-tub/ConfigILM.git',str(D/'ConfigILM')],check=True)
r=requests.get('https://git.tu-berlin.de/api/v4/projects/rsim%2Freben-training-scripts/repository/tree',params={'recursive':'true','per_page':100},timeout=40)
print('gitlab tree',r.status_code,flush=True)
if r.ok:
    for p in r.json():
        name=p['path']
        if name.endswith('.py'):
            t=requests.get('https://git.tu-berlin.de/rsim/reben-training-scripts/-/raw/main/'+name,timeout=30).text
            out=D/'reben-source'/name;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(t)
            if any(x in t for x in ['Normalize','normaliz','transforms']):print(name+'\n'+t[:18000],flush=True)
subprocess.run(['/root/satquery/.venv/bin/python','-m','pip','install','--target',str(D/'deps'),'--no-deps','timm==1.0.19','einops==0.8.1','lmdb==1.7.3','pandas==2.3.2','pyarrow==21.0.0','python-dateutil==2.9.0.post0','pytz==2025.2','tzdata==2025.2'],check=True)
print('Isolated dependencies installed',flush=True)
