param([Parameter(Mandatory=$true)][string]$ImagePath, [switch]$Detail)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime]
$null = [Windows.Storage.Streams.IRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]
$asTask = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Await-WinRT($operation, [Type]$type) {
    $task = $asTask.MakeGenericMethod($type).Invoke($null, @($operation))
    $task.GetAwaiter().GetResult()
}
$file = Await-WinRT ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
$stream = Await-WinRT ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
try {
    $decoder = Await-WinRT ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
    if ($decoder.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or $decoder.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) {
        throw 'Image trop grande pour Windows OCR : réduisez ses dimensions.'
    }
    # Petites photos : agrandir avant reconnaissance, sans modifier le fichier source.
    $facteur = if ([Math]::Max($decoder.PixelWidth, $decoder.PixelHeight) -le 800) {
        [Math]::Min(4.0, 1600.0 / [Math]::Max($decoder.PixelWidth, $decoder.PixelHeight))
    } else { 1.0 }
    $transform = [Windows.Graphics.Imaging.BitmapTransform]::new()
    $transform.ScaledWidth = [uint32][Math]::Round($decoder.PixelWidth * $facteur)
    $transform.ScaledHeight = [uint32][Math]::Round($decoder.PixelHeight * $facteur)
    $bitmap = Await-WinRT ($decoder.GetSoftwareBitmapAsync(
        [Windows.Graphics.Imaging.BitmapPixelFormat]::Bgra8,
        [Windows.Graphics.Imaging.BitmapAlphaMode]::Premultiplied,
        $transform,
        [Windows.Graphics.Imaging.ExifOrientationMode]::RespectExifOrientation,
        [Windows.Graphics.Imaging.ColorManagementMode]::DoNotColorManage
    )) ([Windows.Graphics.Imaging.SoftwareBitmap])
    $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    if ($null -eq $engine) { throw 'Aucune langue OCR Windows disponible.' }
    try {
        $result = Await-WinRT ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
        if ($Detail) {
            $lignes = @($result.Lines | ForEach-Object {
                @{texte=$_.Text; mots=@($_.Words | ForEach-Object {
                    @{texte=$_.Text; x=$_.BoundingRect.X; y=$_.BoundingRect.Y;
                      largeur=$_.BoundingRect.Width; hauteur=$_.BoundingRect.Height}
                })}
            })
            @{lignes=$lignes; facteur=$facteur; largeur=$bitmap.PixelWidth;
              hauteur=$bitmap.PixelHeight; langue=$engine.RecognizerLanguage.LanguageTag;
              moteur='Windows.Media.Ocr'; version='geometrie-v1'} | ConvertTo-Json -Depth 8 -Compress
        } else {
            @($result.Lines | ForEach-Object { $_.Text }) | ConvertTo-Json -Compress
        }
    } finally { $bitmap.Dispose() }
} finally { $stream.Dispose() }
