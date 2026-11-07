$ErrorActionPreference = 'Stop'
wsl.exe -d Ubuntu --cd /mnt/c/Users/nrgen/.codex/scratch/satquery-flood-lab -- /root/satquery-flood-lab/venv/bin/python -m uvicorn floodlab.server:app --host 127.0.0.1 --port 8770
