# Panduan build Windows

[Kembali ke panduan pengguna](../README.md)

Versi Windows x64 memakai mesin konversi yang sama dengan Linux. Dialognya memakai
Tkinter; PyInstaller menyertakan Python dan pustaka yang diperlukan. Codec AVIF
berasal dari rilis resmi libavif v1.4.2 dengan SHA-256 yang dipin di
[`windows/build.ps1`](../windows/build.ps1).

## Membangun installer

Gunakan Windows x64 dengan Python 3.12 x64, Visual Studio C++ Build Tools (termasuk
Windows SDK), Inno Setup 6, dan akses internet. Dari folder utama proyek, jalankan:

```powershell
./windows/build.ps1
```

Hasilnya berada di `dist/Convert-Image-3.0.0-Windows-x64-Setup.exe`.
Workflow [Test and build](../.github/workflows/build.yml) juga menjalankan proses ini
di Windows Server 2022. Installer dibuat hanya setelah tes source lolos; artefak
diunggah hanya setelah pengujian paket dan installer lolos.

## Integrasi File Explorer

Ekstensi C++ native memakai `IShellExtInit` dan `IContextMenu` untuk mengambil semua
file dalam satu pilihan. Lima submenu format masing-masing berisi tiga kualitas.
Jalur file dikirim dalam satu berkas JSON UTF-8, sehingga spasi, Unicode, karakter
khusus, dan banyak file tidak diubah menjadi perintah shell. Konversi berjalan
di proses terpisah dari Explorer.

Pendaftaran COM dan asosiasi menu hanya dibuat di
`HKEY_CURRENT_USER\Software\Classes`. Installer tidak mengubah aplikasi pembuka
gambar bawaan. Uninstall menghapus hanya pendaftaran milik Convert Image.

Menu memakai integrasi klasik; di Windows 11 gunakan **Show more options**.
Menu modern langsung belum disediakan. Target paket adalah Windows x64; Windows
ARM64 dan 32-bit belum didukung.

## Data pengguna

- Pengaturan: `%LOCALAPPDATA%\Convert Image\config\config.json`
- Log: `%LOCALAPPDATA%\Convert Image\cache\`
- Aplikasi: `%LOCALAPPDATA%\Programs\Convert Image\` secara default

Pengaturan dan log tetap disimpan setelah uninstall. Batas kualitas dan perilaku
format dijelaskan pada [panduan teknis](advanced.md).

## Pemeriksaan sebelum rilis

Build menjalankan seluruh tes lintas format dengan codec asli. Setelah dikemas,
pengujian memasang aplikasi pada folder dengan spasi dan Unicode, menjalankan 30
konversi melalui protokol batch, memeriksa 15 aksi menu native dan aktivasi COM,
kemudian memeriksa pembaruan tanpa menimpa pengaturan serta uninstall tanpa
menghapus hasil gambar.

Pengujian otomatis tidak menggantikan pemeriksaan tampilan menu pada desktop
Windows 10/11. Rilis awal diberi label **pratinjau** sampai verifikasi desktop
selesai. Installer belum memakai tanda tangan digital.

Referensi: [integrasi menu klasik Microsoft](https://learn.microsoft.com/en-us/windows/win32/shell/context-menu-handlers),
[pengemasan PyInstaller](https://pyinstaller.org/en/stable/operating-mode.html).
