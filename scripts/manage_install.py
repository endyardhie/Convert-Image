"""Per-user install/uninstall with backup, atomic replacement, and rollback."""
import ast
import datetime
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import tempfile


def atomic_write(path, text, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.img2avif-install-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(text)
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def manage(assets, action):
    data = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
    config = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'img2avif/config.json'
    launcher = Path.home() / '.local/bin/img2avif'
    converter = data / 'img2avif/convert.py'
    extension = data / 'nemo-python/extensions/nemo_img2avif.py'
    paths = {'convert.py': converter, 'nemo_img2avif.py': extension, 'img2avif': launcher, 'convert-image': launcher.with_name('convert-image')}
    if action not in ('install', 'uninstall'):
        raise ValueError('Aksi tidak dikenal: ' + action)
    if action == 'install':
        ast.parse(assets['convert.py'])
        ast.parse(assets['nemo_img2avif.py'])
        defaults = json.loads(assets['config.json'])
        assets = dict(assets, img2avif='#!/usr/bin/env bash\nexec /usr/bin/python3 ' + shlex.quote(str(converter)) + ' "$@"\n')
        assets['convert-image'] = assets['img2avif']
    backup = None
    for key, path in paths.items():
        if path.is_symlink():
            raise RuntimeError('Target berupa symlink; tidak diubah: ' + str(path))
        if path.exists():
            if not path.is_file():
                raise RuntimeError('Target bukan file: ' + str(path))
            if backup is None:
                root = data / 'img2avif-backups'
                root.mkdir(parents=True, exist_ok=True)
                backup = Path(tempfile.mkdtemp(prefix=datetime.datetime.now().strftime('%Y%m%d-%H%M%S-'), dir=root))
            shutil.copy2(path, backup / key)
    changed = []
    created_config = False
    try:
        for key, path in paths.items():
            if action == 'install':
                atomic_write(path, assets[key], 0o755 if key in ('img2avif', 'convert-image') else 0o644)
            else:
                path.unlink(missing_ok=True)
            changed.append((key, path))
        if action == 'install':
            config.parent.mkdir(parents=True, exist_ok=True)
            try:
                with config.open('x') as stream:
                    created_config = True
                    json.dump(defaults, stream, indent=2)
                    stream.write('\n')
            except FileExistsError:
                pass
    except BaseException:
        for key, path in reversed(changed):
            saved = backup / key if backup else None
            if saved and saved.exists():
                os.replace(saved, path)
            else:
                path.unlink(missing_ok=True)
        if created_config:
            config.unlink(missing_ok=True)
        raise
    if backup:
        print('Backup:', backup)
    if action == 'install':
        print('Menu terpasang: Convert Image > Avif / Jpg / Pdf > High Quality / Standard / Small Size')
        print('Konfigurasi:', config)
        print('CLI:', launcher.with_name('convert-image'))
        print('Alias kompatibilitas:', launcher)
    else:
        print('Converter, launcher, dan menu dihapus.')
        print('Gambar, konfigurasi, log, dan backup tetap tersimpan.')
