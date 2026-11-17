# Nemo Convert Img2Avif

Konversi JPG, JPEG, PNG, dan WebP ke AVIF melalui menu klik kanan **Nemo**. Dibuat untuk Linux Mint Cinnamon, dengan tiga preset, pemrosesan banyak file, dan installer untuk pengguna desktop.

**Klik kanan gambar → Convert Img2Avif → High Quality / Standard / Small Size.**

## Pilihan kualitas

| Preset | Resolusi | Encoding |
| --- | --- | --- |
| **High Quality** | Resolusi asli | Lossless RGB/grayscale 8-bit, 4:4:4; piksel hasil decode dibandingkan sebelum disimpan |
| **Standard** | Sisi terpanjang maksimal **1920 px** | Lossy, kualitas **60**, 4:2:0 |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | Lossy, kualitas **40**, 4:2:0 |

Rasio gambar dipertahankan dan gambar kecil tidak diperbesar. Semua preset memakai **libaom, speed 0**, untuk mengutamakan kompresi dengan waktu encoding paling lambat. Maksimal 4 thread digunakan secara default. Ukuran akhir bergantung pada isi gambar; tidak ada target ukuran file yang dijamin.

**Lossless dapat menghasilkan file lebih besar daripada JPEG atau WebP asal.** Lossless berarti piksel gambar 8-bit yang sudah didekode dan disesuaikan orientasinya tetap sama. Ini tidak mengembalikan detail yang sudah hilang pada JPEG/WebP lossy, dan bukan salinan identik seluruh metadata file asli.

## Instalasi

### Unduh satu installer

