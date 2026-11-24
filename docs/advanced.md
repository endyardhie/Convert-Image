# Panduan teknis Convert Image

[Kembali ke panduan pengguna](../README.md)

Panduan build dan struktur paket Windows tersedia di [panduan Windows](windows.md). Lokasi konfigurasi Windows adalah `%LOCALAPPDATA%\Convert Image\config\config.json`, dan log berada di `%LOCALAPPDATA%\Convert Image\cache\`. Perintah APT dan jalur XDG di bawah berlaku untuk Linux.

Halaman ini berisi rincian kualitas, pengaturan tambahan, penggunaan melalui terminal, serta panduan pemeriksaan dan pengembangan. Untuk pemasangan dan penggunaan sehari-hari, ikuti [panduan utama](../README.md).

Perintah yang memakai file proyek dijalankan dari folder utama hasil clone repositori.

## Pilihan kualitas

### Avif

| Preset | Resolusi | Encoding |
| --- | --- | --- |
| **High Quality** | Resolusi asli | Lossless RGB/grayscale 8-bit, 4:4:4; piksel hasil decode dibandingkan sebelum disimpan |
| **Standard** | Sisi terpanjang maksimal **1920 px** | Lossy, kualitas **60**, 4:2:0 |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | Lossy, kualitas **40**, 4:2:0 |

Rasio gambar dipertahankan dan gambar kecil tidak diperbesar. Semua preset AVIF memakai **libaom, speed 0**, untuk mengutamakan kompresi dengan waktu encoding paling lambat. Maksimal 4 thread digunakan secara default. Ukuran akhir bergantung pada isi gambar; tidak ada target ukuran file yang dijamin.

**Lossless dapat menghasilkan file lebih besar daripada JPEG atau WebP asal.** Lossless berarti piksel gambar 8-bit yang sudah didekode dan disesuaikan orientasinya tetap sama. Ini tidak mengembalikan detail yang sudah hilang pada JPEG/WebP lossy, dan bukan salinan identik seluruh metadata file asli.

### Jpg

| Preset | Resolusi | Encoding |
| --- | --- | --- |
| **High Quality** | Resolusi asli | JPEG kualitas **95**, 4:4:4 |
| **Standard** | Sisi terpanjang maksimal **1920 px** | JPEG kualitas **85**, 4:2:0 |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | JPEG kualitas **70**, 4:2:0 |

Semua preset JPG memakai encoding **lossy**, `optimize` dan progressive JPEG dari Pillow. JPG tidak mendukung transparansi: area transparan dikompositkan pada latar putih. Profil ICC diteruskan; orientasi EXIF diterapkan, metadata EXIF/XMP tidak disalin. Resolusi tidak diperbesar. Re-encode JPG dapat mengurangi kualitas dan dapat menghasilkan file yang lebih besar, terutama pada High Quality.

### Pdf

Satu gambar menghasilkan **satu file PDF satu halaman**, bukan menggabungkan batch ke satu dokumen. Input berupa JPG/JPEG, PNG, WebP, atau AVIF; aplikasi ini tidak mengonversi dokumen PDF sebagai input.

| Preset | Resolusi gambar di PDF | Kompresi gambar |
| --- | --- | --- |
| **High Quality** | Resolusi asli | JPEG kualitas **95**, 4:4:4 |
| **Standard** | Sisi terpanjang maksimal **1920 px** | JPEG kualitas **85**, 4:2:0 |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | JPEG kualitas **70**, 4:2:0 |

PDF mengikuti rasio gambar, tanpa crop atau margin tambahan, dengan ukuran halaman nominal 96 dpi (halaman sangat panjang dibatasi sambil menjaga rasio). Area transparan memakai latar putih; orientasi EXIF diterapkan dan gambar dengan profil ICC dinormalisasi ke sRGB. Gambar di dalam PDF memakai kompresi lossy, termasuk High Quality. PDF ini berupa gambar, tanpa OCR atau teks yang dapat dipilih. Ukuran file akhir tidak dijamin lebih kecil.

PDF dibuat menggunakan ReportLab dan diperiksa ulang menggunakan pypdf: jumlah halaman, ukuran halaman, dimensi gambar, dan kemampuan decode gambar di dalamnya diperiksa sebelum file dipublikasikan.

### Png

| Preset | Resolusi | Encoding |
| --- | --- | --- |
| **High Quality** | Resolusi asli | PNG lossless 8-bit, kompresi maksimum |
| **Standard** | Sisi terpanjang maksimal **1920 px** | PNG lossless setelah resize |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | PNG lossless setelah resize |

Semua preset memakai `optimize` dan kompresi level 9, tanpa pengurangan palet warna. Perbedaan kualitas Standard/Small terletak pada resolusi: encoding PNG mempertahankan piksel hasil resize. Transparansi dan profil ICC dipertahankan. PNG dapat jauh lebih besar daripada JPG, AVIF, atau WebP.

### Webp

| Preset | Resolusi | Encoding |
| --- | --- | --- |
| **High Quality** | Resolusi asli | WebP lossless 8-bit, method 6, exact alpha |
| **Standard** | Sisi terpanjang maksimal **1920 px** | WebP lossy kualitas **80**, method 6 |
| **Small Size** | Sisi terpanjang maksimal **1280 px** | WebP lossy kualitas **60**, method 6 |

Transparansi dan profil ICC dipertahankan. High Quality memverifikasi piksel RGBA hasil decode, termasuk warna di area transparan. Batas format WebP adalah 16383 piksel per sisi; gunakan Standard/Small untuk gambar yang melampaui batas tersebut.

### Input AVIF

AVIF dibaca melalui `avifdec`, sehingga tetap tersedia pada sistem yang Pillow-nya belum mendukung AVIF. Metadata jumlah frame diperiksa lebih dahulu; AVIF animasi/sequence dilewati. Input AVIF di atas 8-bit dilewati pada High Quality untuk output lossless (AVIF/PNG/WebP); preset lain menormalkan hasil ke 8-bit. Semua output dari input AVIF memerlukan `avifdec`.

## Memasang dari repositori

```bash
git clone https://github.com/endyardhie/Convert-Image.git
cd Convert-Image
bash install-image.sh
```

Jalankan installer sebagai pengguna desktop biasa, tanpa `sudo bash`. Setelah selesai, tunggu aktivitas salin/pindah file selesai, jalankan `nemo -q`, lalu buka kembali Nemo.

## Perilaku aplikasi

- File asli tidak ditimpa atau dihapus.
- Hasil disimpan di folder sumber: `foto-high.avif`, `foto-high.jpg`, `foto-high.pdf`, `foto-high.png`, atau `foto-high.webp`, sesuai format dan preset. Standard/Small memakai akhiran `-standard`/`-small`.
- Jika nama sudah ada, nomor ditambahkan, misalnya `foto-high-1.avif`.
- Mendukung nama file dengan spasi, Unicode, dan karakter khusus tanpa mengeksekusinya sebagai perintah shell.
- Batch diproses berurutan di luar proses Nemo agar file manager tetap responsif.
- Dialog menampilkan file yang sedang diproses, tombol batal, dan ringkasan ukuran setelah selesai.
- Batal menghentikan encoder AVIF aktif. Untuk JPG/PDF/PNG/WebP, pembatalan diperiksa setelah encoding selesai sebelum publikasi hasil. Hasil yang sudah selesai tetap disimpan.
- Pada AVIF/PNG/WebP, transparansi dan profil ICC diteruskan. Orientasi EXIF diterapkan ke piksel; EXIF/XMP tidak disalin.
- Setiap hasil didekode untuk pemeriksaan dimensi. High Quality AVIF/WebP dan semua preset PNG juga memeriksa kesamaan seluruh piksel RGBA terhadap gambar yang telah disiapkan (termasuk resize).

## Persyaratan dan batasan

Target utama: **Linux Mint 22.x Cinnamon**, Nemo, Python sistem, Pillow, `libavif-bin` dengan encoder libaom, Zenity, dan binding Python Nemo. Integrasi menu perlu diperiksa pada desktop Nemo pengguna; pengujian otomatis headless tidak membuktikan tampilnya menu pada setiap versi desktop.

Nama paket binding berbeda menurut distribusi:

| Sistem | Paket |
| --- | --- |
| Linux Mint | `python-nemo` |
| Ubuntu / Debian | `nemo-python` |

Paket lain: `python3`, `python3-gi`, `gir1.2-nemo-3.0`, `python3-pil`, `python3-reportlab`, `python3-pypdf`, `libavif-bin`, `zenity`.

- Gambar animasi WebP/APNG/AVIF dilewati; aplikasi ini hanya untuk gambar diam.
- High Quality untuk output lossless (AVIF/PNG/WebP) melewati PNG/AVIF lebih dari 8-bit dan JPEG CMYK agar tidak mengklaim lossless setelah menurunkan kedalaman atau mengubah model warna.
- Seluruh output memakai gambar 8-bit; kedalaman PNG 16-bit akan berkurang. JPEG CMYK dengan profil ICC dikonversi melalui profilnya; tanpa profil digunakan konversi bawaan Pillow.
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
  "small_quality": 40,
  "jpg_high_quality": 95,
  "jpg_standard_quality": 85,
  "jpg_small_quality": 70,
  "pdf_high_quality": 95,
  "pdf_standard_quality": 85,
  "pdf_small_quality": 70,
  "webp_standard_quality": 80,
  "webp_small_quality": 60
}
```

