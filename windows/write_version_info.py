"""Generate matching version resources for the Windows app and Explorer DLL."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def generate(destination):
    info = json.loads((ROOT / 'windows/version.json').read_text())
    assert re.fullmatch(r'\d+\.\d+\.\d+', info['version'])
    assert re.fullmatch(r'\d+\.\d+\.\d+\.\d+', info['file_version'])
    version = tuple(map(int, info['file_version'].split('.')))
    assert version[:3] == tuple(map(int, info['version'].split('.')))
    assert all(0 <= x <= 65535 for x in version)
    fields = {
        'CompanyName': info['company_name'], 'FileDescription': 'Convert Image',
        'FileVersion': info['file_version'], 'InternalName': 'ConvertImage',
        'LegalCopyright': info['copyright'], 'OriginalFilename': 'ConvertImage.exe',
        'ProductName': info['product_name'], 'ProductVersion': info['version'],
    }
    strings = ',\n'.join('StringStruct(' + repr(k) + ', ' + repr(v) + ')' for k, v in fields.items())
    resource = f'''VSVersionInfo(
  ffi=FixedFileInfo(filevers={version!r}, prodvers={version!r}, mask=0x3f,
                   flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
  kids=[StringFileInfo([StringTable('040904B0', [{strings}])]),
        VarFileInfo([VarStruct('Translation', [1033, 1200])])])
'''
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'app-version.txt').write_text(resource, encoding='utf-8')
    fields.update(FileDescription='Convert Image Explorer extension', InternalName='ConvertImageShell', OriginalFilename='ConvertImageShell.dll')
    rc = '#include <windows.h>\n#pragma code_page(65001)\n1 VERSIONINFO\n'
    rc += 'FILEVERSION ' + ','.join(map(str, version)) + '\n'
    rc += 'PRODUCTVERSION ' + ','.join(map(str, version)) + '\n'
    rc += 'FILEFLAGSMASK 0x3fL\nFILEFLAGS 0\nFILEOS VOS_NT_WINDOWS32\nFILETYPE VFT_DLL\nFILESUBTYPE 0\nBEGIN\n'
    rc += 'BLOCK "StringFileInfo" BEGIN\nBLOCK "040904B0" BEGIN\n'
    for key, value in fields.items():
        rc += 'VALUE ' + json.dumps(key) + ', ' + json.dumps(value + '\0') .replace('\\u0000', '\\0') + '\n'
    rc += 'END\nEND\nBLOCK "VarFileInfo" BEGIN\nVALUE "Translation", 0x409, 1200\nEND\nEND\n'
    (destination / 'shell-version.rc').write_text(rc, encoding='utf-8')
    return info


if __name__ == '__main__':
    generate(ROOT / 'build/version')