Unduh [install-img2avif.sh](https://raw.githubusercontent.com/endyardhie/Nemo-Convert-Img2Avif/main/install-img2avif.sh), lalu jalankan sebagai pengguna desktop biasa:

```bash
bash "$(xdg-user-dir DOWNLOAD)/install-img2avif.sh"
```

### Dari GitHub

```bash
git clone https://github.com/endyardhie/Nemo-Convert-Img2Avif.git
cd Nemo-Convert-Img2Avif
bash install-img2avif.sh
```

Jangan menjalankan installer dengan `sudo bash`. Installer hanya menggunakan sudo untuk memasang paket APT; file aplikasinya dipasang untuk pengguna saat ini.

Setelah pemasangan selesai, tunggu aktivitas salin/pindah file di Nemo selesai, lalu jalankan:

```bash
nemo -q
```

Buka kembali Nemo, pilih satu atau beberapa gambar, lalu **klik kanan → Convert Img2Avif → pilih preset**. Jika menu belum muncul, periksa **Edit → Plugins** dan aktifkan ekstensi yang terkait, lalu mulai ulang Nemo.

## Perilaku aplikasi

- File asli tidak ditimpa atau dihapus.
- Hasil disimpan di folder sumber: `foto-high.avif`, `foto-standard.avif`, atau `foto-small.avif`.
- Jika nama sudah ada, nomor ditambahkan, misalnya `foto-high-1.avif`.
- Mendukung nama file dengan spasi, Unicode, dan karakter khusus tanpa mengeksekusinya sebagai perintah shell.
- Batch diproses berurutan di luar proses Nemo agar file manager tetap responsif.
- Dialog menampilkan file yang sedang diproses, tombol batal, dan ringkasan ukuran setelah selesai.
- Batal menghentikan encoder aktif; hasil yang sudah selesai tetap disimpan.
- Transparansi dan profil ICC diteruskan. Orientasi EXIF diterapkan ke piksel; EXIF/XMP tidak disalin.
- Setiap hasil didekode untuk pemeriksaan dimensi. High Quality juga memeriksa kesamaan seluruh piksel RGBA.

## Persyaratan dan batasan

Target utama: **Linux Mint 22.x Cinnamon**, Nemo, Python sistem, Pillow, `libavif-bin` dengan encoder libaom, Zenity, dan binding Python Nemo. Integrasi menu perlu diperiksa pada desktop Nemo pengguna; pengujian otomatis headless tidak membuktikan tampilnya menu pada setiap versi desktop.

Nama paket binding berbeda menurut distribusi:

| Sistem | Paket |
| --- | --- |
| Linux Mint | `python-nemo` |
| Ubuntu / Debian | `nemo-python` |

Paket lain: `python3`, `python3-gi`, `gir1.2-nemo-3.0`, `python3-pil`, `libavif-bin`, `zenity`.

- Gambar animasi WebP/APNG dilewati; aplikasi ini hanya untuk gambar diam.
- High Quality melewati PNG lebih dari 8-bit dan JPEG CMYK agar tidak mengklaim lossless setelah menurunkan kedalaman atau mengubah model warna.
- Standard/Small menghasilkan RGB/RGBA 8-bit; kedalaman PNG 16-bit akan berkurang. JPEG CMYK dengan profil ICC dikonversi melalui profilnya; tanpa profil digunakan konversi bawaan Pillow.
- Hanya file lokal/mount dengan path lokal yang didukung. File perlu bisa dibaca dan folder sumber perlu bisa ditulis.
- Dibutuhkan ruang sementara untuk PNG dan hasil decode. Foto besar dengan speed 0 bisa membutuhkan waktu beberapa menit atau lebih.
- Encoding yang gagal atau tidak lolos pemeriksaan tidak dipublikasikan sebagai hasil akhir.

## Konfigurasi

Pengaturan dibuat di `~/.config/img2avif/config.json` (atau `$XDG_CONFIG_HOME/img2avif/config.json`):

```json
{
  "speed": 0,
  "threads": 4,
  "standard_edge": 1920,
  "standard_quality": 60,
  "small_edge": 1280,
  "small_quality": 40
}
```

`speed` berada pada rentang 0–10: 0 paling lambat; angka lebih tinggi mempercepat encoding dan dapat mengubah ukuran file. Untuk penggunaan harian yang lebih cepat, coba 4 atau 6. `threads` dibatasi jumlah CPU yang tersedia. Perubahan konfigurasi dibaca pada konversi berikutnya. Tooltip menu menunjukkan nilai default.

Installer tidak menimpa konfigurasi yang sudah ada.

## Update, pemeriksaan, dan uninstall

```bash
# Update dari checkout Git yang sudah ada
git pull --ff-only
bash install-img2avif.sh

# Periksa dependensi tanpa mengubah file atau menjalankan APT
bash install-img2avif.sh --check

# Lewati pemasangan paket APT, tetap periksa dependensi
bash install-img2avif.sh --no-deps

# Hapus menu, converter, dan launcher
bash install-img2avif.sh --uninstall
```

Uninstall juga dapat dijalankan dengan `bash uninstall.sh` dari checkout. Konfigurasi, log, backup, dan gambar tetap disimpan. Mulai ulang Nemo setelah update atau uninstall.

File aplikasi berada di `~/.local/share/img2avif/convert.py` dan `~/.local/share/nemo-python/extensions/nemo_img2avif.py`, mengikuti `$XDG_DATA_HOME` bila diatur. Launcher dipasang di `~/.local/bin/img2avif`. File lama dicadangkan di `~/.local/share/img2avif-backups/` sebelum diubah; bila penulisan gagal, installer mencoba memulihkan file yang sudah diubah.

CLI dapat digunakan bila `~/.local/bin` ada dalam PATH:

```bash
img2avif standard --no-gui -- "/path/foto satu.jpg" "/path/foto dua.png"
```

## Troubleshooting

**APT gagal:** perbaiki repo yang disebut pada output APT, lalu jalankan installer lagi. Installer tidak mengubah repo sistem dan berhenti sebelum mengubah aplikasi bila pemasangan dependensi gagal.

**Repo Cloudflare meminta `zena`:** untuk Linux Mint berbasis Ubuntu 24.04, repo WARP perlu suite Ubuntu `noble`, bukan kode Mint. Ubah hanya entri Cloudflare yang bermasalah, mengikuti [petunjuk Cloudflare](https://pkg.cloudflareclient.com/). Pemberitahuan bahwa repo tidak mendukung `i386` berbeda dengan error `Release file` dan bukan penyebab paket `python3-nemo` tidak ditemukan.

**Paket `python3-nemo` tidak ditemukan:** paket Linux Mint bernama `python-nemo`; versi installer dalam repo ini sudah menggunakan nama tersebut.

**Konversi gagal:** lihat log pada dialog hasil, di `~/.cache/img2avif/` (atau `$XDG_CACHE_HOME/img2avif/`). Jalankan preset melalui CLI untuk melihat ringkasan di terminal. Log dapat berisi nama/path file lokal; periksa isinya sebelum membagikannya.

## Pengembangan dan pengujian

Source utama berada di `src/`; jangan mengedit payload installer secara manual. Setelah mengubah source:

```bash
python3 scripts/build_installer.py
bash -n install-img2avif.sh uninstall.sh
python3 scripts/build_installer.py --check
python3 -m unittest discover -s tests -v
```

Tes integrasi AVIF memakai `avifenc` dan `avifdec` asli jika tersedia; bila tidak tersedia, tes tersebut ditandai **skipped**, bukan dianggap lulus. Tes tidak memasang paket maupun me-restart Nemo. Sebelum rilis, lakukan juga pemasangan dan klik kanan manual pada Linux Mint Cinnamon.

## Referensi

- [Paket resmi Linux Mint Zena](https://fastly.linuxmint.io/list.php?release=zena)
- [Nemo Python bindings](https://github.com/linuxmint/nemo-extensions/tree/master/nemo-python)
- [libavif / avifenc](https://github.com/AOMediaCodec/libavif)
- [Opsi avifenc Ubuntu 24.04](https://manpages.ubuntu.com/manpages/noble/man1/avifenc.1.html)

## Lisensi

[MIT](LICENSE) — Endy Ardhie.
