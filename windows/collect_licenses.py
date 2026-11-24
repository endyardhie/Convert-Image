"""Copy redistribution notices from installed build dependencies into the app."""
from pathlib import Path
import importlib.metadata
import shutil
import sys

destination = Path('dist/ConvertImage/licenses')
for name in ('Pillow', 'reportlab', 'pypdf', 'pyinstaller', 'charset-normalizer'):
    distribution = importlib.metadata.distribution(name)
    for file in distribution.files or ():
        if any(token in str(file).lower() for token in ('license', 'copying', 'notice')):
            source = Path(distribution.locate_file(file))
            if source.is_file():
                target = destination / name / str(file).replace('..', '_parent_')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
shutil.copy2(Path(sys.base_prefix) / 'LICENSE.txt', destination / 'Python.txt')
