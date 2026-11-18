---
name: epub-translation-id
description: Menerjemahkan EPUB (novel/light novel) ke bahasa Indonesia sambil mempertahankan seluruh gambar, struktur paragraf, dan format EPUB; melakukan audit konteks paragraf dan kalimat secara berulang, membangun EPUB final, memvalidasi gambar/XML, serta mengekstrak chapter ke TXT. Gunakan saat pengguna memberikan file EPUB dan meminta terjemahan Indonesia, perbaikan terjemahan, hasil EPUB, atau file per chapter.
license: MIT
compatibility: Python 3.8+; bash for the installer; optional WeasyPrint/pdfimages for render checks.
---

# Terjemahan EPUB ke Bahasa Indonesia

## Kompatibilitas

Skill ini mengikuti **Agent Skills open standard** dan dapat dipakai di OpenCode, Claude Code, Codex, Cursor, Gemini CLI, serta host lain yang mendukung `SKILL.md`.

Instalasi: lihat bagian Install di README repo.

Script Python hanya memakai standard library dan tidak bergantung pada satu host. Perintah shell memakai `bash`; di Windows gunakan Git Bash/WSL atau jalankan skrip Python langsung.

## Tujuan

Hasilkan EPUB berbahasa Indonesia yang:
- menerjemahkan seluruh teks cerita, bukan ringkasan;
- mempertahankan **semua gambar asli** dan posisinya di dalam teks;
- menjaga struktur paragraf, judul chapter, scene break, dan urutan cerita;
- mengikuti konteks adegan, bukan terjemahan kata per kata;
- menggunakan EYD V dan istilah yang konsisten;
- lolos validasi EPUB, XML, gambar, dan pengecekan paragraf.

Gunakan skill `indonesia-eyd-writing-skill` untuk keputusan ejaan, tanda baca, dan penyuntingan bahasa Indonesia.

## Dependensi

- Python 3.8+ dengan standard library (tanpa paket eksternal).
- `indonesia-eyd-writing-skill` opsional untuk penyuntingan bahasa Indonesia.
- WeasyPrint + `pdfimages` opsional untuk pemeriksaan render visual.

## Prinsip yang tidak boleh dilanggar

1. **Jangan menghapus gambar.** Saat membangun ulang HTML chapter, `<img>` yang berada di antara paragraf wajib dimasukkan kembali pada indeks paragraf yang sama. Mempertahankan file gambar di folder `Images/` saja tidak cukup.
2. **Jaga keselarasan paragraf.** Satu baris terjemahan = satu paragraf sumber. Jumlah paragraf setiap section harus sama dengan sumber. Ini menjaga posisi gambar, scene break, dan urutan adegan.
3. **Baca konteks sebelum menerjemahkan.** Baca paragraf sebelum dan sesudahnya. Selesaikan pronomina, referensi, idiom, dan maksud kalimat dari konteks cerita.
4. **Jangan menerjemahkan istilah yang sudah mapan secara sembarangan.** Pertahankan nama tokoh, tempat, gelar, dan istilah khusus dunia buku secara konsisten. Buat daftar istilah tetap untuk buku tersebut (mis. istilah sihir, nama guild, gelar keagamaan, atau nama tempat) dan jangan memaksakan istilah dari buku lain.
5. **Pertahankan fakta.** Jangan mengubah angka, negasi, pelaku, sebab-akibat, tingkat kepastian (mungkin/harus/pasti), atau urutan kejadian.
6. **Loop audit.** Setelah menerjemahkan, lakukan beberapa putaran: audit paragraf, audit kalimat, perbaikan, bangun ulang, lalu audit lagi sampai tidak ada temuan yang pasti.
7. **Verifikasi dengan bukti.** Tunjukkan hasil `unzip -t`, hitungan gambar, hash gambar, validasi XML, dan sampel teks. Jangan hanya mengklaim sudah selesai.

## Alur kerja

### 0. Audit awal EPUB

```bash
unzip -l "$EPUB"
```

Periksa:
- jumlah section XHTML dan urutannya di `content.opf`;
- semua file gambar dan ukurannya;
- gambar yang menjadi halaman tersendiri (color insert, front matter, character design);
- gambar yang berada **di dalam chapter** (inline illustration);
- gambar cover (kadang memakai `<svg><image xlink:href=...>`);
- apakah ada chapter tanpa teks (halaman gambar saja).

