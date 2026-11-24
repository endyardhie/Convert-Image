# Pengajuan dan penggunaan SignPath Foundation

[Kembali ke README](../README.md) · [Code signing policy](../CODE_SIGNING.md)

## Status

Persiapan repositori dan workflow tersedia. Pengajuan belum berarti diterima;
rilis Windows yang sudah ada tetap belum ditandatangani. SignPath Foundation
meninjau kelayakan, reputasi dan pengendalian proyek sebelum memberi akses.

Pemilik proyek melaporkan pada **25 November 2026** bahwa pengujian langsung
di Windows berjalan normal. Pemeriksaan otomatis sebelumnya meliputi konversi,
batch Unicode, menu native, dialog pembatalan, instalasi, update dan uninstall.

## Mengajukan proyek

Buka [formulir resmi](https://signpath.org/apply) dengan data berikut:

| Kolom | Isi |
| --- | --- |
| Project Name | Convert Image |
| Repository URL | https://github.com/endyardhie/Convert-Image |
| Homepage URL | https://github.com/endyardhie/Convert-Image#readme |
| Download URL | https://github.com/endyardhie/Convert-Image/releases |
| Privacy Policy URL | https://github.com/endyardhie/Convert-Image/blob/main/CODE_SIGNING.md#privacy-policy |
| Category | Graphics |
| Maintainer Type | Individual maintainer(s) |
| Build System | GitHub Actions |
| First / Last Name | Endy / Ardhie |
| Discovery Channel | AI / LLM tools; ChatGPT / OpenAI Codex |

Gunakan alamat email yang ingin dipakai untuk akun dan pemberitahuan SignPath.
Alamat kontak pribadi tidak perlu ditambahkan ke repositori publik.

**Tagline**

> Convert images directly from the right-click menu on Windows and Linux.

**Description**

Convert Image is a free, MIT-licensed desktop utility that makes local image
conversion accessible from Windows File Explorer and the Nemo file manager on
Linux. Users can convert one or multiple still images between common image
formats or save them as individual PDF documents, with straightforward quality
choices. Original files are preserved, and images are processed locally without
uploading them to an online service.

**Reputation**

This is a recently released, individually maintained project. We do not yet have
broad adoption or independent media coverage to claim. Public source, license,
build scripts, test results and release artifacts are available for inspection:

- [MIT license](https://github.com/endyardhie/Convert-Image/blob/main/LICENSE)
- [Public releases](https://github.com/endyardhie/Convert-Image/releases)
- [GitHub-hosted CI](https://github.com/endyardhie/Convert-Image/actions)
- [Successful Linux/Windows build and package tests](https://github.com/endyardhie/Convert-Image/actions/runs/45438857600)
- [Signing and privacy policy](https://github.com/endyardhie/Convert-Image/blob/main/CODE_SIGNING.md)

The first Windows preview has been manually tested by the project owner, who
reported that it works normally. Automated checks include 75 conversion
combinations, plus packaged-app batch conversion, the native shell menu and
install/update/uninstall tests. We understand that acceptance remains subject
to the Foundation's assessment of project reputation and controls.

Sebelum mengirim, pemilik akun perlu membaca dan menyetujui Code of Conduct serta
persetujuan pemrosesan data pada formulir. Persetujuan pemasaran bersifat opsional.
Aktifkan MFA pada GitHub dan akun signing sesuai persyaratan Foundation.

## Setelah pengajuan diterima

1. Ikuti instruksi onboarding dari SignPath. Jika perlu memasang GitHub App,
   tinjau izinnya dan pilih hanya repo `endyardhie/Convert-Image`.
2. Pastikan project terhubung ke Trusted Build System **GitHub.com** dan gunakan
   sertifikat Foundation, bukan sertifikat uji, untuk unduhan publik.
3. Buat dua artifact configurations dari
   [`application.xml`](../signpath/application.xml) dan
   [`installer.xml`](../signpath/installer.xml). Tinjau konfigurasinya bersama
   SignPath; XML di repo merupakan persiapan yang belum divalidasi oleh layanan.
4. Tetapkan Endy Ardhie sebagai approver dan gunakan kebijakan yang mewajibkan
   persetujuan manual untuk setiap permintaan produksi.
5. Simpan API token submitter pada GitHub repository secret `SIGNPATH_API_TOKEN`.
   Jangan menempelkan token di issue, README atau chat. Gunakan hak minimum untuk
   project/policy ini.
6. Isi repository variables di bawah sesuai nilai akun yang diberikan SignPath.
   Set `SIGNPATH_ENABLED=true` paling akhir, setelah seluruh konfigurasi siap.

| Repository variable | Nilai |
| --- | --- |
| `SIGNPATH_ORGANIZATION_ID` | Organization ID dari SignPath |
| `SIGNPATH_PROJECT_SLUG` | Slug project yang sebenarnya |
| `SIGNPATH_POLICY_SLUG` | Slug kebijakan produksi dengan persetujuan manual |
| `SIGNPATH_APPLICATION_CONFIG` | Slug konfigurasi untuk aplikasi dan DLL |
| `SIGNPATH_INSTALLER_CONFIG` | Slug konfigurasi installer |
| `SIGNPATH_ENABLED` | `true` setelah onboarding selesai |

## Menjalankan penandatanganan

Buka **Actions → Sign Windows release → Run workflow**, pilih branch **main**.
Workflow tidak berjalan otomatis pada push atau pull request.

Alurnya adalah build dan tes → unggah aplikasi untuk verifikasi asal → persetujuan
signing aplikasi/DLL → verifikasi tanda tangan → buat dan tes installer → persetujuan
signing installer → verifikasi dan tes ulang. Kedua permintaan membutuhkan
persetujuan di SignPath, dengan waktu tunggu 30 menit per permintaan.

Setelah berhasil, artifact **Convert-Image-Windows-signed** berisi installer,
checksum baru, dan laporan `signatures.json`. Tinjau hasil sebelum mengunggahnya
ke GitHub Releases. Workflow ini tidak menerbitkan rilis otomatis. Perbarui
status publik dan acknowledgement setelah penandatanganan benar-benar tersedia.

File milik pihak ketiga dan uninstaller Inno Setup belum termasuk cakupan awal.
Jangan menyatakan bahwa semua komponen paket sudah ditandatangani. Status
**pratinjau/stabil** dan **bertanda tangan/belum** tetap merupakan hal terpisah.
Tanda tangan tepercaya membantu identitas penerbit; SmartScreen tetap dapat
menampilkan peringatan untuk aplikasi dengan reputasi yang belum terbentuk.

Referensi: [ketentuan Foundation](https://signpath.org/terms),
[integrasi GitHub resmi](https://docs.signpath.io/trusted-build-systems/github),
[konfigurasi artifact](https://docs.signpath.io/artifact-configuration/examples).
