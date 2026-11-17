param(
    [string]$PythonSourceDir = 'C:\Program Files\PostgreSQL\18\pgAdmin 4\python'
)
# Environnement autonome hors ligne pour le scanner ; le .venv historique reste intact.
$ErrorActionPreference = 'Stop'
$racine = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $racine '.venv-scanner'
$packagesSource = Join-Path $racine '.venv/Lib/site-packages'
if (-not (Test-Path -LiteralPath (Join-Path $PythonSourceDir 'python313.zip'))) {
    throw 'Python embarqué 3.13 absent. Fournir -PythonSourceDir avec un runtime installé compatible.'
}
$paquets = @('_pytest','pytest','pluggy','iniconfig','packaging','pygments','colorama')
foreach ($paquet in $paquets) {
    if (-not (Test-Path -LiteralPath (Join-Path $packagesSource $paquet))) {
        throw "Dépendance locale de test absente : $paquet"
    }
}
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Get-ChildItem -LiteralPath $PythonSourceDir -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
}
$site = Join-Path $destination 'Lib/site-packages'
New-Item -ItemType Directory -Force -Path $site | Out-Null
foreach ($paquet in $paquets) {
    Copy-Item -LiteralPath (Join-Path $packagesSource $paquet) -Destination $site -Recurse -Force
    Get-ChildItem -LiteralPath $packagesSource -Directory -Filter "$paquet-*.dist-info" | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $site -Recurse -Force
    }
}
Copy-Item -LiteralPath (Join-Path $packagesSource 'py.py') -Destination $site -Force
@('python313.zip', '.', 'Lib/site-packages', 'import site') | Set-Content -LiteralPath (Join-Path $destination 'python313._pth') -Encoding ascii
& (Join-Path $destination 'python.exe') -c 'import sys,pytest; print(sys.version); print(pytest.__version__)'
if ($LASTEXITCODE -ne 0) { throw 'Verification de l environnement scanner echouee' }
Write-Output "Environnement pret : $destination\python.exe"
