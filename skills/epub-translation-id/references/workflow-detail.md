# Detail Alur Kerja Terjemahan EPUB

Dokumen ini memperluas `SKILL.md` dengan urutan kerja yang bisa diulang untuk EPUB lain.

## 1. Inventarisasi EPUB

```bash
EPUB="/path/ke/buku.epub"
WORK="/path/ke/kerja"
OUT="/path/ke/buku-ID.epub"

unzip -l "$EPUB"
unzip -p "$EPUB" OEBPS/content.opf | sed -n '1,120p'
```

Catat:
- `dc:title`, `dc:language`, `dc:identifier`;
- urutan `spine`;
- daftar `manifest` untuk XHTML dan gambar;
- apakah gambar berada di section tersendiri atau inline di chapter.

Buat daftar halaman:

| Section | Judul | Jumlah `<img>` | File gambar |
|---|---|---:|---|
| section-0005 | Bab 1 | 0 | — |
| section-0006 | Bab 2 | 1 | `INTERIORIMAGES_.jpg` |

Untuk setiap gambar inline, catat **indeks paragraf teks tempat gambar itu muncul**. Indeks dihitung dari paragraf teks, bukan dari elemen `<p>` kosong.

## 2. Ekstraksi

Jalankan:

```bash
# Sesuaikan dengan host:
# OpenCode:    SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code: SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex:       SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:  SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/epub-translation-id}"
python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
```

Yang dilakukan skrip:
- membaca setiap XHTML di spine, melewati cover/TOC/nav/copyright;
- mengambil judul dari `<title>`;
- mengubah setiap `<p>` atau heading `<h1>`–`<h6>` menjadi satu baris;
- menandai italic dengan `{i}...{/i}` dan bold dengan `{b}...{/b}`;
- mempertahankan `***`;
- mencatat gambar inline dan indeks paragrafnya ke `meta.json`;
- menghitung hash semua file gambar ke `image_manifest.json`.

Section seperti “About the Author” dan “Newsletter” **ikut diekstrak** dan harus diterjemahkan. Halaman yang hanya berisi gambar tidak muncul di `src/`; builder mempertahankannya.

Periksa hasil:

```bash
wc -l "$WORK"/src/section-*.txt
cd "$WORK"
python3 - <<'PY'
import json
m = json.load(open('meta.json'))
for s in m['sections']:
    print(s['id'], s['title'], 'paragraf=', s['paragraphs'],
          'gambar=', len(s['images']))
PY
```

Jika ada section yang hanya berisi gambar, tidak perlu diterjemahkan; builder akan mempertahankannya.

## 3. Penerjemahan

Buat file `id/section-XXXX.txt` untuk setiap section yang punya teks. Aturan:

- jumlah baris harus sama dengan `src/section-XXXX.txt`;
- baris pertama = judul chapter;
- satu baris = satu paragraf;
- jangan mengubah `***`;
- jangan menambahkan baris kosong di dalam file;
- pertahankan penanda `{i}` dan `{b}` jika ada.

Terjemahkan semua section yang punya teks, termasuk About the Author, Newsletter, afterword, dan halaman ekstra. Jangan hanya menerjemahkan chapter bernomor.

Untuk halaman promosi/watermark yang tidak punya section (mis. `jln.html`), buat `$WORK/auxiliary.json`:

```json
{"Download all your Fav Light Novels from": "Unduh semua novel ringan favoritmu dari"}
```

Sebelum menerjemahkan satu paragraf, baca minimal paragraf sebelumnya dan sesudahnya. Untuk dialog, tentukan:
- siapa penutur;
- siapa yang dirujuk “dia”;
- apakah kalimat itu perintah, larangan, pertanyaan retoris, atau penjelasan.

## 4. Membangun EPUB

```bash
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
```

Builder:
- menyalin isi EPUB asli ke `$WORK/build`;
- mempertahankan `<head>`, atribut `<body>`, dan wrapper `<div>` tunggal;
- mengganti XHTML section yang punya file terjemahan;
- menyisipkan gambar inline berdasarkan `meta.json`;
- memperbarui judul section, TOC, NCX, label halaman gambar, dan bahasa;
- menerapkan `auxiliary.json` pada halaman promosi/watermark;
- menormalkan semua `<img>`;
- membuat cover fallback;
- menulis ZIP EPUB.

Metadata opsional di `$WORK/metadata.json`:

```json
{"title": "Judul Buku (Edisi Indonesia)", "creator": "Nama Penulis", "identifier": "urn:uuid:..."}
```

Setelah build, periksa:

```bash
unzip -l "$OUT" | sed -n '1,20p'
unzip -t "$OUT"
```

## 5. Validasi

```bash
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
```

Skrip memeriksa:
- semua XHTML/XML valid;
- `mimetype` pertama dan tidak dikompresi;
- manifest dan spine;
- hash semua file gambar;
- jumlah dan posisi `<img>`;
- link internal;
- jumlah baris `src` vs `id`;
- sisa kata Inggris per paragraf, dengan nama file dan cuplikan;
- gambar yang masih memakai `height:100%`;
- laporan ditulis ke `validation.txt`.

