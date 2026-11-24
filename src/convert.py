#!/usr/bin/python3
"""Convert Image: shared, validated image conversion for Linux and Windows."""
import argparse
import errno
import io
import json
import os
import re
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import warnings

# Optional user-local PDF dependencies, used when system packages are unavailable.
_vendor = Path(__file__).resolve().parent / "vendor"
if _vendor.is_dir():
    sys.path.insert(0, str(_vendor))

from PIL import Image, ImageOps, ImageCms

DEFAULTS = {"speed": 0, "threads": 4, "standard_edge": 1920,
            "standard_quality": 60, "small_edge": 1280, "small_quality": 40, "jpg_high_quality": 95,
            "jpg_standard_quality": 85, "jpg_small_quality": 70,
            "pdf_high_quality": 95, "pdf_standard_quality": 85, "pdf_small_quality": 70,
            "webp_standard_quality": 80, "webp_small_quality": 60}
MODES = {"high": "High Quality", "standard": "Standard", "small": "Small Size"}
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
warnings.simplefilter("error", Image.DecompressionBombWarning)


class Cancelled(Exception):
    pass


def windows():
    return sys.platform == "win32"


def user_directory(kind):
    if windows():
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Convert Image"
        return base / kind
    variable = "XDG_CONFIG_HOME" if kind == "config" else "XDG_CACHE_HOME"
    fallback = ".config" if kind == "config" else ".cache"
    return Path(os.environ.get(variable, Path.home() / fallback)) / "img2avif"


def find_tool(name):
    if windows():
        # Use the verified bundled codec before anything found in PATH.
        bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        candidate = bundle / "tools" / (name + ".exe")
        if candidate.is_file():
            return str(candidate)
    return shutil.which(name)


def process_options():
    return {"creationflags": subprocess.CREATE_NO_WINDOW} if windows() else {}


def window_icon(window):
    bundle = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    icon = bundle / "app.ico"
    if icon.is_file():
        window.iconbitmap(str(icon))


def message(text, error=False):
    if windows():
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        window_icon(root)
        try:
            (messagebox.showerror if error else messagebox.showinfo)("Convert Image", text, parent=root)
        finally:
            root.destroy()
        return
    subprocess.run(["zenity", "--error" if error else "--info", "--no-markup",
                    "--title=Convert Image", "--width=560", "--text=" + text],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def settings():
    config = user_directory("config") / "config.json"
    result = DEFAULTS.copy()
    if config.exists():
        result.update(json.loads(config.read_text(encoding="utf-8")))
    limits = {"speed": (0, 10), "threads": (1, 64), "standard_edge": (1, 16384),
              "small_edge": (1, 16384), "standard_quality": (1, 99), "small_quality": (1, 99), "jpg_high_quality": (1, 95),
              "jpg_standard_quality": (1, 95), "jpg_small_quality": (1, 95), "pdf_high_quality": (1, 95),
              "pdf_standard_quality": (1, 95), "pdf_small_quality": (1, 95), "webp_standard_quality": (1, 100),
              "webp_small_quality": (1, 100)}
    for key, (low, high) in limits.items():
        value = result[key]
        if type(value) is not int or not low <= value <= high:
            raise ValueError("Pengaturan tidak valid: " + key)
    if result["small_edge"] > result["standard_edge"]:
        raise ValueError("small_edge harus <= standard_edge")
    result["threads"] = min(result["threads"], os.cpu_count() or 1)
    return result


class Progress:
    def __init__(self, mode, count, headless, output_format="avif"):
        self.proc = None
        self.window = None
        self.cancelled = False
        if not headless and windows():
            import tkinter as tk
            from tkinter import ttk
            self.window = tk.Tk()
            self.window.title("Convert Image — " + output_format.upper())
            self.window.geometry("560x300")
            self.window.resizable(False, False)
            window_icon(self.window)
            self.window.configure(background="#f1faf6")
            self.window.protocol("WM_DELETE_WINDOW", self.cancel)
            frame = ttk.Frame(self.window, padding=24)
            frame.pack(fill="both", expand=True)
            ttk.Label(frame, text=output_format.upper() + " · " + MODES[mode], font=("Segoe UI", 14, "bold")).pack(anchor="w")
            self.label = tk.StringVar(value="Memulai konversi " + str(count) + " gambar…")
            ttk.Label(frame, textvariable=self.label, wraplength=510).pack(anchor="w", pady=(12, 8))
            self.bar = ttk.Progressbar(frame, mode="indeterminate")
            self.bar.pack(fill="x")
            self.bar.start(12)
            self.cancel_button = ttk.Button(frame, text="Batalkan", command=self.cancel)
            self.cancel_button.pack(anchor="e", pady=(12, 0))
            self.window.update()
            return
        if not headless:
            self.proc = subprocess.Popen(
                ["zenity", "--progress", "--pulsate", "--auto-close", "--no-markup",
                 "--title=Convert Image — " + output_format.upper() + " — " + MODES[mode], "--width=520",
                 "--text=Memulai konversi " + str(count) + " gambar..."],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                text=True)

    def check(self):
        if self.window:
            self.window.update()
        if self.cancelled:
            raise Cancelled()
        if self.proc and self.proc.poll() is not None:
            raise Cancelled()

    def cancel(self):
        self.cancelled = True
        self.label.set("Membatalkan proses…")
        self.cancel_button.configure(state="disabled")

    def update(self, text):
        self.check()
        if self.window:
            self.label.set(text.replace("\n", " ").replace("\r", " "))
            self.window.update()
        if self.proc:
            try:
                self.proc.stdin.write("# " + text.replace("\n", " ").replace("\r", " ") + "\n")
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError):
                raise Cancelled()

    def close(self):
        if self.window:
            self.bar.stop()
            self.window.destroy()
            self.window = None
        if self.proc:
            try:
                self.proc.stdin.close()
                self.proc.wait(timeout=2)
            except (BrokenPipeError, OSError, subprocess.TimeoutExpired):
                if self.proc.poll() is None:
                    self.proc.terminate()
                    self.proc.wait()


