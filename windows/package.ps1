param([switch]$RequireSignedPayload)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$version = Get-Content windows/version.json -Raw | ConvertFrom-Json
foreach ($name in @('ConvertImage.exe', 'ConvertImageShell.dll')) {
    $file = Join-Path 'dist/ConvertImage' $name
    $metadata = (Get-Item $file).VersionInfo
    if ($metadata.ProductName -ne $version.product_name -or
        $metadata.ProductVersion -ne $version.version -or
        $metadata.FileVersion -ne $version.file_version -or
        $metadata.CompanyName -ne $version.company_name -or
        $metadata.OriginalFilename -ne $name) {
        throw "Metadata produk/versi tidak sesuai: $name"
    }
    if ($RequireSignedPayload) {
        $signature = Get-AuthenticodeSignature $file
        if ($signature.Status -ne 'Valid' -or -not $signature.TimeStamperCertificate -or
            $signature.SignerCertificate.Subject -notmatch 'CN=SignPath Foundation(?:,|$)') {
            throw "Tanda tangan SignPath Foundation tidak valid: $name"
        }
    }
}
$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $iscc)) { throw 'Inno Setup 6 tidak ditemukan' }
& $iscc "/DAppVersion=$($version.version)" "/DAppFileVersion=$($version.file_version)" windows/installer.iss
if ($LASTEXITCODE -ne 0) { throw 'Build installer gagal' }
$installer = Get-Item "dist/Convert-Image-$($version.version)-Windows-x64-Setup.exe"
if ($installer.VersionInfo.ProductName -ne $version.product_name -or
    $installer.VersionInfo.ProductVersion -ne $version.version -or
    $installer.VersionInfo.FileVersion -ne $version.file_version) {
    throw 'Metadata installer tidak sesuai'
}
if ($RequireSignedPayload) { $env:CONVERT_IMAGE_REQUIRE_SIGNED = '1' }
try {
    python windows/smoke_test.py
    if ($LASTEXITCODE -ne 0) { throw 'Pengujian installer gagal' }
} finally {
    Remove-Item Env:CONVERT_IMAGE_REQUIRE_SIGNED -ErrorAction SilentlyContinue
}
