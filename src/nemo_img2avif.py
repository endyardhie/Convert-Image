"""Nemo context submenu. Encoding runs outside the file-manager process."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import gi
gi.require_version("Nemo", "3.0")
from gi.repository import Nemo, GObject, Gio


class Img2AvifMenu(GObject.GObject, Nemo.MenuProvider):
    def get_file_items(self, window, files):
        if not files:
            return []
        paths = []
        for item in files:
            path = Gio.File.new_for_uri(item.get_uri()).get_path()
            if item.is_directory() or not path or Path(path).suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp"):
                return []
            paths.append(path)
        root = Nemo.MenuItem(name="ConvertImage::Root", label="Convert Image", tip="Konversi gambar ke AVIF atau JPG", icon="image-x-generic")
        menu = Nemo.Menu()
        for output_format, format_label in (("avif", "Avif"), ("jpg", "Jpg")):
            format_item = Nemo.MenuItem(name="ConvertImage::" + output_format, label=format_label, tip="Konversi ke " + format_label)
            presets = Nemo.Menu()
            tips = {
                "avif": ("Lossless 8-bit, resolusi asli; hasil diverifikasi",
                         "Maks. 1920 px, kualitas AVIF 60", "Maks. 1280 px, kualitas AVIF 40"),
                "jpg": ("Resolusi asli, kualitas JPG 95 (lossy)",
                        "Maks. 1920 px, kualitas JPG 85", "Maks. 1280 px, kualitas JPG 70"),
            }
            for (mode, label), tip in zip((("high", "High Quality"), ("standard", "Standard"), ("small", "Small Size")), tips[output_format]):
                child = Nemo.MenuItem(name="ConvertImage::" + output_format + "::" + mode, label=label, tip=tip)
                child.connect("activate", self.activate, output_format, mode, tuple(paths))
                presets.append_item(child)
            format_item.set_submenu(presets)
            menu.append_item(format_item)
        root.set_submenu(menu)
        return [root]

    def activate(self, _item, output_format, mode, paths):
        data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        script = data / "img2avif/convert.py"
        # Request file avoids ARG_MAX even for thousands of selected filenames.
        request = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="img2avif-request-", delete=False) as stream:
                request = stream.name
                json.dump({"format": output_format, "mode": mode, "files": paths}, stream)
            subprocess.Popen(["/usr/bin/python3", str(script), "--request", request],
                             start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            if request:
                Path(request).unlink(missing_ok=True)
            subprocess.Popen(["zenity", "--error", "--no-markup", "--text=Convert Image gagal dimulai. Jalankan ulang installer."])
