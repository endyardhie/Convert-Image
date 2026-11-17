#!/usr/bin/env python3
"""Build the downloadable installer from the versioned source files."""
import argparse
from pathlib import Path
import pprint

ROOT = Path(__file__).resolve().parents[1]


def render():
    assets = {name: (ROOT / 'src' / name).read_text()
              for name in ('convert.py', 'nemo_img2avif.py', 'config.json')}
    template = (ROOT / 'scripts/install.template.sh').read_text()
    manager = (ROOT / 'scripts/manage_install.py').read_text()
    return template.replace('__MANAGER__', manager).replace('__ASSETS__', 'ASSETS = ' + pprint.pformat(assets, width=100))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    destination = ROOT / 'install-img2avif.sh'
    output = render()
    if args.check:
        if not destination.exists() or destination.read_text() != output:
            raise SystemExit('Installer belum sinkron. Jalankan python3 scripts/build_installer.py')
        print('Installer sesuai dengan source.')
    else:
        destination.write_text(output)
        destination.chmod(0o755)
        print(destination)
