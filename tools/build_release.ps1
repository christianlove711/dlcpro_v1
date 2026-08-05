param(
    [string]$ReleaseTag = "2026-08-05"
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$releaseBase = Join-Path $projectRoot "release"
$releaseName = "DLCProControl_$ReleaseTag"
$releaseRoot = Join-Path $releaseBase $releaseName
$zipPath = "$releaseRoot.zip"

if (Test-Path -LiteralPath $releaseRoot) {
    throw "Release directory already exists. Use another -ReleaseTag: $releaseRoot"
}
if (Test-Path -LiteralPath $zipPath) {
    throw "Release ZIP already exists. Use another -ReleaseTag: $zipPath"
}

Push-Location $projectRoot
try {
    python -m pytest tests daq_pc/tests -q
    if ($LASTEXITCODE -ne 0) { throw "Tests failed; release aborted" }

    python -m PyInstaller --clean --noconfirm DLCProControl.spec
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed" }

    New-Item -ItemType Directory -Force -Path $releaseRoot | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $releaseRoot "docs") | Out-Null
    Copy-Item -LiteralPath (Join-Path $projectRoot "dist\DLCProControl") -Destination $releaseRoot -Recurse
    Copy-Item -LiteralPath (Join-Path $projectRoot "docs\USER_GUIDE.md") -Destination (Join-Path $releaseRoot "docs")
    Copy-Item -LiteralPath (Join-Path $projectRoot "docs\RELEASE_NOTES_2026-08-05.md") -Destination (Join-Path $releaseRoot "docs")
    Copy-Item -LiteralPath (Join-Path $projectRoot "reports\adc_peak_balance\ALGORITHM_REPORT.md") -Destination (Join-Path $releaseRoot "docs\ADC_00MODE_ALGORITHM.md")

    $readme = @(
        "DLCProControl $ReleaseTag",
        "",
        "1. Start DLCProControl\DLCProControl.exe.",
        "2. Read docs\USER_GUIDE.md before first use.",
        "3. The FPGA bitstream is not bundled; select a verified .bit file in the ADC window.",
        "4. FPGA programming does not open Vivado GUI, but Vivado and USB-JTAG are required."
    ) -join [Environment]::NewLine
    Set-Content -LiteralPath (Join-Path $releaseRoot "README.txt") -Value $readme -Encoding utf8

    $manifestPath = Join-Path $releaseRoot "SHA256SUMS.txt"
    Get-ChildItem -LiteralPath $releaseRoot -Recurse -File |
        Where-Object { $_.FullName -ne $manifestPath } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($releaseRoot.Length + 1).Replace("\", "/")
            $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
            "$hash  $relative"
        } | Set-Content -LiteralPath $manifestPath -Encoding ascii

    Compress-Archive -LiteralPath $releaseRoot -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Host "Release directory: $releaseRoot"
    Write-Host "Release ZIP: $zipPath"
} finally {
    Pop-Location
}
