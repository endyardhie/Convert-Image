import errno
import sys
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


converter = load('converter', ROOT / 'src/convert.py')
manager = load('manager', ROOT / 'scripts/manage_install.py')


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.cfg = converter.DEFAULTS.copy()

    def test_resize_preserves_aspect_alpha_profile_and_no_upscale(self):
        source = self.root / 'foto spasi $uji [1].PNG'
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGBA', (2400, 1200), (20, 140, 220, 80)).save(source, icc_profile=icc)
        result = converter.prepare(source, 'standard', self.cfg)
        self.assertEqual(result.size, (1920, 960))
        self.assertEqual(result.mode, 'RGBA')
        self.assertEqual(result.info['icc_profile'], icc)
        self.assertEqual(converter.prepare(source, 'small', self.cfg).size, (1280, 640))
        small = self.root / 'tiny.webp'
        Image.new('RGB', (37, 19), 'red').save(small, lossless=True)
        self.assertEqual(converter.prepare(small, 'standard', self.cfg).size, (37, 19))

    def test_lossless_preparation_and_orientation(self):
        source = self.root / 'alpha.png'
        image = Image.new('RGBA', (32, 20), (30, 80, 130, 60))
        image.save(source)
        self.assertEqual(converter.prepare(source, 'high', self.cfg).tobytes(), image.tobytes())
        jpeg = self.root / 'rotation.jpeg'
        exif = Image.Exif()
        exif[274] = 6
        Image.new('RGB', (40, 20), 'blue').save(jpeg, exif=exif)
        self.assertEqual(converter.prepare(jpeg, 'high', self.cfg).size, (20, 40))

    def test_high_rejects_16bit_png_and_cmyk(self):
        png = self.root / '16.png'
        Image.new('I;16', (4, 4), 40000).save(png)
        with self.assertRaisesRegex(ValueError, '16-bit'):
            converter.prepare(png, 'high', self.cfg)
        jpeg = self.root / 'cmyk.jpg'
        Image.new('CMYK', (4, 4), (20, 30, 40, 0)).save(jpeg)
        with self.assertRaisesRegex(ValueError, 'CMYK'):
            converter.prepare(jpeg, 'high', self.cfg)
        self.assertEqual(converter.prepare(jpeg, 'standard', self.cfg).mode, 'RGB')

    def test_animation_rejected(self):
        source = self.root / 'animation.webp'
        Image.new('RGB', (8, 8), 'red').save(source, save_all=True, duration=100,
            append_images=[Image.new('RGB', (8, 8), 'blue')], lossless=True)
        with self.assertRaisesRegex(ValueError, 'Animasi'):
            converter.prepare(source, 'standard', self.cfg)

    def test_publish_never_overwrites_and_supports_no_hardlinks(self):
        encoded = self.root / 'encoded'
        encoded.write_bytes(b'encoded output')
        source = self.root / 'original.jpg'
        source.write_bytes(b'original')
        first = converter.publish(encoded, source, 'high')
        second = converter.publish(encoded, source, 'high')
        with patch.object(converter.os, 'link', side_effect=OSError(errno.EOPNOTSUPP, 'No hardlinks')):
            third = converter.publish(encoded, source, 'high')
        self.assertEqual(len({first, second, third}), 3)
        self.assertEqual(source.read_bytes(), b'original')
        for path in (first, second, third):
            self.assertEqual(path.read_bytes(), b'encoded output')

    def test_failed_lossless_verification_does_not_publish(self):
        source = self.root / 'verification.png'
        Image.new('RGB', (8, 8), 'blue').save(source)

        def bad_codec(command, progress, log):
            destination = Path(command[-1])
            if command[0] == 'avifenc':
                destination.write_bytes(b'encoded')
            else:
                Image.new('RGB', (8, 8), 'red').save(destination)

        with patch.object(converter, 'run', side_effect=bad_codec), (self.root / 'test.log').open('w') as log:
            with self.assertRaisesRegex(RuntimeError, 'lossless'):
                converter.convert(source, 'high', self.cfg, True, converter.Progress('high', 1, True), log)
        self.assertFalse(list(self.root.glob('verification-high*.avif')))
        self.assertFalse(list(self.root.glob('.img2avif-*')))

    @unittest.skipUnless(shutil.which('avifenc') and shutil.which('avifdec'), 'Real libavif CLI is not installed')
    def test_real_codec_lossless_and_resized_transparency(self):
        self.cfg.update(speed=8, threads=1, small_edge=32)
        probe = __import__('subprocess').run(['avifenc', '--help'], capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
        modern = '--qcolor' in probe.stdout + probe.stderr
        source = self.root / 'actual.png'
        image = Image.new('RGBA', (64, 40))
        image.putdata([((i * 7) % 256, (i * 19) % 256, (i * 31) % 256, (i * 43) % 256) for i in range(64 * 40)])
        image.save(source)
        # Opaque RGB values are preserved even where alpha is zero.
        with (self.root / 'codec.log').open('w') as log:
            high, size = converter.convert(source, 'high', self.cfg, modern, converter.Progress('high', 1, True), log)
            small, size = converter.convert(source, 'small', self.cfg, modern, converter.Progress('small', 1, True), log)
        self.assertTrue(high.is_file())
        self.assertTrue(small.is_file())
        self.assertEqual(size, (32, 20))


@unittest.skipIf(sys.platform == 'win32', 'Linux installer only')
class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.assets = {name: (ROOT / 'src' / name).read_text()
                       for name in ('convert.py', 'nemo_img2avif.py', 'config.json')}
        self.env = patch.dict(os.environ, XDG_DATA_HOME=str(self.root / 'data'), XDG_CONFIG_HOME=str(self.root / 'config'))
        self.env.start()
        self.addCleanup(self.env.stop)
        self.home = patch.object(Path, 'home', return_value=self.root)
        self.home.start()
        self.addCleanup(self.home.stop)

    def test_update_preserves_config_and_uninstall_preserves_user_data(self):
        manager.manage(self.assets, 'install')
        config = self.root / 'config/img2avif/config.json'
        config.write_text('{"speed": 4}')
        manager.manage(self.assets, 'install')
        self.assertEqual(json.loads(config.read_text()), {'speed': 4})
        self.assertEqual(len(list((self.root / 'data/img2avif-backups').glob('*/convert.py'))), 1)
        self.assertTrue(os.access(self.root / '.local/bin/img2avif', os.X_OK))
        self.assertTrue(os.access(self.root / '.local/bin/convert-image', os.X_OK))
        manager.manage(self.assets, 'uninstall')
        self.assertTrue(config.exists())
        self.assertFalse((self.root / 'data/img2avif/convert.py').exists())
        self.assertFalse((self.root / 'data/nemo-python/extensions/nemo_img2avif.py').exists())
        self.assertFalse((self.root / '.local/bin/img2avif').exists())
        self.assertFalse((self.root / '.local/bin/convert-image').exists())

    def test_write_failure_rolls_back_prior_file(self):
        manager.manage(self.assets, 'install')
        original = self.root / 'data/img2avif/convert.py'
        original.write_text('# old converter\n')
        write = manager.atomic_write
        calls = []

        def fail_second(path, text, mode=0o644):
            calls.append(path)
            if len(calls) == 2:
                raise OSError('simulated write error')
            write(path, text, mode)

        with patch.object(manager, 'atomic_write', side_effect=fail_second):
            with self.assertRaisesRegex(OSError, 'simulated'):
                manager.manage(self.assets, 'install')
        self.assertEqual(original.read_text(), '# old converter\n')

    def test_symlink_target_rejected_without_touching_target(self):
        extension = self.root / 'data/nemo-python/extensions/nemo_img2avif.py'
        extension.parent.mkdir(parents=True)
        target = self.root / 'unrelated.py'
        target.write_text('preserve me')
        extension.symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            manager.manage(self.assets, 'install')
        self.assertEqual(target.read_text(), 'preserve me')



class JpegTests(unittest.TestCase):
    setUp = ImageTests.setUp
    # Reuse the isolated scratch directory, but only add JPEG-specific cases.
    def test_jpg_presets_same_format_and_collision(self):
        source = self.root / 'foto spasi ü.jpg'
        Image.new('RGB', (2200, 1100), 'steelblue').save(source, quality=98)
        original = source.read_bytes()
        with (self.root / 'jpg.log').open('w') as log:
            for mode, size in [('high', (2200, 1100)), ('standard', (1920, 960)), ('small', (1280, 640))]:
                first, actual = converter.convert(source, mode, self.cfg, False, converter.Progress(mode, 1, True), log, 'jpg')
                second, _ = converter.convert(source, mode, self.cfg, False, converter.Progress(mode, 1, True), log, 'jpg')
                self.assertNotEqual(first, second)
                self.assertEqual(actual, size)
                with Image.open(first) as result:
                    result.load()
                    self.assertEqual((result.format, result.size), ('JPEG', size))
                    self.assertTrue(result.info.get('progressive'))
        self.assertEqual(source.read_bytes(), original)

    def test_jpg_alpha_white_and_icc(self):
        source = self.root / 'transparent.png'
        icc = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        Image.new('RGBA', (32, 20), (200, 0, 0, 0)).save(source, icc_profile=icc)
        with (self.root / 'alpha.log').open('w') as log:
            target, _ = converter.convert(source, 'high', self.cfg, False, converter.Progress('high', 1, True), log, 'jpg')
        with Image.open(target) as result:
            self.assertEqual(result.mode, 'RGB')
            self.assertEqual(result.getpixel((10, 10)), (255, 255, 255))
            self.assertEqual(result.info['icc_profile'], icc)

    def test_jpg_cli_without_avif_tools(self):
        import subprocess
        source = self.root / 'input.jpeg'
        Image.new('RGB', (20, 10), 'blue').save(source)
        env = dict(os.environ, PATH='', XDG_CONFIG_HOME=str(self.root / 'config'), XDG_CACHE_HOME=str(self.root / 'cache'))
        result = subprocess.run([sys.executable, str(ROOT / 'src/convert.py'), '--format', 'jpg', 'standard', '--no-gui', '--', str(source)], env=env, capture_output=True, text=True, encoding='utf-8', errors='replace')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.root / 'input-standard.jpg').exists())

    def test_jpg_save_failure_or_cancellation_never_publishes(self):
        source = self.root / 'failure.png'
        Image.new('RGB', (20, 10), 'red').save(source)
        with (self.root / 'fail.log').open('w') as log:
            with patch.object(Image.Image, 'save', side_effect=OSError('disk full')):
                with self.assertRaises(OSError):
                    converter.convert(source, 'high', self.cfg, False, converter.Progress('high', 1, True), log, 'jpg')
            progress = converter.Progress('high', 1, True)
            with patch.object(progress, 'check', side_effect=[None, converter.Cancelled()]):
                with self.assertRaises(converter.Cancelled):
                    converter.convert(source, 'high', self.cfg, False, progress, log, 'jpg')
        self.assertFalse(list(self.root.glob('failure-*.jpg')))
        self.assertFalse(list(self.root.glob('.img2avif-*')))


