param(
    [string]$Distribution = 'Ubuntu',
    [string]$Python = '/root/satquery/.venv/bin/python',
    [switch]$Check
)
$ErrorActionPreference = 'Stop'
$RepoLinux = (& wsl.exe -d $Distribution -- wslpath -a -u $PSScriptRoot)
if ($LASTEXITCODE -ne 0 -or -not $RepoLinux) { throw 'Could not translate the repository path into WSL.' }
$LaunchArgs = @('-d', $Distribution, '--', $Python, "$($RepoLinux.Trim())/paired_lab/launch.py")
if ($Check) { $LaunchArgs += '--check' }
& wsl.exe @LaunchArgs
exit $LASTEXITCODE
