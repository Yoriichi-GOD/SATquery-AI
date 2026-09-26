"""Start the connected lab plus the preserved main service when needed."""
import os,sys,time,subprocess,requests
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def healthy(port):
    try:return requests.get(f'http://127.0.0.1:{port}/api/status',timeout=2).status_code==200
    except requests.RequestException:return False
def main():
    if '--check' in sys.argv:
        states={p:healthy(p) for p in [8765,8767]};print(states);return 0 if all(states.values()) else 1
    if healthy(8765) and healthy(8767):print('Already ready: http://localhost:8767');return 0
    children=[];logs=[]
    try:
        for port,folder in [(8765,ROOT.parent),(8767,ROOT)]:
            if healthy(port):continue
            log_dir=Path(os.environ.get('SATQUERY_LOG_DIR', str(ROOT.parent / '.runtime' / 'logs')));log_dir.mkdir(parents=True,exist_ok=True)
            log=(log_dir/f'{port}.log').open('a');logs.append(log)
            child=subprocess.Popen([sys.executable,'-m','uvicorn','server:app','--app-dir',str(folder),'--host','127.0.0.1','--port',str(port),'--no-access-log'],stdout=log,stderr=subprocess.STDOUT);children.append(child)
            for _ in range(60):
                if healthy(port):break
                if child.poll() is not None:raise RuntimeError(f'Service {port} stopped; inspect {log_dir}/{port}.log')
                time.sleep(.5)
            else:raise RuntimeError(f'Service {port} did not become ready.')
        print('Ready: http://localhost:8767 — one page for all connected workflows.',flush=True)
        print('Main workspace remains at http://localhost:8765. Ctrl+C stops only services started by this launcher.',flush=True)
        while all(c.poll() is None for c in children):time.sleep(1)
    except KeyboardInterrupt:pass
    finally:
        for c in children:
            if c.poll() is None:c.terminate()
        for c in children:
            try:c.wait(timeout=10)
            except subprocess.TimeoutExpired:c.kill()
        for log in logs:log.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
