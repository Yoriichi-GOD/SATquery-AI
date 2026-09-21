$ErrorActionPreference = "Stop"
Write-Host "SatQuery workspace: http://localhost:8767"
wsl.exe -d Ubuntu -- /root/satquery/.venv/bin/python "/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/launch.py"