`speed` berada pada rentang 0–10: 0 paling lambat; angka lebih tinggi mempercepat encoding dan dapat mengubah ukuran file. Untuk penggunaan harian yang lebih cepat, coba 4 atau 6. `threads` dibatasi jumlah CPU yang tersedia. Perubahan konfigurasi dibaca pada konversi berikutnya. Tooltip menu menunjukkan nilai default.

Installer tidak menimpa konfigurasi yang sudah ada. Konfigurasi lama yang belum memiliki opsi `jpg_*`/`pdf_*` otomatis memakai default 95/85/70. Rentang kualitas JPG/PDF adalah 1–95; opsi `standard_quality`/`small_quality` dan `speed` khusus AVIF, sedangkan batas resolusi dipakai semua format. `webp_standard_quality` dan `webp_small_quality` memiliki rentang 1–100, default 80/60. PNG dan WebP High Quality tidak memakai nilai kualitas lossy. Semua opsi yang belum ada dalam konfigurasi lama memakai default.

## Update, pemeriksaan, dan uninstall

Jika checkout masih memakai alamat repo lama, perbarui remote terlebih dahulu:

```bash
git remote set-url origin https://github.com/endyardhie/Convert-Image.git
```

`install-image.sh` adalah installer utama. `install-img2avif.sh` tetap disediakan dengan payload yang sama untuk kompatibilitas tautan lama. CLI tanpa `--format` tetap menghasilkan AVIF.