Skrip keluar dengan kode `2` jika ada temuan. Temuan “possible untranslated English paragraphs” biasanya berarti halaman tambahan (About the Author, Newsletter, promo) belum diterjemahkan.

Validasi tambahan jika WeasyPrint tersedia:

```bash
cd "$WORK"
python3 - <<'PY'
from weasyprint import HTML
import glob, os
os.makedirs('render', exist_ok=True)
for f in sorted(glob.glob('build/OEBPS/Text/section-*.html')):
    HTML(filename=f).write_pdf('render/'+os.path.basename(f)+'.pdf')
PY
for f in render/*.pdf; do echo "$f"; pdfimages -list "$f" | tail -n +3 | wc -l; done
```

Gunakan `pdfimages` untuk memastikan gambar benar-benar tertanam dan muncul di halaman yang benar.

## 6. Audit semantik

Urutan yang terbukti efektif:

1. **Audit paragraf** — cari salah rujukan, negasi, idiom, informasi hilang.
2. **Audit kalimat** — pecah kalimat, periksa modalitas dan hubungan klausa.
3. **Audit independen** — bagi buku menjadi beberapa kelompok chapter, minta auditor berbeda.
4. **Terapkan temuan** — satu per satu, catat sebelum/sesudah.
5. **Bangun ulang dan validasi** — jangan lupa gambar.
6. **Ulangi** sampai tidak ada temuan makna yang pasti.

Contoh temuan yang harus dicari:

- Nama tokoh yang terpotong di dialog harus cocok dengan konteks adegan, bukan ditebak dari bunyi.
- “itu tidak apa-apa” bisa membalik negasi sumber “it was not fine”.
- Atribusi dialog harus sesuai penutur; jangan menukar “kataku” dan “katamu” tanpa bukti dari konteks.
- “getting the boot” bukan ditendang, tetapi diusir.
- “must have” bukan “mungkin”, tetapi “pasti”.
- “would I?” bukan “haruskah?”, tetapi “apakah aku akan melakukannya?”.
- “mid-thirties” bukan “tiga puluh tahun”, tetapi “pertengahan tiga puluhan”.

## 7. Ekstrak chapter TXT

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$WORK/chapters"
# tanpa meta.json:
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK/chapters"
# kecepatan TTS lain:
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$WORK/chapters" --wpm 150
# tanpa header durasi:
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$WORK/chapters" --no-duration
```

Jika `$WORK` diberikan, skrip hanya mengekstrak section yang punya `id/section-XXXX.txt`; section yang belum diterjemahkan tidak ikut menjadi TXT.

Periksa:
- jumlah file sesuai jumlah chapter;
- judul di baris pertama;
- perkiraan durasi TTS di baris kedua;
- paragraf dipisahkan baris kosong;
- `***` tetap ada;
- tidak ada file kosong;
- front/back matter tidak ikut menjadi file chapter;
- `daftar-isi.txt` memuat durasi per chapter dan total.

Durasi dihitung dari jumlah kata (termasuk judul) pada `--wpm`, default 140 kata/menit, dibulatkan ke detik. Default ini sengaja konservatif sebagai upper bound; 150–160 memberi estimasi lebih cepat. Ini estimasi; kecepatan TTS tiap mesin berbeda.

Penamaan: `Chapter N`/`Bab N` menjadi `bab-XX.txt`; `Interlude`/`Selingan` menjadi `selingan-XX.txt`; judul lain menjadi slug. Untuk buku dengan pola judul berbeda, sesuaikan `CHAPTER_RE`/`INTERLUDE_RE`.

## 8. Laporan akhir

Sertakan:
- path EPUB;
- path folder chapter;
- jumlah chapter dan kata;
- estimasi durasi TTS per chapter dan total;
- hasil `unzip -t`;
- jumlah gambar dan hash identik;
- jumlah `<img>`;
- validasi XML;
- jumlah isu penyelarasan paragraf;
- contoh perbaikan penting.

## 9. Uji asap pipeline

Sebelum menganggap skill siap dipakai pada buku baru, jalankan rantai ini pada satu buku yang sudah punya terjemahan:

```bash
python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$WORK/chapters"
unzip -t "$OUT" | tail -2
```

Tes sintetis bawaan repo:

```bash
python3 skills/epub-translation-id/tests/test_pipeline.py
# atau
make test
```

Kriteria lulus:
- `validate_epub.py` mencetak `issues: 0` dan keluar dengan kode 0;
- jumlah gambar final sama dengan sumber dan hash identik;
- jumlah `<img>` final sama dengan sumber;
- file chapter yang dihasilkan sama dengan hasil yang sudah diketahui (mis. `diff -rq`);
- `unzip -t` melaporkan `No errors detected`.