Buat audit halaman-per-halaman: setiap section, jumlah `<img>`, path gambar, dan posisi relatif terhadap paragraf. Jangan mengandalkan daftar manifest saja.

### 1. Siapkan workspace

```bash
# Saat skill dijalankan dari folder skill ini:
SKILL_DIR="$(pwd)"
# OpenCode:
# SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code:
# SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex / universal:
# SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:
# SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"

mkdir -p "$WORK"/{src,id,build}
python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
```

Script menghasilkan:
- `src/section-XXXX.txt` — judul + satu paragraf per baris, dengan penanda `{i}...{/i}` untuk italic, `{b}...{/b}` untuk bold, dan `***` untuk scene break;
- `meta.json` — judul, jumlah paragraf teks, daftar gambar beserta indeks paragraf;
- `image_manifest.json` — path dan hash gambar.

Periksa bahwa jumlah baris `src` setiap section sama dengan jumlah paragraf teks di EPUB.

### 2. Terjemahkan paragraf per paragraf

- Buat `id/section-XXXX.txt` dengan jumlah baris yang sama persis.
- Baris pertama adalah judul chapter terjemahan.
- Satu baris = satu paragraf; jangan menggabung atau memecah paragraf.
- Pertahankan `***`, penanda italic `{i}...{/i}`, dan bold `{b}...{/b}`.
- Terjemahkan **semua** section yang diekstrak, bukan hanya chapter utama. Ini termasuk “About the Author”, “Newsletter”, afterword, dan halaman teks tambahan lain. Jika halaman promosi tidak diekstrak (mis. `jln.html`), terjemahkan frasanya lewat `auxiliary.json` (lihat langkah 3).
- Terjemahkan dialog dengan tanda kutip Indonesia: “...” dan atribusi `,” kata X.`
- Baca konteks: siapa berbicara, siapa dirujuk “dia”, apa maksud idiom, apa yang baru terjadi.
- Jangan menerjemahkan langsung frasa seperti:
  - “getting the boot” → diusir, bukan ditendang;
  - “settle the score” → menyelesaikan perhitungan lama;
  - “if anything” → malah/sebaliknya, bukan “kalau ada”;
  - “must have” → pasti, bukan “mungkin”;
  - “you do!” → “kau memang …!”;
  - “kiss ass” → mencari muka, bukan menjilat;
  - “talked myself up” → membanggakan diri, bukan menyemangati diri.

Gunakan contoh terjemahan pengguna jika ada sebagai acuan suara dan istilah, tetapi tetap periksa konteksnya.

### 3. Bangun EPUB

```bash
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT_EPUB"
```

Builder harus:
- menyalin semua file asli, termasuk seluruh `Images/`;
- mempertahankan `<head>`, atribut `<body>`, dan wrapper `<div>` tunggal agar CSS/path tetap aman;
- mengganti hanya section yang punya terjemahan;
- menyisipkan kembali gambar inline pada indeks paragraf yang tercatat;
- mempertahankan `id` gambar dan path relatifnya;
- menormalkan gambar agar tampil: `width:100%; max-width:100%; height:auto; display:block; margin:0 auto;` (kecuali logo kecil);
- memberi page break sebelum/sesudah ilustrasi penuh halaman chapter;
- mengganti cover SVG dengan `<img>` sebagai fallback;
- memperbarui `<title>`, TOC, NCX, dan `dc:language` menjadi `id`;
- memperbarui `dc:title`/`dc:creator`/`dc:identifier` jika `metadata.json` disediakan;
- menulis `mimetype` sebagai entri pertama dan tanpa kompresi.

Dua file opsional di `$WORK`:

`auxiliary.json` — frasa di halaman promosi/watermark yang tidak punya section:
```json
{"Download all your Fav Light Novels from": "Unduh semua novel ringan favoritmu dari"}
```

`metadata.json` — metadata buku final:
```json
{"title": "Judul Buku (Edisi Indonesia)", "creator": "Nama Penulis", "identifier": "urn:uuid:..."}
```

Builder sudah punya padanan bawaan untuk label umum (`Table of Contents`, `About the Author:`, `Newsletter`, `Color Inserts`, dst.) dan watermark “Download all your Fav Light Novels from…”. Untuk buku lain, tambahkan label yang berbeda ke `common_labels` di script atau ke `auxiliary.json`.

