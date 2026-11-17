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
        root = Nemo.MenuItem(name="Img2Avif::Root", label="Convert Img2Avif", tip="Konversi gambar ke AVIF", icon="image-x-generic")
        menu = Nemo.Menu()
        for mode, label, tip in (
            ("high", "High Quality", "Lossless 8-bit, resolusi asli; hasil diverifikasi"),
            ("standard", "Standard", "Maks. sisi terpanjang 1920 px, kualitas 60"),
            ("small", "Small Size", "Maks. sisi terpanjang 1280 px, kualitas 40"),
        ):
            child = Nemo.MenuItem(name="Img2Avif::" + mode, label=label, tip=tip)
            child.connect("activate", self.activate, mode, tuple(paths))
            menu.append_item(child)
        root.set_submenu(menu)
        return [root]

    def activate(self, _item, mode, paths):
        data = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
        script = data / "img2avif/convert.py"
        # Request file avoids ARG_MAX even for thousands of selected filenames.
        request = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".json", prefix="img2avif-request-", delete=False) as stream:
                request = stream.name
                json.dump({"mode": mode, "files": paths}, stream)
            subprocess.Popen(["/usr/bin/python3", str(script), "--request", request],
                             start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            if request:
                Path(request).unlink(missing_ok=True)
            subprocess.Popen(["zenity", "--error", "--no-markup", "--text=Img2Avif gagal dimulai. Jalankan ulang installer."])
