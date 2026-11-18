# Petunjuk Penggunaan — epub-translation-id

Panduan ini ditujukan untuk manusia yang menjalankan skill secara manual atau mengawasi agent. Instruksi yang dibaca agent ada di [`skills/epub-translation-id/SKILL.md`](skills/epub-translation-id/SKILL.md).

Skill ini mengikuti standar terbuka **Agent Skills** dan bisa dipasang di OpenCode, Claude Code, Codex, Cursor, Gemini CLI, dan host lain yang mendukung `SKILL.md`.

## 1. Prasyarat

- Python 3.8 atau lebih baru.
- EPUB sumber yang Anda berhak terjemahkan.
- Salah satu host: OpenCode, Claude Code, Codex, Cursor, Gemini CLI, atau host Agent Skills lain.
- Node.js 18+ dengan `npx` untuk instalasi lintas host termudah.
- Opsional: skill `indonesia-eyd-writing-skill` untuk penyuntingan bahasa Indonesia.
- Opsional: WeasyPrint dan `pdfimages` untuk memeriksa hasil render.

Tidak ada dependensi Python eksternal; semua skrip memakai standard library. Perintah shell memakai `bash`; di Windows gunakan Git Bash/WSL atau jalankan skrip Python langsung.

## 2. Instalasi

**Copy baris ini ke chat AI agent** agar dia memasang skill ini sendiri:
> Pasang Agent Skill `epub-translation-id` dari https://github.com/murafdev/epub-translation-id dengan `npx skills add murafdev/epub-translation-id --skill epub-translation-id -g -a <agent> --copy -y` (ganti `<agent>` dengan `claude-code`, `opencode`, `codex`, `cursor`, atau `gemini-cli`), lalu pastikan skill muncul di daftar skill.

Cara yang disarankan adalah `npx skills`, yang tahu path skill tiap host:

```bash
# Lihat skill yang tersedia
npx skills add murafdev/epub-translation-id --list

# Install global untuk Claude Code
npx skills add murafdev/epub-translation-id \
  --skill epub-translation-id -g -a claude-code --copy -y
```

Ganti `-a` dengan salah satu:

```text
opencode | claude-code | codex | cursor | gemini-cli | '*'
```

Hilangkan `-g` untuk instalasi project scope. `--copy` disarankan di Termux/Android atau filesystem yang symlink-nya tidak andal.

Jika ingin installer lokal tanpa `npx`, gunakan skrip bawaan dari root repo:

```bash
./install.sh
# Jika filesystem tidak mengizinkan executable bit:
# bash install.sh

# Target eksplisit:
./install.sh --agent claude-code
./install.sh --agent all
./install.sh --agent opencode --scope project
./install.sh --dir "$HOME/.local/share/agent-skills"
```

Path user default:

| Host | Path |
|---|---|
| OpenCode | `~/.config/opencode/skills/epub-translation-id` |
| Claude Code | `~/.claude/skills/epub-translation-id` |
| Codex / universal | `~/.agents/skills/epub-translation-id` |
| Cursor | `~/.cursor/skills/epub-translation-id` |
| Gemini CLI | `~/.gemini/skills/epub-translation-id` |

Scope project memakai `.opencode/skills`, `.claude/skills`, `.agents/skills`, atau `.gemini/skills` di repo saat ini.

Instalasi manual (contoh Claude Code dan Codex/universal):

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/epub-translation-id "$HOME/.claude/skills/"

mkdir -p "$HOME/.agents/skills"
cp -R skills/epub-translation-id "$HOME/.agents/skills/"
```

Mulai sesi baru setelah instalasi agar skill terdeteksi. Untuk Codex/agent generik, `AGENTS.md` di root repo juga menunjuk ke skill ini; untuk Claude Code, lihat `CLAUDE.md`; untuk Gemini CLI, lihat `GEMINI.md`.

Uji cepat dari root repo:

```bash
python3 skills/epub-translation-id/tests/test_pipeline.py
# atau
make test
```

## 3. Siapkan workspace

Sesuaikan `SKILL_DIR` dengan host yang dipakai:

```bash
# OpenCode:
SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code:
# SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex / universal:
# SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:
# SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"

EPUB="/path/ke/buku.epub"
WORK="/path/ke/kerja"
OUT="/path/ke/buku-ID.epub"
CHAPTERS="/path/ke/chapters"

mkdir -p "$WORK"
```

Struktur yang akan terbentuk:

```text
$WORK/
  src/                  # paragraf sumber, satu baris per paragraf
  id/                   # terjemahan, selaras baris dengan src
  build/                # EPUB yang sedang dibangun
  meta.json
  image_manifest.json
  validation.txt