Jika struktur EPUB berbeda, sesuaikan selector/class tetapi jangan mengubah prinsip: **semua gambar dan posisinya harus dipertahankan**.

### 4. Validasi wajib

```bash
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT_EPUB" "$WORK"
unzip -t "$OUT_EPUB"
```

Yang harus diperiksa:
- semua XHTML/XML/OPF/NCX dapat diparse;
- jumlah entri dan manifest/spine konsisten;
- semua gambar ada dan **hash SHA-256 identik** dengan EPUB asli;
- jumlah `<img>` di XHTML sama dengan sumber;
- setiap section dengan gambar punya gambar pada posisi paragraf yang benar (dihitung dengan parser HTML);
- tidak ada link internal yang rusak;
- tidak ada sisa kata fungsi Inggris yang tidak disengaja (validator mencetak file dan cuplikan paragraf yang mencurigakan);
- jumlah baris `src` = `id` = jumlah paragraf di `meta.json`;
- tidak ada perbedaan angka, tanda tanya, tanda seru, atau tanda kutip pembuka yang menunjukkan paragraf bergeser.

Validator keluar dengan kode `2` jika ada masalah. Jangan mengabaikan temuan “possible untranslated English paragraphs”; periksa apakah itu halaman tambahan yang belum diterjemahkan, lalu terjemahkan atau tambahkan padanannya.

Jika tersedia, render setiap section dengan WeasyPrint dan periksa `pdfimages -list` untuk memastikan gambar benar-benar muncul.

### 5. Audit semantik berulang

Lakukan minimal tiga jenis audit, lalu ulangi setelah perbaikan:

**A. Audit paragraf**
- Bandingkan makna setiap paragraf dengan sumber.
- Cari salah rujukan pronomina, negasi terbalik, sebab-akibat salah, idiom salah, informasi hilang/bertambah.

**B. Audit kalimat**
- Pecah paragraf menjadi kalimat.
- Periksa subjek/objek, modalitas (harus/mungkin/pasti), jumlah, dan hubungan antarkalimat.
- Periksa apakah kalimat terjemahan menyampaikan maksud yang sama, bukan hanya kata yang mirip.

**C. Audit independen**
- Minta auditor terpisah untuk kelompok chapter berbeda (mis. Bab 1–2, 3–4, dst.).
- Minta mereka hanya melaporkan kesalahan makna yang pasti, bukan preferensi gaya.
- Terapkan temuan, bangun ulang, lalu minta audit ulang atau jalankan audit otomatis lagi.

Berhenti hanya setelah putaran terakhir tidak menemukan kesalahan makna yang pasti.

Catat setiap temuan dan perbaikan di `translation-revision-notes.md`: lokasi, teks sebelum, teks sesudah, dan alasan konteks. Ini bukti audit, bukan sekadar klaim.

### 6. Ekstrak chapter ke TXT

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT_EPUB" "$WORK" "$CHAPTERS_DIR"
# atau tanpa meta.json:
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT_EPUB" "$CHAPTERS_DIR"
# ubah kecepatan TTS (default 140 kata/menit):
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT_EPUB" "$WORK" "$CHAPTERS_DIR" --wpm 150
# tanpa kolom durasi di daftar-isi:
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT_EPUB" "$WORK" "$CHAPTERS_DIR" --no-duration
```

Hasil:
- satu file TXT per chapter (`bab-01.txt`, dst.; selingan menjadi `selingan-01.txt`);
- halaman front/back matter (TOC, copyright, About the Author, Newsletter, cover) dilewati;
- judul di baris pertama;
- TXT chapter hanya berisi judul dan paragraf, tanpa header durasi;
- paragraf dipisahkan baris kosong;
- scene break `***` dipertahankan;
- `daftar-isi.txt` berisi nama file, jumlah kata, perkiraan durasi TTS, judul, dan total durasi.

Durasi dihitung dari jumlah kata (termasuk judul) pada kecepatan `--wpm`, dibulatkan ke detik. Default 140 kata/menit adalah estimasi konservatif (upper bound), berguna untuk merencanakan kuota TTS; gunakan 150–160 untuk estimasi yang lebih cepat. Ini estimasi, bukan durasi pasti.

Jika penamaan chapter buku lain berbeda, sesuaikan `CHAPTER_RE` dan `INTERLUDE_RE` di script; judul yang tidak cocok akan menjadi nama file slug.

### 7. Laporan akhir

Sertakan bukti, bukan hanya klaim:
- path EPUB final dan folder `chapters/`;
- jumlah chapter, kata, dan file TXT;
- estimasi durasi TTS per chapter dan total;
- hasil `unzip -t`;
- jumlah gambar, jumlah `<img>`, dan status hash identik;
- hasil validasi XML/OPF/NCX;
- jumlah isu penyelarasan paragraf;
- ringkasan `translation-revision-notes.md` dengan contoh sebelum → sesudah;
- sampel teks dari awal/tengah/akhir buku.

## Format keluaran yang disarankan

```
$WORK/
  src/                  # paragraf sumber, satu baris per paragraf
  id/                   # terjemahan, selaras baris dengan src
  build/                # EPUB yang sedang dibangun
  meta.json
  image_manifest.json
  auxiliary.json        # opsional: padanan frasa halaman promosi
  metadata.json         # opsional: judul/penulis/identifier final
