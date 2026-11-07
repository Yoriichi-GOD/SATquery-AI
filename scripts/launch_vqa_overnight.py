"""Wait for the local worker and temporarily prevent automatic system sleep on Windows."""
import argparse
import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--run-id', required=True)
    args = parser.parse_args()
    if not args.run_id.replace('-', '').isalnum(): raise ValueError('Unsafe run identity')
    runtime = ROOT/'.runtime/vqa-20261108'
    runtime.mkdir(parents=True, exist_ok=True)
    if (runtime/'worker.lock').exists(): raise RuntimeError('An existing worker lock must be inspected first')
    if os.name == 'nt':
        drive = ROOT.drive[0].lower()
        linux_root = '/mnt/'+drive+ROOT.as_posix()[2:]
        command = ['wsl.exe', '-d', 'Ubuntu', '--cd', linux_root, '--',
                   '/root/satquery/.venv/bin/python', '-u', '-m', 'research.vqa.campaign', '--run-id', args.run_id]
    else:
        command = [sys.executable, '-u', '-m', 'research.vqa.campaign', '--run-id', args.run_id]
    log = runtime/(args.run_id+'.worker.log')
    if log.exists(): raise FileExistsError('Prior worker log retained; select a fresh run identity')
    awake = False
    try:
        if os.name == 'nt':
            awake = bool(ctypes.windll.kernel32.SetThreadExecutionState(0x80000001))
        with log.open('xb') as stream:
            child = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            receipt = {'run_id': args.run_id, 'launcher_pid': os.getpid(), 'worker_transport_pid': child.pid,
                       'started_utc': datetime.now(timezone.utc).isoformat(), 'system_awake_request': awake}
            path = runtime/(args.run_id+'.launcher.json')
            path.write_text(json.dumps(receipt, indent=2))
            code = child.wait()
            receipt.update(exit_code=code, ended_utc=datetime.now(timezone.utc).isoformat())
            path.write_text(json.dumps(receipt, indent=2))
            raise SystemExit(code)
    finally:
        if os.name == 'nt' and awake:
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__ == '__main__': main()