```

## 4. Audit awal EPUB

```bash
unzip -l "$EPUB"
unzip -p "$EPUB" OEBPS/content.opf | sed -n '1,140p'
```

Catat:

- jumlah section XHTML dan urutan spine;
- semua file gambar dan ukurannya;
- halaman gambar penuh (color insert, front matter, character design);
- gambar inline di dalam chapter;
- cover, terutama yang memakai `<svg><image xlink:href=...>`;
- chapter yang hanya berisi gambar.

Jangan hanya mengandalkan manifest. Periksa isi XHTML untuk memastikan gambar inline dan posisinya.

## 5. Ekstrak section

```bash
python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
```

Hasil:

- `$WORK/src/section-XXXX.txt` — judul di baris pertama, satu paragraf per baris;
- penanda `{i}...{/i}` untuk italic dan `{b}...{/b}` untuk bold;
- `***` untuk scene break;
- `meta.json` — jumlah paragraf dan indeks gambar inline;
- `image_manifest.json` — hash SHA-256 semua gambar.

Periksa:

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

Section yang hanya berisi gambar tidak muncul di `src/`; builder mempertahankannya.

## 6. Terjemahkan

Buat `$WORK/id/section-XXXX.txt` untuk setiap section yang punya teks. Aturan:

- jumlah baris harus sama persis dengan `src/section-XXXX.txt`;
- baris pertama adalah judul chapter terjemahan;
- satu baris = satu paragraf;
- jangan menambah baris kosong di dalam file;
- pertahankan `***`, `{i}...{/i}`, dan `{b}...{/b}`;
- jangan menerjemahkan nama/tempat/istilah yang sudah ditetapkan tanpa alasan.

Contoh:

```text
Bab 1: Rencana Masa Depan dan Kekhawatiran Cliff
Satu bulan telah berlalu sejak peristiwa di Kerajaan Shirone.
“Kau yakin?” tanyaku.
***
Malam itu, kami berangkat.
```

Terjemahkan **semua** section berteks, termasuk About the Author, Newsletter, afterword, dan halaman tambahan. Halaman promosi yang tidak punya section (mis. `jln.html`) ditangani lewat `auxiliary.json`:

```json
{"Download all your Fav Light Novels from": "Unduh semua novel ringan favoritmu dari"}
```

Sebelum menerjemahkan paragraf, baca minimal paragraf sebelum dan sesudahnya. Untuk dialog, pastikan:

- siapa penutur;
- siapa yang dirujuk “dia”;
- apakah kalimat itu perintah, larangan, pertanyaan retoris, atau ejekan;
- modalitas (harus/mungkin/pasti) dan negasi tidak berubah.

## 7. Bangun EPUB

```bash
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
```

Builder:

- menyalin seluruh isi EPUB asli, termasuk semua gambar;
- mempertahankan `<head>` dan atribut `<body>` asli;
- mengganti isi section yang punya terjemahan;
- menyisipkan gambar inline sesuai `meta.json`;
- menerjemahkan judul, TOC, NCX, dan label halaman umum;
- menormalkan gambar menjadi responsif;
- memberi page break di sekitar ilustrasi chapter;
- mengganti cover SVG dengan `<img>` fallback;
- menulis `mimetype` sebagai entri pertama dan tanpa kompresi.

Metadata opsional di `$WORK/metadata.json`:

```json
{"title": "Judul Buku (Edisi Indonesia)", "creator": "Nama Penulis", "identifier": "urn:uuid:..."}
```

## 8. Validasi

```bash
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
unzip -t "$OUT"
```

Validator memeriksa:

- ZIP dan `mimetype`;
- semua XHTML/XML/OPF/NCX dapat diparse;
- manifest dan spine;
- hash SHA-256 semua gambar;
- jumlah dan posisi `<img>`;
- link internal;
- jumlah baris `src` vs `id`;
- sisa paragraf berbahasa Inggris;
- gambar yang masih memakai `height:100%`.

Validator keluar dengan kode `2` jika ada issue. Baca `$WORK/validation.txt` dan perbaiki sebelum lanjut.

Jika tersedia, render untuk pemeriksaan visual:

```bash
cd "$WORK"
python3 - <<'PY'
from weasyprint import HTML
import glob, os
os.makedirs('render', exist_ok=True)
for f in sorted(glob.glob('build/OEBPS/Text/section-*.html')):
    HTML(filename=f).write_pdf('render/' + os.path.basename(f) + '.pdf')
