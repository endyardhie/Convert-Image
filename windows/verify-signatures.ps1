param(
    [Parameter(Mandatory=$true)][string]$Directory,
    [string]$InstallerPath,
    [string]$ReportPath
)
$ErrorActionPreference = 'Stop'
$files = @((Join-Path $Directory 'ConvertImage.exe'), (Join-Path $Directory 'ConvertImageShell.dll'))
if ($InstallerPath) { $files += $InstallerPath }
$report = foreach ($file in $files) {
    $signature = Get-AuthenticodeSignature $file
    if ($signature.Status -ne 'Valid' -or -not $signature.TimeStamperCertificate -or
        $signature.SignerCertificate.Subject -notmatch 'CN=SignPath Foundation(?:,|$)') {
        throw "Tanda tangan tepercaya SignPath Foundation tidak valid: $file ($($signature.Status))"
    }
    [PSCustomObject]@{
        File = Split-Path $file -Leaf
        Status = $signature.Status.ToString()
        Publisher = $signature.SignerCertificate.Subject
        CertificateThumbprint = $signature.SignerCertificate.Thumbprint
        TimestampAuthority = $signature.TimeStamperCertificate.Subject
        SHA256 = (Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant()
    }
}
$report | Format-Table File, Status, Publisher -AutoSize
if ($ReportPath) { $report | ConvertTo-Json | Set-Content $ReportPath -Encoding utf8 }
