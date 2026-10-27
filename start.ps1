param(
    [string]$Distribution = 'Ubuntu',
    [string]$Python = '/root/satquery/.venv/bin/python',
    [string]$AssetRoot = '',
    [switch]$Check
)
$ErrorActionPreference = 'Stop'
$RepoWindows = $PSScriptRoot.Replace('\', '/')
$RepoLinux = (& wsl.exe -d $Distribution --exec wslpath -a -u $RepoWindows)
if ($LASTEXITCODE -ne 0 -or -not $RepoLinux) { throw 'Could not translate the repository path into WSL.' }
$LaunchArgs = @('-d', $Distribution, '--exec', $Python, "$($RepoLinux.Trim())/paired_lab/launch.py")
if ($AssetRoot) { $LaunchArgs = @('-d', $Distribution, '--exec', 'env', "SATQUERY_ASSET_ROOT=$AssetRoot", $Python, "$($RepoLinux.Trim())/paired_lab/launch.py") }
if ($Check) { $LaunchArgs += '--check' }
& wsl.exe @LaunchArgs
exit $LASTEXITCODE
