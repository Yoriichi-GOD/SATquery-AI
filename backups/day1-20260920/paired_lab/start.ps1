$ErrorActionPreference = "Stop"
Write-Host "SATquery connected lab: http://localhost:8767"
Write-Host "VQA, NDVI and paired workflows are available there. The original workspace stays separate."
wsl.exe -d Ubuntu -- /root/satquery/.venv/bin/python "/mnt/c/Users/nrgen/.codex/scratch/SATquery AI/paired_lab/launch.py"