def run(command, progress, log):
    progress.check()
    log.write("COMMAND " + repr(command) + "\n")
    log.flush()
    command = list(command)
    if windows() and command[0] in ("avifenc", "avifdec"):
        command[0] = find_tool(command[0]) or command[0]
    proc = subprocess.Popen(command, stdout=log, stderr=log, **process_options())
    try:
        while proc.poll() is None:
            progress.check()
            time.sleep(0.15)
        progress.check()
        if proc.returncode:
            raise RuntimeError(Path(command[0]).name + " gagal; lihat log")
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()


def prepare(source, mode, cfg, output_format="avif"):
    with source.open("rb") as stream:
        header = stream.read(29)
    # Pillow otherwise silently reduces RGB/RGBA 16-bit PNGs to 8-bit.
    if output_format in ("avif", "png", "webp") and mode == "high" and header[:8] == b"\x89PNG\r\n\x1a\n" and len(header) > 24 and header[24] > 8:
        raise ValueError("PNG 16-bit: High Quality dilewati agar tidak menurunkan kedalaman warna")
    with Image.open(source) as original:
        if original.format not in ("JPEG", "PNG", "WEBP"):
            raise ValueError("Isi file bukan JPEG, PNG, atau WebP")
        if getattr(original, "n_frames", 1) != 1:
            raise ValueError("Animasi dilewati; skrip ini untuk gambar diam")
        if output_format in ("avif", "png", "webp") and mode == "high" and original.mode not in ("1", "L", "LA", "P", "RGB", "RGBA"):
            raise ValueError("High Quality memerlukan gambar RGB/grayscale 8-bit; mode " + original.mode + " dilewati")
        image = ImageOps.exif_transpose(original)
        profile = original.info.get("icc_profile")
        # Normalize CMYK JPEGs through their ICC profile for the lossy presets.
        if image.mode == "CMYK":
            if profile:
                srgb = ImageCms.createProfile("sRGB")
                image = ImageCms.profileToProfile(image, ImageCms.ImageCmsProfile(io.BytesIO(profile)), srgb, outputMode="RGB")
                profile = ImageCms.ImageCmsProfile(srgb).tobytes()
            else:
                image = image.convert("RGB")
        alpha = "A" in image.getbands() or "transparency" in image.info
        image = image.convert("RGBA" if alpha else "RGB")
        if mode != "high":
            edge = cfg[mode + "_edge"]
            resampling = getattr(Image, "Resampling", Image)
            image.thumbnail((edge, edge), resampling.LANCZOS)
        # Keep ICC, bake orientation, and omit EXIF/XMP metadata from the PNG.
        image.info.clear()
        if profile:
            image.info["icc_profile"] = profile
        return image