```bash
# Update dari checkout Git yang sudah ada
git pull --ff-only
bash install-image.sh

# Periksa dependensi tanpa mengubah file atau menjalankan APT
bash install-image.sh --check

# Lewati pemasangan paket APT, tetap periksa dependensi
bash install-image.sh --no-deps

# Hapus menu, converter, dan launcher
bash install-image.sh --uninstall
```

Uninstall juga dapat dijalankan dengan `bash uninstall.sh` dari checkout. Konfigurasi, log, backup, dan gambar tetap disimpan. Mulai ulang Nemo setelah update atau uninstall.

File aplikasi berada di `~/.local/share/img2avif/convert.py` dan `~/.local/share/nemo-python/extensions/nemo_img2avif.py`, mengikuti `$XDG_DATA_HOME` bila diatur. Launcher utama dipasang di `~/.local/bin/convert-image`; `~/.local/bin/img2avif` tetap tersedia untuk kompatibilitas. Nama direktori konfigurasi, cache, dan ekstensi lama dipertahankan agar update tidak membuat dua menu atau kehilangan pengaturan. File lama dicadangkan di `~/.local/share/img2avif-backups/` sebelum diubah; bila penulisan gagal, installer mencoba memulihkan file yang sudah diubah.

CLI dapat digunakan bila `~/.local/bin` ada dalam PATH:

```bash
convert-image --format avif standard --no-gui -- "/path/foto satu.jpg" "/path/foto dua.png"
convert-image --format jpg small --no-gui -- "/path/foto satu.jpg"
convert-image --format pdf standard --no-gui -- "/path/foto satu.jpg" "/path/foto dua.png"
convert-image --format png high --no-gui -- "/path/foto.avif"
convert-image --format webp standard --no-gui -- "/path/foto.png"
```

