param([switch]$SkipInstaller)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root
$tools = Join-Path $root 'build/windows-codecs'
New-Item -ItemType Directory -Force $tools | Out-Null
$archive = Join-Path $tools 'windows-artifacts.zip'
Invoke-WebRequest 'https://github.com/AOMediaCodec/libavif/releases/download/v1.4.2/windows-artifacts.zip' -OutFile $archive
$expected = 'cb2d9fea43dcbab1d0707e3b37eb7b08070ad2fb60a2c188c39ec12382c0484a'
if ((Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $expected) {
    throw 'Checksum codec AVIF tidak sesuai. Build dihentikan.'
}
Expand-Archive $archive -DestinationPath $tools -Force
$pythonDir = Split-Path (Get-Command python).Source -Parent
Get-ChildItem $pythonDir -Filter 'vcruntime140*.dll' | Copy-Item -Destination $tools
$env:PATH = "$tools;$env:PATH"
& "$tools/avifenc.exe" --version
if ($LASTEXITCODE -ne 0) { throw 'Encoder AVIF tidak dapat dijalankan' }

python -m pip install -r windows/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Pemasangan dependensi build gagal' }
python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Pengujian gagal' }

python windows/write_version_info.py
if ($LASTEXITCODE -ne 0) { throw 'Pembuatan metadata versi gagal' }
python -c "from PIL import Image; Image.open('assets/branding/logo.png').save('assets/branding/app.ico',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])"
python -m PyInstaller --noconfirm --clean --windowed --onedir --name ConvertImage --paths src --icon assets/branding/app.ico --version-file build/version/app-version.txt --add-data "assets/branding/app.ico;." --add-binary "$tools/avifenc.exe;tools" --add-binary "$tools/avifdec.exe;tools" --add-binary "$tools/*.dll;tools" --hidden-import PIL.ImageCms --collect-all reportlab --collect-all pypdf --copy-metadata Pillow --copy-metadata reportlab --copy-metadata pypdf windows/app.py
if ($LASTEXITCODE -ne 0) { throw 'Build aplikasi gagal' }

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = & $vswhere -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
if (-not $vs) { throw 'Visual C++ Build Tools tidak ditemukan' }
$vcvars = Join-Path $vs 'VC/Auxiliary/Build/vcvars64.bat'
cmd /c "`"$vcvars`" && rc /nologo /fobuild\version\shell-version.res build\version\shell-version.rc && cl /nologo /std:c++17 /EHsc /O2 /MT /utf-8 /LD windows\context_menu.cpp /Fe:dist\ConvertImage\ConvertImageShell.dll /link /DEF:windows\context_menu.def build\version\shell-version.res shell32.lib ole32.lib uuid.lib user32.lib"
if ($LASTEXITCODE -ne 0) { throw 'Build ekstensi File Explorer gagal' }
cmd /c "`"$vcvars`" && cl /nologo /std:c++17 /EHsc /O2 /MT /utf-8 /DCONVERT_IMAGE_TEST windows\context_menu.cpp /Fe:build\shell-test.exe /link shell32.lib ole32.lib uuid.lib user32.lib"
if ($LASTEXITCODE -ne 0) { throw 'Build pengujian ekstensi gagal' }

# Ship notices for bundled Python modules and the statically linked AVIF tools.
$notices = 'dist/ConvertImage/licenses'
New-Item -ItemType Directory -Force $notices | Out-Null
Copy-Item windows/THIRD-PARTY.md $notices
$licenses = @{
    'libavif.txt' = 'https://raw.githubusercontent.com/AOMediaCodec/libavif/v1.4.2/LICENSE'
    'aom.txt' = 'https://aomedia.googlesource.com/aom/+/v3.14.1/LICENSE?format=TEXT'
    'aom-patents.txt' = 'https://aomedia.googlesource.com/aom/+/v3.14.1/PATENTS?format=TEXT'
    'dav1d.txt' = 'https://raw.githubusercontent.com/videolan/dav1d/1.5.3/COPYING'
    'libyuv.txt' = 'https://chromium.googlesource.com/libyuv/libyuv/+/644251f25/LICENSE?format=TEXT'
    'libjpeg-turbo.txt' = 'https://raw.githubusercontent.com/libjpeg-turbo/libjpeg-turbo/3.1.4.1/LICENSE.md'
    'libjpeg-ijg.txt' = 'https://raw.githubusercontent.com/libjpeg-turbo/libjpeg-turbo/3.1.4.1/README.ijg'
    'libsharpyuv.txt' = 'https://chromium.googlesource.com/webm/libwebp/+/v1.6.0/COPYING?format=TEXT'
    'libpng.txt' = 'https://raw.githubusercontent.com/pnggroup/libpng/v1.6.58/LICENSE'
    'zlib.txt' = 'https://raw.githubusercontent.com/madler/zlib/v1.3.2/LICENSE'
}
foreach ($entry in $licenses.GetEnumerator()) {
    $target = Join-Path $notices $entry.Key
    if ($entry.Value.EndsWith('?format=TEXT')) {
        $response = Invoke-WebRequest $entry.Value
        [IO.File]::WriteAllBytes($target, [Convert]::FromBase64String($response.Content))
    } else { Invoke-WebRequest $entry.Value -OutFile $target }
}
python windows/collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw 'Pengumpulan lisensi gagal' }

if (-not $SkipInstaller) {
    & ./windows/package.ps1
}