def encoder_args(mode, cfg, modern):
    args = ["avifenc", "--codec", "aom", "--speed", str(cfg["speed"]),
            "--jobs", str(cfg["threads"]), "--depth", "8", "--range", "full"]
    if mode == "high":
        args += ["--lossless", "--yuv", "444", "--cicp", "1/13/0"]
    else:
        args += ["--yuv", "420"]
        quality = cfg[mode + "_quality"]
        if modern:
            args += ["--qcolor", str(quality), "--qalpha", "100"]
        else:
            quantizer = str(round((100 - quality) * 63 / 100))
            args += ["--min", quantizer, "--max", quantizer,
                     "--minalpha", "0", "--maxalpha", "0"]
    return args


def publish(encoded, source, mode, output_format="avif"):
    """No overwrite even when separate jobs target the same name."""
    base = source.stem + "-" + mode
    for index in range(10000):
        suffix = "" if index == 0 else "-" + str(index)
        target = source.with_name(base + suffix + "." + output_format)
        try:
            os.link(encoded, target)
            return target
        except FileExistsError:
            continue
        except OSError as exc:
            if exc.errno not in (errno.EPERM, errno.EOPNOTSUPP, errno.ENOSYS, errno.EXDEV):
                raise
            # FAT/SMB may not support hard links. Exclusive create is still safe.
            try:
                descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            except FileExistsError:
                continue
            try:
                with os.fdopen(descriptor, "wb") as output, encoded.open("rb") as data:
                    shutil.copyfileobj(data, output)
                return target
            except BaseException:
                target.unlink(missing_ok=True)
                raise
    raise RuntimeError("Terlalu banyak hasil dengan nama yang sama")


def encode_pdf(image, encoded, mode, cfg, progress):
    """One image per page, preserving aspect ratio with no margins or cropping."""
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader

    progress.update("Encoding PDF")
    jpeg = io.BytesIO()
    image.save(jpeg, format="JPEG", quality=cfg["pdf_" + mode + "_quality"],
               subsampling=0 if mode == "high" else 2, optimize=True, progressive=True)
    jpeg.seek(0)
    progress.check()
    # Nominal 96 dpi; keep unusually wide/tall pages within the PDF page limit.
    scale = min(72 / 96, 14400 / max(image.size))
    width, height = (edge * scale for edge in image.size)
    canvas = Canvas(str(encoded), pagesize=(width, height), pageCompression=1, invariant=1)
    canvas.setTitle("Converted image")
    canvas.drawImage(ImageReader(jpeg), 0, 0, width=width, height=height)
    canvas.showPage()
    canvas.save()
    progress.check()
    with encoded.open("rb") as stream:
        reader = PdfReader(stream, strict=True)
        if len(reader.pages) != 1:
            raise RuntimeError("Verifikasi PDF gagal: jumlah halaman")
        page = reader.pages[0]
        if abs(float(page.mediabox.width) - width) > 0.01 or abs(float(page.mediabox.height) - height) > 0.01:
            raise RuntimeError("Verifikasi PDF gagal: ukuran halaman")
        objects = page["/Resources"]["/XObject"].get_object()
        images = [obj.get_object() for obj in objects.values() if obj.get_object().get("/Subtype") == "/Image"]
        if len(images) != 1 or (images[0]["/Width"], images[0]["/Height"]) != image.size:
            raise RuntimeError("Verifikasi PDF gagal: dimensi gambar")
        with Image.open(io.BytesIO(images[0].get_data())) as check:
            check.load()
            if check.size != image.size:
                raise RuntimeError("Verifikasi PDF gagal: decode gambar")


