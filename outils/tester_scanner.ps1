$ErrorActionPreference = 'Stop'
$racine = Split-Path $PSScriptRoot -Parent
$python = Join-Path $racine '.venv-scanner/python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Lancer outils/preparer_env_scanner.ps1 avant les tests.'
}
# Dossier neuf dans le projet : aucun ancien temporaire n'est supprimé.
$tempTests = Join-Path (Join-Path $racine '.tmp') ('pytest-scanner-' + [guid]::NewGuid().ToString('N'))
Push-Location $racine
try {
    & $python -m pytest outils -q -p no:cacheprovider --basetemp=$tempTests
    $codeSortie = $LASTEXITCODE
} finally { Pop-Location }
exit $codeSortie