$OUT_EPUB               # EPUB final
chapters/               # TXT per chapter (bersih) + daftar-isi.txt berdurasi
validation.txt
image-audit.txt
translation-revision-notes.md
```

## Checklist gambar (khusus)

- [ ] Semua file gambar asli ada di EPUB final.
- [ ] Hash setiap gambar sama dengan asli.
- [ ] Jumlah `<img>` di XHTML sama dengan sumber.
- [ ] Gambar inline ada di antara paragraf yang benar, bukan hanya di folder.
- [ ] Cover tampil (bukan hanya SVG yang tidak didukung reader).
- [ ] Color insert, front matter, character design, dan logo ada.
- [ ] Tidak ada gambar yang terpotong/tersembunyi karena `height:100%` tanpa lebar.

## Checklist bahasa

- [ ] EYD V: ejaan, tanda baca, huruf kapital, kata depan, partikel.
- [ ] Dialog memakai tanda kutip dan koma yang tepat.
- [ ] Istilah konsisten di seluruh buku.
- [ ] Nama tokoh/tempat tidak berubah-ubah.
- [ ] Tidak ada terjemahan literal yang mengubah maksud.
- [ ] Tidak ada kalimat yang hanya enak dibaca tetapi bertentangan dengan sumber.
- [ ] About the Author, Newsletter, afterword, dan halaman teks tambahan sudah diterjemahkan.
- [ ] Label TOC/NCX dan halaman gambar (Color Inserts, Title Page, dst.) sudah diterjemahkan.
- [ ] Halaman promosi/watermark tidak menyisakan kalimat Inggris (lihat `auxiliary.json`).

## Jebakan yang sudah terbukti

1. **Gambar hilang saat regenerasi HTML.** Builder yang hanya menyalin paragraf akan membuang `<img>`. Selalu simpan peta `indeks paragraf → tag gambar` dan sisipkan kembali.
2. **`height="100%"` membuat gambar tidak tampil** di sebagian reader. Gunakan lebar responsif dan `height:auto`.
3. **Cover SVG tidak tampil** di reader EPUB2 tertentu. Sediakan fallback `<img>`.
4. **Paragraf bergeser** membuat gambar dan scene break salah tempat. Jangan mengubah jumlah baris.
5. **Terjemahan harfiah idiom** sering membalik makna. Baca konteks dan cari padanan Indonesia.
6. **“If anything”, “must have”, “would I”, “getting the boot”, “settle the score”** adalah jebakan umum. Periksa modalitas dan idiom.
7. **Nama/pronoun** bisa berubah rujukan. Jika sumber menyebut “he” untuk kakek, jangan menjadi “dia” yang ambigu.
8. **Halaman tambahan sering terlupa.** About the Author, Newsletter, afterword, dan halaman promosi tetap harus diterjemahkan; validator akan menandainya sebagai paragraf Inggris.
9. **Watermark bukan chapter.** Baris seperti “Download all your Fav Light Novels from Just Light Novels” tidak punya section sendiri. Tangani lewat `auxiliary.json` atau padanan bawaan builder.
10. **Jangan mengklaim selesai tanpa bukti.** Tunjukkan hasil validasi dan sampel teks.

## Etika dan hak cipta

Terjemahkan hanya karya yang Anda punya haknya. Jangan menyebarkan EPUB sumber, teks terjemahan, atau cover art tanpa izin. Skill ini tidak melakukan bypass DRM.