def convert(source, mode, cfg, modern, progress, log, output_format="avif"):
    if output_format not in ("avif", "jpg", "pdf", "png", "webp"):
        raise ValueError("Format output tidak didukung")
    if source.suffix.lower() not in EXTENSIONS or not source.is_file():
        raise ValueError("File tidak didukung atau tidak ditemukan")
    with tempfile.TemporaryDirectory(prefix=".img2avif-", dir=source.parent) as scratch:
        temp = Path(scratch)
        input_source = source
        if source.suffix.lower() == ".avif":
            # Use libavif even on systems whose Pillow has no AVIF plugin.
            info = temp / "avif-info.txt"
            with info.open("w", encoding="utf-8") as metadata:
                run(["avifdec", "--info", str(source)], progress, metadata)
            report = info.read_text(encoding="utf-8", errors="replace")
            log.write(report)
            frames = re.findall(r"^\s*\*\s+\d+ timescales per second.*?,\s*(\d+) frames?\s*$", report, re.MULTILINE)
            depth = re.findall(r"^\s*\*\s+Bit Depth\s*:\s*(\d+)\s*$", report, re.MULTILINE)
            if not frames or not depth:
                raise ValueError("Tidak dapat memverifikasi metadata AVIF")
            if int(frames[-1]) != 1:
                raise ValueError("Animasi AVIF dilewati; skrip ini untuk gambar diam")
            if int(depth[-1]) > 8 and mode == "high" and output_format in ("avif", "png", "webp"):
                raise ValueError("AVIF di atas 8-bit dilewati pada High Quality lossless")
            input_source = temp / "decoded-input.png"
            run(["avifdec", "--depth", "8", str(source), str(input_source)], progress, log)
        image = prepare(input_source, mode, cfg, output_format)
        png, encoded, decoded = temp / "input.png", temp / ("output." + output_format), temp / "check.png"
        if output_format in ("png", "webp"):
            progress.update("Encoding " + output_format.upper() + ": " + source.name)
            if output_format == "png":
                image.save(encoded, format="PNG", optimize=True, compress_level=9)
            else:
                if max(image.size) > 16383:
                    raise ValueError("WebP maksimum 16383 piksel per sisi; pilih Standard atau Small Size")
                image.save(encoded, format="WEBP", lossless=mode == "high",
                           quality=100 if mode == "high" else cfg["webp_" + mode + "_quality"],
                           method=6, exact=True, icc_profile=image.info.get("icc_profile", b""))
            progress.check()
            with Image.open(encoded) as check:
                check.load()
                if check.format != output_format.upper() or check.size != image.size:
                    raise RuntimeError("Verifikasi format/dimensi gagal")
                if (output_format == "png" or mode == "high") and check.convert("RGBA").tobytes() != image.convert("RGBA").tobytes():
                    raise RuntimeError("Verifikasi lossless gagal: piksel berubah; hasil tidak disimpan")
            progress.check()
            return publish(encoded, source, mode, output_format), image.size
        if output_format in ("jpg", "pdf"):
            # JPEG has no alpha channel; composite on white instead of discarding alpha.
            profile = image.info.get("icc_profile")
            if image.mode == "RGBA":
                background = Image.new("RGB", image.size, "white")
                background.paste(image, mask=image.getchannel("A"))
                image = background
            else:
                image = image.convert("RGB")
            if output_format == "pdf":
                # PDF DeviceRGB uses sRGB pixels rather than an untagged source profile.
                if profile:
                    srgb = ImageCms.createProfile("sRGB")
                    image = ImageCms.profileToProfile(image, ImageCms.ImageCmsProfile(io.BytesIO(profile)), srgb, outputMode="RGB")
                encode_pdf(image, encoded, mode, cfg, progress)
                progress.check()
                return publish(encoded, source, mode, output_format), image.size
            progress.update("Encoding JPG: " + source.name)
            image.save(encoded, format="JPEG", quality=cfg["jpg_" + mode + "_quality"],
                       subsampling=0 if mode == "high" else 2, optimize=True,
                       progressive=True, icc_profile=profile)
            progress.check()
            with Image.open(encoded) as check:
                check.load()
                if check.format != "JPEG" or check.size != image.size:
                    raise RuntimeError("Verifikasi JPG gagal")
            target = publish(encoded, source, mode, output_format)
            return target, image.size
        image.save(png, format="PNG", compress_level=1)
        run(encoder_args(mode, cfg, modern) + [str(png), str(encoded)], progress, log)
        if not encoded.is_file() or not encoded.stat().st_size:
            raise RuntimeError("Encoder tidak menghasilkan AVIF")
        progress.update("Memeriksa hasil: " + source.name)
        run(["avifdec", str(encoded), str(decoded)], progress, log)
        with Image.open(decoded) as check:
            if check.size != image.size:
                raise RuntimeError("Verifikasi dimensi gagal")
            if mode == "high" and check.convert("RGBA").tobytes() != image.convert("RGBA").tobytes():
                raise RuntimeError("Verifikasi lossless gagal: piksel berubah; hasil tidak disimpan")
        progress.check()
        target = publish(encoded, source, mode)
    return target, image.size


