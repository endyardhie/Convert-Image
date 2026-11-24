"""Windows entry point, with a file picker when opened from the Start menu."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import convert


def choose_images():
    import tkinter as tk
    from tkinter import filedialog, ttk

    root = tk.Tk()
    root.withdraw()
    convert.window_icon(root)
    files = filedialog.askopenfilenames(
        parent=root, title="Pilih gambar — Convert Image",
        filetypes=[("Gambar", "*.jpg *.jpeg *.png *.webp *.avif")])
    if not files:
        root.destroy()
        return False
    root.deiconify()
    root.title("Convert Image")
    root.geometry("460x360")
    root.resizable(False, False)
    frame = ttk.Frame(root, padding=24)
    frame.pack(fill="both", expand=True)
    ttk.Label(frame, text="Convert Image", font=("Segoe UI", 19, "bold")).pack(anchor="w")
    ttk.Label(frame, text=str(len(files)) + " gambar dipilih · file asli tetap tersimpan").pack(anchor="w", pady=(6, 18))
    ttk.Label(frame, text="Simpan sebagai").pack(anchor="w")
    output = ttk.Combobox(frame, values=["Avif", "Jpg", "Pdf", "Png", "Webp"], state="readonly")
    output.set("Jpg")
    output.pack(fill="x", pady=(3, 10))
    quality = ttk.Combobox(frame, values=list(convert.MODES.values()), state="readonly")
    quality.set("Standard")
    quality.pack(fill="x")
    result = []

    def start():
        mode = next(key for key, value in convert.MODES.items() if value == quality.get())
        result.extend(["--format", output.get().lower(), mode, "--", *files])
        root.destroy()

    ttk.Button(frame, text="Mulai konversi", command=start).pack(anchor="e", pady=(16, 0))
    root.mainloop()
    if result:
        sys.argv[1:] = result
    return bool(result)


if __name__ == "__main__":
    if len(sys.argv) == 1 and not choose_images():
        raise SystemExit(0)
    raise SystemExit(convert.main())