### Dependensi PDF tanpa akses administrator

Installer APT memasang `python3-reportlab` dan `python3-pypdf`. Jika pemasangan paket sistem tidak tersedia tetapi Python pip sudah ada, alternatifnya pasang hanya untuk converter ini:

```bash
pdf_vendor="${XDG_DATA_HOME:-$HOME/.local/share}/img2avif/vendor"
python3 -m pip install --target "$pdf_vendor" 'reportlab>=3.6,<5' 'pypdf>=3,<7'
bash install-image.sh --no-deps
```

Converter dan pemeriksa dependensi installer dapat membaca folder `vendor` tersebut. Uninstall mempertahankan folder dependensi ini, seperti konfigurasi dan log. JPG, AVIF, PNG, dan WebP tidak menggunakan pustaka PDF pada proses konversinya.

## Troubleshooting

**APT gagal:** perbaiki repo yang disebut pada output APT, lalu jalankan installer lagi. Installer tidak mengubah repo sistem dan berhenti sebelum mengubah aplikasi bila pemasangan dependensi gagal.

**Repo Cloudflare meminta `zena`:** untuk Linux Mint berbasis Ubuntu 24.04, repo WARP perlu suite Ubuntu `noble`, bukan kode Mint. Ubah hanya entri Cloudflare yang bermasalah, mengikuti [petunjuk Cloudflare](https://pkg.cloudflareclient.com/). Pemberitahuan bahwa repo tidak mendukung `i386` berbeda dengan error `Release file` dan bukan penyebab paket `python3-nemo` tidak ditemukan.

**Paket `python3-nemo` tidak ditemukan:** paket Linux Mint bernama `python-nemo`; versi installer dalam repo ini sudah menggunakan nama tersebut.

**Konversi gagal:** lihat log pada dialog hasil, di `~/.cache/img2avif/` (atau `$XDG_CACHE_HOME/img2avif/`). Jalankan preset melalui CLI untuk melihat ringkasan di terminal. Log dapat berisi nama/path file lokal; periksa isinya sebelum membagikannya.

## Pengembangan dan pengujian

Source utama berada di `src/`; jangan mengedit payload installer secara manual. Setelah mengubah source:

```bash
python3 scripts/build_installer.py
bash -n install-image.sh install-img2avif.sh uninstall.sh
python3 scripts/build_installer.py --check
python3 -m unittest discover -s tests -v
```

Tes JPG memakai encoder JPEG Pillow asli, termasuk JPG → JPG, ketiga preset, alpha putih, profil ICC, kegagalan/batal, serta CLI tanpa codec AVIF. Hierarki lima belas aksi menu diuji dengan API Nemo tiruan. Tes PDF memeriksa ketiga preset, satu halaman per gambar, rasio dan dimensi, orientasi EXIF, alpha putih, penamaan tanpa overwrite, kegagalan/batal, kompatibilitas konfigurasi, dan batch CLI. Tes lintas format memeriksa 75 kombinasi: lima jenis input × lima output × tiga preset. AVIF sequence, decoder hilang, kesamaan piksel PNG/WebP lossless, profil ICC, dan kegagalan encoding juga diuji. Tes integrasi AVIF memakai `avifenc` dan `avifdec` asli jika tersedia; bila tidak tersedia, tes tersebut ditandai **skipped**, bukan dianggap lulus. Tes tidak memasang paket maupun me-restart Nemo. Sebelum rilis, lakukan juga pemasangan dan klik kanan manual pada Linux Mint Cinnamon.

## Referensi

- [Paket resmi Linux Mint Zena](https://fastly.linuxmint.io/list.php?release=zena)
- [Nemo Python bindings](https://github.com/linuxmint/nemo-extensions/tree/master/nemo-python)
- [Opsi JPEG Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#jpeg)
- [libavif / avifenc](https://github.com/AOMediaCodec/libavif)
- [Opsi avifenc Ubuntu 24.04](https://manpages.ubuntu.com/manpages/noble/man1/avifenc.1.html)