class MenuTests(unittest.TestCase):
    def test_five_formats_three_presets_and_callback_arguments(self):
        import types
        class Menu:
            def __init__(self): self.items = []
            def append_item(self, item): self.items.append(item)
        class Item:
            def __init__(self, **kwargs): self.__dict__.update(kwargs)
            def set_submenu(self, menu): self.submenu = menu
            def connect(self, signal, callback, *args): self.activation = args
        class File:
            def is_directory(self): return False
            def get_uri(self): return 'file:///tmp/test.avif'
        gi = types.ModuleType('gi'); gi.require_version = lambda *args: None
        repository = types.ModuleType('gi.repository')
        repository.Nemo = types.SimpleNamespace(Menu=Menu, MenuItem=Item, MenuProvider=type('Provider', (), {}))
        repository.GObject = types.SimpleNamespace(GObject=type('GObject', (), {}))
        repository.Gio = types.SimpleNamespace(File=types.SimpleNamespace(new_for_uri=lambda uri: types.SimpleNamespace(get_path=lambda: '/tmp/test.avif')))
        with patch.dict('sys.modules', {'gi': gi, 'gi.repository': repository}):
            module = load('test_nemo_menu', ROOT / 'src/nemo_img2avif.py')
        root = module.Img2AvifMenu().get_file_items(None, [File()])[0]
        self.assertEqual(root.label, 'Convert Image')
        self.assertEqual([x.label for x in root.submenu.items], ['Avif', 'Jpg', 'Pdf', 'Png', 'Webp'])
        for item, output_format in zip(root.submenu.items, ['avif', 'jpg', 'pdf', 'png', 'webp']):
            self.assertEqual([x.label for x in item.submenu.items], ['High Quality', 'Standard', 'Small Size'])
            for child, mode in zip(item.submenu.items, ['high', 'standard', 'small']):
                self.assertEqual(child.activation, (output_format, mode, ('/tmp/test.avif',)))

if __name__ == '__main__':
    unittest.main()
