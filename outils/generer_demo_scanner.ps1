# Images de contrôle artificielles, pas des photos terrain ni une mesure de précision OCR.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$racine = Split-Path $PSScriptRoot -Parent
$sortie = Join-Path $racine 'data/scanner_demo'
New-Item -ItemType Directory -Force -Path $sortie | Out-Null
$cas = @(
    @{id='verifie'; lignes=@('Nutella', '3017620422003', 'Pour 100 g', 'Energie 539 kcal', 'Lipides 30,9 g', 'Sucres 56,3 g', 'Sel 0,107 g')},
    @{id='non_verifie'; lignes=@('Biscuits de demonstration', 'Marque inconnue', 'Pour 100 g', 'Energie 400 kcal', 'Lipides 10 g', 'Sucres 20 g', 'Sel 0,5 g')},
    @{id='illisible'; lignes=@('Photographie de demonstration', 'Un emballage sans tableau nutritionnel')}
)
$font = [System.Drawing.Font]::new('Arial', 24)
try {
    foreach ($casImage in $cas) {
        $bmp = [System.Drawing.Bitmap]::new(1100, 700)
        $g = [System.Drawing.Graphics]::FromImage($bmp)
        try {
            $g.Clear([System.Drawing.Color]::White)
            $y = 30
            foreach ($ligne in $casImage.lignes) {
                $g.DrawString($ligne, $font, [System.Drawing.Brushes]::Black, 30, $y)
                $y += 65
            }
            $bmp.Save((Join-Path $sortie ($casImage.id + '.png')), [System.Drawing.Imaging.ImageFormat]::Png)
        } finally { $g.Dispose(); $bmp.Dispose() }
    }
} finally { $font.Dispose() }
$manifest = @{
    type_images='synthetiques'
    provenance='Images de controle generees par outils/generer_demo_scanner.ps1. Valeurs Nutella : export local Open Food Facts (ODbL), 16/11/2026. Ne prouve pas la precision sur photos reelles.'
    cas=@(
        @{id='verifie';photo='verifie.png';statut_attendu='verifie';code_attendu='3017620422003'},
        @{id='non_verifie';photo='non_verifie.png';statut_attendu='non_verifie'},
        @{id='illisible';photo='illisible.png';statut_attendu='illisible'}
    )
}
$manifest | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 (Join-Path $sortie 'manifest.json')
Write-Output "Images de controle et manifest generes dans $sortie"
