"""Start the consolidated local research release without modifying existing services."""
import argparse,os,socket,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=18968);p.add_argument('--flood-port',type=int,default=18970)
    p.add_argument('--flood-python',default=os.environ.get('FLOODLAB_PYTHON',sys.executable));a=p.parse_args()
    if a.port==a.flood_port:raise SystemExit('The two services need different ports')
    for port in [a.port,a.flood_port]:
        if not 1024<=port<=65535:raise SystemExit('Use a local port from1024 to65535')
        with socket.socket() as sock:
            if sock.connect_ex(('127.0.0.1',port))==0:raise SystemExit(f'Port{port} already occupied; no service replaced')
    flood=ROOT/'components/floodlab';logs=ROOT/'.runtime/research-release';logs.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'SATQUERY_BASELINE_ROOT':str(ROOT),'FLOODLAB_BASELINE_ROOT':str(flood),
        'FLOODLAB_UPSTREAM':f'http://127.0.0.1:{a.flood_port}','JAI_PORT':str(a.port),
        'SATQUERY_CASE_RESEARCH_ROOT':str(ROOT/'research/results/case-campaign-20261107'),
        'JAI_TERRAIN_EXPOSURE_ROOT':str(ROOT/'.runtime/research-release/terrain-exposure')}
    processes=[];handles=[]
    try:
        for name,python,module,port,cwd,factory in [('floodlab',a.flood_python,'floodlab.server:app',a.flood_port,flood,False),
            ('satquery',sys.executable,'jai_extension.server:create_app',a.port,ROOT,True)]:
            handle=(logs/(name+'.log')).open('ab',buffering=0);handles.append(handle)
            cmd=[python,'-m','uvicorn',module,'--host','127.0.0.1','--port',str(port)]+(['--factory'] if factory else [])
            processes.append(subprocess.Popen(cmd,cwd=cwd,env=env,stdout=handle,stderr=subprocess.STDOUT))
            print(name,'PID',processes[-1].pid,flush=True)
        print(f'SATQuery http://127.0.0.1:{a.port}/ | Research /api/research/cases | Flood response http://127.0.0.1:{a.flood_port}/',flush=True)
        while all(child.poll() is None for child in processes):
            try:processes[0].wait(timeout=1)
            except subprocess.TimeoutExpired:pass
        raise SystemExit('A service exited; inspect .runtime/research-release logs')
    except KeyboardInterrupt:pass
    finally:
        for child in processes:
            if child.poll() is None:child.terminate()
        for child in processes:
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:child.kill();child.wait()
        for handle in handles:handle.close()

if __name__=='__main__':main()
