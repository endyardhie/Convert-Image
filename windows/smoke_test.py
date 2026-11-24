"""Exercise the packaged executable, native menu, install/update/uninstall on Windows."""
import ctypes
import json
import os
from pathlib import Path
import subprocess
import tempfile
import winreg
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
CLSID = '{2B414F21-4B8D-4DB6-9E69-7EE68D08C822}'


def execute(command, **kwargs):
    result = subprocess.run([str(x) for x in command], timeout=180, **kwargs)
    assert result.returncode == 0, (command, result.returncode)


def check_app(app, folder):
    # Multi-image UTF-8 requests use the same protocol as the Explorer extension.
    sources = []
    for name in ('foto ü & [1].png', 'gambar 日本語.png'):
        source = folder / name
        Image.new('RGBA', (48, 30), (20, 120, 160, 100)).save(source)
        sources.append(source)
    originals = [p.read_bytes() for p in sources]
    for fmt in ('avif', 'jpg', 'pdf', 'png', 'webp'):
        for mode in ('high', 'standard', 'small'):
            request = folder / 'request.json'
            request.write_text(json.dumps({'format': fmt, 'mode': mode, 'files': [str(p) for p in sources], 'no_gui': True}, ensure_ascii=False), encoding='utf-8')
            execute([app, '--request', request])
            assert not request.exists(), 'Request file must be cleaned up'
            for source in sources:
                target = source.with_name(source.stem + '-' + mode + '.' + fmt)
                assert target.stat().st_size > 0, target
                if fmt == 'pdf':
                    from pypdf import PdfReader
                    assert len(PdfReader(target).pages) == 1
                elif fmt != 'avif':
                    with Image.open(target) as result:
                        result.load()
                        assert result.size == (48, 30)
    for source, original in zip(sources, originals):
        assert source.read_bytes() == original
    execute([ROOT / 'build/shell-test.exe', *sources])
    # Real COM activation uses the registered in-process shell DLL.
    ole32 = ctypes.OleDLL('ole32')
    ole32.CoInitialize(None)
    class GUID(ctypes.Structure):
        _fields_ = [('a', ctypes.c_ulong), ('b', ctypes.c_ushort), ('c', ctypes.c_ushort), ('d', ctypes.c_ubyte * 8)]
    clsid, iid = GUID(), GUID()
    ole32.CLSIDFromString(CLSID, ctypes.byref(clsid))
    ole32.CLSIDFromString('{000214E4-0000-0000-C000-000000000046}', ctypes.byref(iid))
    instance = ctypes.c_void_p()
    ole32.CoCreateInstance(ctypes.byref(clsid), None, 1, ctypes.byref(iid), ctypes.byref(instance))
    assert instance.value
    table = ctypes.cast(instance, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
    ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(table[2])(instance)
    ole32.CoFreeUnusedLibrariesEx(0, 0)
    ole32.CoUninitialize()


def registry_value(key):
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
        return winreg.QueryValueEx(handle, '')[0]


with tempfile.TemporaryDirectory(prefix='convert-image-windows-') as temp:
    folder = Path(temp) / 'Gambar 日本語 ü'
    folder.mkdir()
    installer = next((ROOT / 'dist').glob('*-Setup.exe'))
    # Install in a path with spaces and Unicode, as a regular per-user app.
    install = folder / 'Aplikasi ü' / 'Convert Image'
    execute([installer, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/DIR=' + str(install), '/LOG=' + str(folder / 'install.log')])
    app = install / 'ConvertImage.exe'
    assert app.is_file()
    if os.environ.get('CONVERT_IMAGE_REQUIRE_SIGNED') == '1':
        execute(['powershell.exe', '-NoProfile', '-File', ROOT / 'windows/verify-signatures.ps1', '-Directory', install])
    for ext in ('jpg', 'jpeg', 'png', 'webp', 'avif'):
        assert registry_value(r'Software\Classes\SystemFileAssociations\.' + ext + r'\shellex\ContextMenuHandlers\ConvertImage') == CLSID
    assert registry_value('Software\\Classes\\CLSID\\' + CLSID + r'\InprocServer32') == str(install / 'ConvertImageShell.dll')
    check_app(app, folder)
    outputs = [p for p in folder.iterdir() if '-high.' in p.name or '-standard.' in p.name or '-small.' in p.name]
    assert len(outputs) == 30
    config = Path(os.environ['LOCALAPPDATA']) / 'Convert Image/config/config.json'
    config.write_text('{"speed":8,"threads":1}', encoding='utf-8')
    execute([installer, '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/DIR=' + str(install)])
    assert json.loads(config.read_text()) == {'speed': 8, 'threads': 1}
    execute([install / 'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'])
    assert config.is_file()
    assert not app.exists()
    assert all(p.exists() for p in outputs)
    for ext in ('jpg', 'jpeg', 'png', 'webp', 'avif'):
        try:
            registry_value(r'Software\Classes\SystemFileAssociations\.' + ext + r'\shellex\ContextMenuHandlers\ConvertImage')
        except FileNotFoundError:
            pass
        else:
            raise AssertionError('Menu registration remains after uninstall: ' + ext)
print('Windows package: 30 conversions, Unicode batch requests, native 15-action menu, COM activation, install, update and uninstall passed.')
