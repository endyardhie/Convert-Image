import importlib.util
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageCms
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('formats_converter', ROOT/'src/convert.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


@unittest.skipUnless(shutil.which('avifenc') and shutil.which('avifdec'), 'Real libavif CLI is not installed')
class FormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.cfg = c.DEFAULTS.copy()
        self.cfg.update(speed=8, threads=1, standard_edge=48, small_edge=32)
        probe = subprocess.run(['avifenc','--help'],capture_output=True,text=True,check=True)
        self.modern = '--qcolor' in probe.stdout+probe.stderr

    def convert(self, source, output, mode='high'):
        with (self.root/'test.log').open('a') as log:
            return c.convert(source,mode,self.cfg,self.modern,c.Progress(mode,1,True),log,output)

    def test_all_five_inputs_to_all_five_outputs_all_presets(self):
        base = self.root/'source.png'
        im = Image.new('RGB',(64,40),'steelblue'); im.save(base)
        sources=[base]
        for suffix in ('jpg','jpeg','webp'):
            p=self.root/('source.'+suffix);im.save(p);sources.append(p)
        avif,_=self.convert(base,'avif');sources.append(avif)
        originals={p:p.read_bytes() for p in sources}
        for source in sources:
            for output in ('avif','jpg','pdf','png','webp'):
                for mode,expected in [('high',(64,40)),('standard',(48,30)),('small',(32,20))]:
                    with self.subTest(source=source.suffix,output=output,mode=mode):
                        target,size=self.convert(source,output,mode)
                        self.assertEqual(size,expected)
                        self.assertEqual(target.suffix,'.'+output)
                        self.assertNotIn(target,sources)
                        if output=='pdf':
                            reader=PdfReader(target);self.assertEqual(len(reader.pages),1)
                            self.assertEqual(reader.pages[0].images[0].image.size,expected)
                        elif output=='avif':
                            decoded=self.root/'checked.png'
                            subprocess.run(['avifdec',str(target),str(decoded)],check=True,capture_output=True)
                            with Image.open(decoded) as result:self.assertEqual(result.size,expected)
                        else:
                            with Image.open(target) as result:
                                result.load();self.assertEqual(result.size,expected)
                                self.assertEqual(result.format,{'jpg':'JPEG','png':'PNG','webp':'WEBP'}[output])
        for p,data in originals.items():self.assertEqual(p.read_bytes(),data)

    def test_png_and_lossless_webp_exact_alpha_icc_and_same_format(self):
        icc=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
        base=self.root/'transparent.png'
        im=Image.new('RGBA',(24,16));im.putdata([((i*7)%256,(i*9)%256,(i*11)%256,(i*13)%256) for i in range(24*16)])
        im.save(base,icc_profile=icc)
        for output in ('png','webp'):
            first,_=self.convert(base,output)
            second,_=self.convert(first,output)
            for target in (first,second):
                with Image.open(target) as result:
                    self.assertEqual(result.convert('RGBA').tobytes(),im.tobytes())
                    self.assertEqual(result.info['icc_profile'],icc)

    def test_avif_animation_rejected_without_publishing(self):
        a=self.root/'a.png';b=self.root/'b.png'
        Image.new('RGB',(24,16),'red').save(a);Image.new('RGB',(24,16),'blue').save(b)
        animated=self.root/'animation.avif'
        subprocess.run(['avifenc','--speed','8',str(a),str(b),str(animated)],check=True,capture_output=True)
        for output in ('avif','jpg','pdf','png','webp'):
            with self.assertRaisesRegex(ValueError,'Animasi AVIF'):self.convert(animated,output)
        self.assertFalse(list(self.root.glob('animation-high.*')))
        self.assertFalse(list(self.root.glob('.img2avif-*')))

    def test_avif_missing_decoder_reports_error(self):
        source=self.root/'input.avif';source.write_bytes(b'invalid')
        env=dict(os.environ,PATH='',XDG_CACHE_HOME=str(self.root/'cache'),XDG_CONFIG_HOME=str(self.root/'config'))
        result=subprocess.run(['/usr/bin/python3',str(ROOT/'src/convert.py'),'--format','png','high','--no-gui','--',str(source)],env=env,capture_output=True,text=True)
        self.assertEqual(result.returncode,1);self.assertIn('avifdec',result.stdout)

    def test_failed_png_webp_encode_and_cancellation_do_not_publish(self):
        source=self.root/'fail.png';Image.new('RGB',(24,16),'red').save(source)
        for output in ('png','webp'):
            with patch.object(Image.Image,'save',side_effect=OSError('disk full')):
                with self.assertRaises(OSError):self.convert(source,output)
            with patch.object(c.Progress,'check',side_effect=c.Cancelled):
                with self.assertRaises(c.Cancelled):self.convert(source,output)
            self.assertFalse(list(self.root.glob('fail-high.'+output)))
        self.assertFalse(list(self.root.glob('.img2avif-*')))


if __name__=='__main__':unittest.main()
