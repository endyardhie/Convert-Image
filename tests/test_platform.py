import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('platform_converter', ROOT / 'src/convert.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class PlatformTests(unittest.TestCase):
    @unittest.skipUnless(sys.platform == 'win32', 'Windows GUI only')
    def test_windows_progress_cancels_active_process(self):
        with tempfile.TemporaryDirectory() as temp:
            progress = c.Progress('standard', 1, False, 'avif')
            try:
                progress.window.after(100, progress.cancel)
                with (Path(temp)/'process.log').open('w') as log:
                    with self.assertRaises(c.Cancelled):
                        c.run([sys.executable, '-c', 'import time; time.sleep(30)'], progress, log)
            finally:
                progress.close()

    def test_windows_directories_and_bundled_codec_precedence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            codec = root / 'tools/avifenc.exe'
            codec.parent.mkdir()
            codec.touch()
            with patch.object(c, 'windows', return_value=True), patch.dict(os.environ, LOCALAPPDATA=temp), patch.object(c.sys, '_MEIPASS', temp, create=True):
                self.assertEqual(c.user_directory('config'), root / 'Convert Image/config')
                self.assertEqual(c.user_directory('cache'), root / 'Convert Image/cache')
                self.assertEqual(c.find_tool('avifenc'), str(codec))

    def test_utf8_request_batch_cleanup_and_collision(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            files = [root / 'foto ü & [1].png', root / 'gambar 日本語.png']
            for f in files:
                Image.new('RGBA', (20, 10), (10, 20, 30, 80)).save(f)
            for index in range(2):
                request = root / 'request.json'
                request.write_text(json.dumps({'format':'png', 'mode':'standard', 'no_gui':True, 'files':list(map(str,files))}, ensure_ascii=False), encoding='utf-8')
                env = dict(os.environ, XDG_CONFIG_HOME=str(root/'config'), XDG_CACHE_HOME=str(root/'cache'), LOCALAPPDATA=str(root/'local'))
                result = subprocess.run([sys.executable, str(ROOT / 'src/convert.py'), '--request', str(request)], capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(request.exists())
                for f in files:
                    suffix = '' if index == 0 else '-1'
                    self.assertTrue(f.with_name(f.stem + '-standard' + suffix + '.png').exists())