def main():
    if windows():
        for stream in (sys.stdout, sys.stderr):
            if stream is not None and hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) == 3 and sys.argv[1] == "--request":
        request = Path(sys.argv[2])
        try:
            payload = json.loads(request.read_text(encoding="utf-8"))
            if not isinstance(payload.get("files"), list) or not payload["files"] or not all(isinstance(p, str) for p in payload["files"]):
                raise ValueError("Daftar gambar tidak valid")
            options = ["--no-gui"] if payload.get("no_gui") is True else []
            sys.argv[1:] = ["--format", payload.get("format", "avif"), payload["mode"], *options, "--", *payload["files"]]
        finally:
            request.unlink(missing_ok=True)
    parser = argparse.ArgumentParser(description="Convert Image untuk Linux dan Windows")
    parser.add_argument("--format", choices=("avif", "jpg", "pdf", "png", "webp"), default="avif", dest="output_format")
    parser.add_argument("mode", choices=MODES)
    parser.add_argument("--no-gui", action="store_true")
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    progress = None
    try:
        required = (["avifenc", "avifdec"] if args.output_format == "avif" else []) + ([] if args.no_gui or windows() else ["zenity"])
        if any(Path(filename).suffix.lower() == ".avif" for filename in args.files) and "avifdec" not in required:
            required.append("avifdec")
        for tool in required:
            if not find_tool(tool):
                raise RuntimeError("Program belum terpasang: " + tool)
        if args.output_format == "pdf":
            try:
                import reportlab
                import pypdf
            except ImportError as exc:
                raise RuntimeError("Dependensi PDF belum tersedia; jalankan ulang installer: " + str(exc))
        cfg = settings()
        modern = False
        if args.output_format == "avif":
            probe = subprocess.run([find_tool("avifenc"), "--help"], capture_output=True, text=True,
                                   encoding="utf-8", errors="replace", check=True, **process_options())
            modern = "--qcolor" in probe.stdout + probe.stderr
        cache = user_directory("cache")
        cache.mkdir(parents=True, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix="convert-", suffix=".log", dir=cache)
        logpath = Path(name)
        done, errors, total_in, total_out = [], [], 0, 0
        cancelled = False
        progress = Progress(args.mode, len(args.files), args.no_gui, args.output_format)
        with os.fdopen(descriptor, "w", encoding="utf-8") as log:
            for number, filename in enumerate(args.files, 1):
                source = Path(os.path.abspath(filename))
                try:
                    progress.update("{}/{} — {} (mohon tunggu)".format(number, len(args.files), source.name))
                    before = source.stat().st_size
                    target, size = convert(source, args.mode, cfg, modern, progress, log, args.output_format)
                    after = target.stat().st_size
                    total_in += before
                    total_out += after
                    line = "{} → {} | {}×{} | {} → {} byte".format(source.name, target.name, *size, before, after)
                    done.append(line)
                    log.write("OK " + line + "\n")
                except Cancelled:
                    cancelled = True
                    log.write("DIBATALKAN\n")
                    break
                except Exception as exc:
                    line = source.name + ": " + str(exc)
                    errors.append(line)
                    log.write("GAGAL " + line + "\n")
                log.flush()
        progress.close()
        progress = None
        summary = "{}\nBerhasil: {} | Gagal/dilewati: {}".format(args.output_format.upper() + " — " + MODES[args.mode], len(done), len(errors))
        if cancelled:
            summary += "\nDibatalkan. Hasil yang sudah selesai tetap tersimpan."
        if total_in:
            summary += "\nTotal: {:.1f} KB → {:.1f} KB ({:+.1f}%)".format(total_in / 1024, total_out / 1024, (total_out / total_in - 1) * 100)
        summary += "\n\nHasil ada di folder gambar asli.\nLog: " + str(logpath)
        if errors:
            summary += "\n\n" + "\n".join(errors[:4])
        print(summary)
        if not args.no_gui:
            message(summary, error=bool(errors) and not done)
        return 130 if cancelled else (1 if errors else 0)
    except Cancelled:
        return 130
    except Exception as exc:
        print(str(exc))
        if not args.no_gui and (windows() or shutil.which("zenity")):
            message(str(exc), error=True)
        return 1
    finally:
        if progress:
            progress.close()


if __name__ == "__main__":
    def stop(_signum, _frame):
        raise Cancelled()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    raise SystemExit(main())
