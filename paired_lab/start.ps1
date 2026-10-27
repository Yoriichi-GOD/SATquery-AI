param(
    [string]$Distribution = 'Ubuntu',
    [string]$Python = '/root/satquery/.venv/bin/python',
    [string]$AssetRoot = '',
    [switch]$Check
)
# Delegate to the checkout-relative launcher.
& (Join-Path $PSScriptRoot '../start.ps1') -Distribution $Distribution -Python $Python -AssetRoot $AssetRoot -Check:$Check
exit $LASTEXITCODE
