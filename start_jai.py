"""Participant-operated startup; loopback only, no downloads or acquisition."""
import os
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = Path(os.environ["SATQUERY_BASELINE_ROOT"]).resolve()
FLOOD = Path(os.environ["FLOODLAB_BASELINE_ROOT"]).resolve()
FLOOD_PYTHON = os.environ.get("FLOODLAB_PYTHON", sys.executable)
PORT = int(os.environ.get("JAI_PORT", "8767"))

if not (MAIN / "paired_lab/server.py").is_file() or not (FLOOD / "floodlab/server.py").is_file():
    raise SystemExit("Approved baseline sources are missing")
for port in [PORT, 8770]:
    with socket.socket() as sock:
        if sock.connect_ex(("127.0.0.1", port)) == 0:
            raise SystemExit(f"Port {port} already has a listener; refusing to replace it")

logs = ROOT / ".runtime" / "jai"
logs.mkdir(parents=True, exist_ok=True)
children = []
handles = []
try:
    for name, python, module, port, cwd, factory in [
        ("floodlab", FLOOD_PYTHON, "floodlab.server:app", 8770, FLOOD, False),
        ("satquery-jai", sys.executable, "jai_extension.server:create_app", PORT, ROOT, True),
    ]:
        handle = open(logs / (name + ".log"), "ab", buffering=0)
        handles.append(handle)
        cmd = [python, "-m", "uvicorn", module, "--host", "127.0.0.1", "--port", str(port)]
        if factory:
            cmd.append("--factory")
        process = subprocess.Popen(cmd, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT)
        children.append(process)
        print(name, "PID", process.pid, flush=True)
    print(f"SATQuery JAI: http://127.0.0.1:{PORT}/#flood . Ctrl+C stops both child services.", flush=True)
    while all(p.poll() is None for p in children):
        try:
            children[0].wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
    raise SystemExit("A service exited. Inspect runtime logs; remaining child will be stopped.")
except KeyboardInterrupt:
    pass
finally:
    for process in children:
        if process.poll() is None:
            process.terminate()
    for process in children:
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
    for handle in handles:
        handle.close()
