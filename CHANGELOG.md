# Changelog

## 2.1.0

- Tambah submenu Pdf dengan High Quality, Standard, dan Small Size.
- Satu gambar per PDF satu halaman; kompresi JPEG 95/85/70, resize proporsional dan latar putih untuk alpha.
- Verifikasi struktur PDF dan gambar sebelum publikasi; mendukung CLI `--format pdf`.
- Tambah dependensi ReportLab/pypdf, konfigurasi `pdf_*`, tes PDF, serta dokumentasi.

## 2.0.0

- Nama proyek/repo menjadi Nemo Convert Image / Nemo-Convert-Image.
- Menu bertingkat Convert Image → Avif/Jpg → High Quality/Standard/Small Size.
- Tambah JPG kualitas 95/85/70, optimized progressive JPEG, dan latar putih untuk alpha.
- Izinkan input JPG/JPEG diproses ulang ke JPG dengan output baru tanpa overwrite.
- Tambah CLI `convert-image --format avif|jpg`, installer `install-image.sh`, dan konfigurasi `jpg_*`.
- Pertahankan installer, CLI, lokasi konfigurasi/cache, dan nama ekstensi lama untuk update kompatibel.
- Tambah pengujian JPG dan struktur menu; perbarui installer yang dihasilkan.

## 1.0.0 — 2026-11-18

- Menu Nemo Convert Img2Avif dengan High Quality, Standard, dan Small Size.
- AVIF lossless 8-bit dengan verifikasi piksel; preset resize 1920/1280 px.
- Batch, pembatalan, transparansi, profil ICC, dan penamaan tanpa menimpa file.
- Installer satu file yang dihasilkan dari source terpisah.
- Dependensi Linux Mint memakai paket `python-nemo` yang benar.
- Backup, penulisan atomik, rollback, pemeriksaan dependensi, launcher CLI, dan uninstall.
- Dokumentasi bahasa Indonesia serta tes unit dan integrasi codec opsional.