PY
for f in render/*.pdf; do echo "$f"; pdfimages -list "$f" | tail -n +3 | wc -l; done
```

## 9. Audit semantik berulang

Lakukan minimal tiga jenis audit:

1. **Audit paragraf** — subjek/objek, pronomina, negasi, modalitas, sebab-akibat, idiom, informasi hilang.
2. **Audit kalimat** — pecah kalimat, bandingkan klausa, pastikan pertanyaan/perintah/ejekan tetap sama.
3. **Audit independen** — bagi buku menjadi beberapa kelompok chapter; minta auditor berbeda hanya melaporkan kesalahan makna yang pasti.

Terapkan temuan, bangun ulang, validasi ulang, lalu audit lagi. Berhenti setelah putaran terakhir tidak menemukan kesalahan makna yang pasti.

Catat setiap perbaikan di `translation-revision-notes.md`:

```markdown
## Bab 3, paragraf 42
- Sebelum: “itu tidak apa-apa”
- Sesudah: “itu tidak baik-baik saja”
- Alasan: sumber “it was not fine”; negasi tidak boleh dibalik.
```

## 10. Ekstrak chapter TXT

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS"
```

Tanpa `meta.json`:

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$CHAPTERS"
```

Ubah kecepatan TTS atau hilangkan durasi dari daftar isi:

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS" --wpm 150
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS" --no-duration
```

Hasil:

- `bab-01.txt`, `bab-02.txt`, dst.;
- `selingan-01.txt` untuk interlude;
- judul di baris pertama;
- TXT chapter hanya berisi judul dan paragraf, tanpa header durasi;
- paragraf dipisahkan baris kosong;
- `***` dipertahankan;
- `daftar-isi.txt` berisi nama file, jumlah kata, durasi per chapter, judul, dan total durasi.

Durasi dihitung dari jumlah kata (termasuk judul) pada `--wpm`, default 140 kata/menit. Default ini sengaja konservatif sebagai upper bound; gunakan 150–160 untuk estimasi yang lebih cepat. Ini estimasi, bukan durasi pasti.

Front/back matter seperti TOC, copyright, About the Author, Newsletter, dan cover dilewati.

## 11. Laporan akhir

Sertakan bukti:

- path EPUB final dan folder chapter;
- jumlah chapter, kata, dan file TXT;
- estimasi durasi TTS per chapter dan total;
- hasil `unzip -t`;
- jumlah gambar, jumlah `<img>`, dan status hash identik;
- hasil validasi XML/OPF/NCX;
- jumlah issue posisi gambar dan paragraf;
- ringkasan `translation-revision-notes.md`;
- sampel teks awal/tengah/akhir.

## 12. Troubleshooting

| Gejala | Penyebab umum | Tindakan |
|---|---|---|
| `img count 0, expected 1` | Section tidak dibangun ulang atau id file hilang | Pastikan `id/section-XXXX.txt` ada dan jumlah baris benar |
| `img positions [1], expected [0]` | Urutan gambar 0 diubah | Builder versi ini menaruh gambar indeks 0 sebelum heading; jangan ubah urutan manual |
| `possible untranslated English paragraphs` | Halaman tambahan/promo belum diterjemahkan | Terjemahkan section atau tambahkan `auxiliary.json` |
| `mimetype is compressed` | EPUB dibangun dengan alat lain | Builder ini selalu menulis mimetype tanpa kompresi; rebuild |
| `broken link` | Path gambar/CSS berubah | Jangan mengubah `src`/`href`; builder hanya mengganti text node |
| `src X lines, id Y lines` | Paragraf digabung/dipecah | Kembalikan satu baris = satu paragraf |
| Cover tidak tampil | Reader tidak mendukung SVG | Pastikan cover fallback `<img>` ada |
| Gambar tidak tampil | `height:100%` tanpa lebar | Builder menormalkan; cek validator |
| TOC masih Inggris | Label tidak ada di `common_labels` | Tambahkan label atau `auxiliary.json` |

## 13. Adaptasi untuk EPUB lain

- Label front/back matter berbeda: ubah `common_labels` dan `title_labels` di `skills/epub-translation-id/scripts/build_epub.py`.
- Frasa promosi berbeda: tambahkan ke `auxiliary.json`.
- Markup chapter memakai `<div>` atau selector lain: sesuaikan regex blok di `extract_sections.py` dan `extract_chapters.py`.
- Nama file chapter tidak memakai angka: ID akan memakai `x0001`, `x0002`, dst.; ini normal.
- CSS atau struktur folder berbeda: builder mempertahankan `<head>` asli, jadi path CSS tetap aman.
- Chapter memakai judul “Prologue”, “Epilogue”, atau “Afterword”: sesuaikan `CHAPTER_RE`/`INTERLUDE_RE` atau biarkan menjadi slug.

## 14. Etika dan hak cipta

Gunakan skill ini hanya untuk karya yang Anda punya hak terjemahnya. Jangan commit EPUB sumber, teks terjemahan, atau cover art ke repo publik tanpa izin. Repo ini hanya berisi skrip dan dokumentasi.

## 15. Checklist akhir

- [ ] Semua section berteks punya `id/section-XXXX.txt`.
- [ ] Jumlah baris `src` = `id`.
- [ ] `validate_epub.py` mencetak `issues: 0`.
- [ ] Semua gambar identik dan jumlah `<img>` sesuai.
- [ ] Tidak ada gambar yang masih memakai `height:100%`.
- [ ] TOC/NCX sudah diterjemahkan.
- [ ] About the Author, Newsletter, afterword, dan promo sudah diterjemahkan.
- [ ] `unzip -t` tidak melaporkan error.
- [ ] Chapter TXT bisa dibuka dan lengkap.
- [ ] `translation-revision-notes.md` terisi.
