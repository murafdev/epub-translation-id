# Petunjuk Penggunaan — epub-translation-id

Panduan untuk manusia. Instruksi yang dibaca agent ada di [`skills/epub-translation-id/SKILL.md`](skills/epub-translation-id/SKILL.md).

## Instalasi

Lihat [`INSTALL.md`](INSTALL.md).

## Prasyarat

- Python 3.8+
- Node.js 18+ dengan `npx` untuk instalasi
- EPUB sumber yang Anda berhak terjemahkan
- Opsional: `indonesia-eyd-writing-skill`, WeasyPrint, dan `pdfimages`

## Workspace

```bash
# Sesuaikan dengan host:
# OpenCode:    SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code: SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex:       SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:  SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"
SKILL_DIR="${SKILL_DIR:-$HOME/.agents/skills/epub-translation-id}"

EPUB="/path/ke/buku.epub"
WORK="/path/ke/kerja"
OUT="/path/ke/buku-ID.epub"
CHAPTERS="/path/ke/chapters"

mkdir -p "$WORK"
```

## Alur kerja

### 1. Audit EPUB

```bash
unzip -l "$EPUB"
unzip -p "$EPUB" OEBPS/content.opf | sed -n '1,120p'
```

Catat urutan spine, gambar inline, halaman gambar penuh, dan cover.

### 2. Ekstrak section

```bash
python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
```

Hasil: `src/section-XXXX.txt`, `meta.json`, dan `image_manifest.json`.

### 3. Terjemahkan

Buat `id/section-XXXX.txt` untuk setiap section berteks.

- Jumlah baris harus sama dengan `src`.
- Baris pertama adalah judul.
- Satu baris = satu paragraf.
- Pertahankan `***`, `{i}...{/i}`, dan `{b}...{/b}`.
- Terjemahkan semua section, termasuk About the Author dan Newsletter.
- Baca konteks sebelum menerjemahkan dialog.

### 4. Bangun EPUB

```bash
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
```

Builder mempertahankan gambar, posisi paragraf, TOC/NCX, dan struktur XHTML.

### 5. Validasi

```bash
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
unzip -t "$OUT"
```

Target: `issues: 0`, semua gambar identik, dan tidak ada paragraf Inggris yang tertinggal.

### 6. Audit terjemahan

Lakukan audit paragraf, kalimat, dan kelompok chapter independen. Perbaiki temuan, build ulang, lalu audit lagi sampai tidak ada kesalahan makna yang pasti. Catat perubahan di `translation-revision-notes.md`.

### 7. Ekstrak chapter TXT

```bash
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS"
```

Hasil: `bab-01.txt`, `selingan-01.txt`, dan `daftar-isi.txt`.

- TXT chapter hanya berisi judul dan paragraf.
- Durasi TTS hanya ada di `daftar-isi.txt`.
- Default 140 kata/menit; ubah dengan `--wpm 150`.
- `--no-duration` menghilangkan durasi dari daftar isi.

### 8. Laporan akhir

Sertakan path EPUB, folder chapter, jumlah kata, hasil `unzip -t`, jumlah gambar, status hash, jumlah issue, dan ringkasan revisi.

## Troubleshooting

| Gejala | Tindakan |
|---|---|
| `img count` atau `img positions` salah | Pastikan `id/section-XXXX.txt` ada dan jumlah baris benar |
| `possible untranslated English paragraphs` | Terjemahkan halaman tambahan atau tambahkan `auxiliary.json` |
| `src X lines, id Y lines` | Kembalikan satu baris = satu paragraf |
| `mimetype is compressed` | Build ulang dengan `build_epub.py` |
| TOC masih Inggris | Tambahkan label ke `common_labels` atau `auxiliary.json` |

## Etika

Terjemahkan hanya karya yang Anda punya haknya. Jangan menyebarkan EPUB sumber atau teks terjemahan tanpa izin.

## Checklist akhir

- [ ] Semua section berteks punya `id/section-XXXX.txt`.
- [ ] Jumlah baris `src` = `id`.
- [ ] `validate_epub.py` mencetak `issues: 0`.
- [ ] Semua gambar identik dan jumlah `<img>` sesuai.
- [ ] TXT chapter bersih; durasi hanya di `daftar-isi.txt`.
- [ ] `unzip -t` tidak melaporkan error.
- [ ] `translation-revision-notes.md` terisi.
