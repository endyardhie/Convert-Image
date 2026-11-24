import sys
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pdf_converter', ROOT / 'src/convert.py')
converter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(converter)


class PdfTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cfg = converter.DEFAULTS.copy()

    def convert(self, source, mode='high'):
        with (self.root / 'test.log').open('a') as log:
            return converter.convert(source, mode, self.cfg, False, converter.Progress(mode, 1, True), log, 'pdf')

    def test_presets_page_geometry_image_resolution_and_collisions(self):
        source = self.root / 'foto spasi ü.png'
        Image.new('RGB', (2400, 1200), 'blue').save(source)
        original = source.read_bytes()
        for mode, expected in [('high', (2400, 1200)), ('standard', (1920, 960)), ('small', (1280, 640))]:
            target, size = self.convert(source, mode)
            second, _ = self.convert(source, mode)
            self.assertEqual(target.suffix, '.pdf')
            self.assertNotEqual(target, second)
            self.assertEqual(size, expected)
            reader = PdfReader(target, strict=True)
            self.assertEqual(len(reader.pages), 1)
            page = reader.pages[0]
            self.assertAlmostEqual(float(page.mediabox.width), expected[0] * .75)
            self.assertAlmostEqual(float(page.mediabox.height), expected[1] * .75)
            self.assertEqual(page.images[0].image.size, expected)
        self.assertEqual(source.read_bytes(), original)

    def test_alpha_flattening_orientation_and_no_upscale(self):
        source = self.root / 'alpha.png'
        Image.new('RGBA', (30, 18), (200, 0, 0, 0)).save(source)
        target, size = self.convert(source, 'small')
        self.assertEqual(size, (30, 18))
        result = PdfReader(target).pages[0].images[0].image
        self.assertEqual(result.convert('RGB').getpixel((10, 10)), (255, 255, 255))
        jpeg = self.root / 'rotate.jpg'
        exif = Image.Exif(); exif[274] = 6
        Image.new('RGB', (40, 20), 'red').save(jpeg, exif=exif)
        target, size = self.convert(jpeg)
        self.assertEqual(size, (20, 40))
        self.assertEqual(PdfReader(target).pages[0].images[0].image.size, (20, 40))

    def test_cli_batch_without_avif_tools(self):
        sources = [self.root / 'one.jpg', self.root / 'two.webp']
        for p in sources: Image.new('RGB', (40, 24), 'green').save(p)
        env = dict(os.environ, PATH='', XDG_CACHE_HOME=str(self.root/'cache'), XDG_CONFIG_HOME=str(self.root/'config'))
        result = subprocess.run([sys.executable, str(ROOT/'src/convert.py'), '--format', 'pdf', 'standard', '--no-gui', '--', *map(str, sources)], capture_output=True, text=True, encoding='utf-8', errors='replace', env=env)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        for source in sources:
            self.assertEqual(len(PdfReader(source.with_name(source.stem+'-standard.pdf')).pages), 1)

    def test_failed_validation_and_cancel_do_not_publish(self):
        source = self.root/'bad.png'
        Image.new('RGB', (20, 10), 'red').save(source)
        with patch('pypdf.PdfReader', side_effect=ValueError('invalid PDF')):
            with self.assertRaisesRegex(ValueError, 'invalid PDF'):
                self.convert(source)
        with patch.object(converter, 'encode_pdf', side_effect=converter.Cancelled):
            with self.assertRaises(converter.Cancelled): self.convert(source)
        self.assertFalse(list(self.root.glob('bad-*.pdf')))
        self.assertFalse(list(self.root.glob('.img2avif-*')))

    def test_old_config_defaults_and_invalid_pdf_quality(self):
        cfg = self.root/'img2avif/config.json'; cfg.parent.mkdir()
        cfg.write_text('{"speed": 4}')
        with patch.object(converter, 'user_directory', return_value=self.root/'img2avif'):
            self.assertEqual(converter.settings()['pdf_high_quality'], 95)
            cfg.write_text('{"pdf_small_quality": 100}')
            with self.assertRaisesRegex(ValueError, 'pdf_small_quality'): converter.settings()


if __name__ == '__main__': unittest.main()
