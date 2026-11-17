# epub-translation-id

[![test](https://github.com/murafdev/epub-translation-id/actions/workflows/test.yml/badge.svg)](https://github.com/murafdev/epub-translation-id/actions/workflows/test.yml)

An Agent Skill for translating EPUB / light novels into Indonesian while preserving every image, paragraph position, and the EPUB structure.

Works with **OpenCode**, **Claude Code**, **Codex**, **Cursor**, **Gemini CLI**, and other hosts that support the open Agent Skills standard.

[English](#english) · [Bahasa Indonesia](#bahasa-indonesia)

---

## English

### What it does

`epub-translation-id` turns a source EPUB into an Indonesian EPUB without flattening the book into plain text. It keeps the original XHTML structure, re-inserts inline illustrations at the correct paragraph, validates the result, and can export one TXT file per chapter.

It is designed for context-aware literary translation, not word-for-word replacement. Pair it with the `indonesia-eyd-writing-skill` for Indonesian spelling, punctuation, and editorial decisions.

### Works with

| Host | Install with | Invoke with |
|---|---|---|
| OpenCode | `--agent opencode` | `$epub-translation-id` |
| Claude Code | `--agent claude-code` | `/epub-translation-id` |
| Codex | `--agent codex` | `$epub-translation-id` |
| Cursor | `--agent cursor` | skill picker / natural language |
| Gemini CLI | `--agent gemini-cli` | skill picker / natural language |
| Other Agent Skills hosts | `--agent universal` | host-specific |

The package follows the open Agent Skills layout: `SKILL.md`, `scripts/`, `references/`, and optional `agents/openai.yaml`. The Python scripts use only the standard library, so they are not tied to a particular agent.

### Features

- **Paragraph-aligned translation** — one source paragraph becomes one translated line. Paragraph counts are checked against the source.
- **Image preservation** — every original image file is kept byte-identical. Inline images are re-inserted at their recorded paragraph index. SVG covers get a responsive `<img>` fallback.
- **Readable images** — legacy `height="100%"` sizing is replaced with responsive width, `height:auto`, and block layout.
- **TOC and auxiliary pages** — chapter labels, NCX entries, Color Inserts, Title Page, About the Author, Newsletter, and common promotional lines are translated.
- **Context audits** — repeated paragraph, sentence, and independent chapter-group audits until no definite meaning errors remain.
- **EPUB validation** — XML/OPF/NCX parsing, manifest/spine checks, `mimetype` rules, SHA-256 image comparison, image counts and positions, internal links, paragraph alignment, and untranslated-English detection.
- **Chapter TXT export** — `bab-01.txt`, `selingan-01.txt`, and `daftar-isi.txt`, with scene breaks preserved.
- **TTS duration estimates** — each chapter TXT gets an estimated speaking time at 140 words/minute (a conservative upper bound, configurable with `--wpm`); the index includes per-chapter and total duration.
- **Synthetic test** — a copyright-free mini EPUB exercises the whole pipeline.

### Requirements

- Python 3.8+ (standard library only)
- One supported agent, or any tool that can run the Python scripts manually
- `gh` with `gh skill install` for the easiest cross-host installation (optional)
- Optional: `indonesia-eyd-writing-skill` for Indonesian editorial review
- Optional: WeasyPrint and `pdfimages` for visual rendering checks

### Install

The recommended installer is GitHub CLI, which understands host-specific skill directories:

```bash
# Pick one agent:
gh skill install murafdev/epub-translation-id epub-translation-id \
  --agent claude-code --scope user

# Other agents:
# --agent opencode
# --agent codex
# --agent cursor
# --agent gemini-cli
# --agent universal
```

Use `--scope project` to install into the current repository instead of your user directory.

Without `gh skill install`, use the bundled installer:

```bash
git clone https://github.com/murafdev/epub-translation-id.git
cd epub-translation-id
./install.sh
# If the filesystem does not allow the executable bit:
# bash install.sh

# Explicit targets:
./install.sh --agent claude-code
./install.sh --agent all
./install.sh --agent opencode --scope project
./install.sh --dir "$HOME/.local/share/agent-skills"
```

Default user paths:

| Host | Path |
|---|---|
| OpenCode | `~/.config/opencode/skills/epub-translation-id` |
| Claude Code | `~/.claude/skills/epub-translation-id` |
| Codex / universal | `~/.agents/skills/epub-translation-id` |
| Cursor | `~/.cursor/skills/epub-translation-id` |
| Gemini CLI | `~/.gemini/skills/epub-translation-id` |

Project scope uses `.opencode/skills`, `.claude/skills`, `.agents/skills`, or `.gemini/skills` in the current repository.

Manual install example for Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/epub-translation-id "$HOME/.claude/skills/"

# Codex / universal:
mkdir -p "$HOME/.agents/skills"
cp -R skills/epub-translation-id "$HOME/.agents/skills/"
```

Start a new host session after installing so the skill is discovered.

### Quick start

Give the agent an EPUB and a request such as:

> Use `epub-translation-id` to translate this EPUB into Indonesian. Preserve every image and paragraph position, audit the translation, build the final EPUB, validate it, and extract each chapter to TXT.

Or run the pipeline manually. Set `SKILL_DIR` to the path for your host:

```bash
# OpenCode:
SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code:
# SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex / generic:
# SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:
# SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"

EPUB="/path/to/book.epub"
WORK="/path/to/work"
OUT="/path/to/book-ID.epub"
CHAPTERS="/path/to/chapters"

python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
# Translate $WORK/src/section-XXXX.txt into $WORK/id/section-XXXX.txt
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS"
```

See [`INSTRUCTIONS.md`](INSTRUCTIONS.md) for the full workflow, file formats, audit loop, and troubleshooting.

### Repository layout

```text
.
├── AGENTS.md                       # Codex / generic agent pointer
├── CLAUDE.md                       # Claude Code pointer
├── GEMINI.md                       # Gemini CLI pointer
├── INSTRUCTIONS.md                 # Human-facing workflow guide
├── README.md
├── LICENSE
├── install.sh                      # Multi-host installer
├── Makefile
├── .github/workflows/test.yml      # CI: synthetic pipeline
└── skills/
    └── epub-translation-id/
        ├── SKILL.md                # Agent-facing instructions
        ├── agents/openai.yaml      # Optional Codex UI metadata
        ├── references/
        │   ├── workflow-detail.md
        │   └── audit-checklist.md
        ├── scripts/
        │   ├── extract_sections.py
        │   ├── build_epub.py
        │   ├── validate_epub.py
        │   └── extract_chapters.py
        └── tests/
            └── test_pipeline.py
```

### Scripts

| Script | Purpose |
|---|---|
| `extract_sections.py` | Extract paragraph-aligned source text, `{i}`/`{b}` markers, scene breaks, and inline image positions. |
| `build_epub.py` | Build the translated EPUB, preserve XHTML head/body, re-insert images, translate TOC/NCX and auxiliary labels, normalise images, add cover fallback. |
| `validate_epub.py` | Validate ZIP/mimetype, XML, manifest/spine, image hashes/counts/positions, links, paragraph alignment, and English leftovers. |
| `extract_chapters.py` | Export story chapters to TXT with estimated TTS duration and write `daftar-isi.txt`. |

Optional workspace files:

`auxiliary.json` — exact phrase replacements for promo/watermark pages:
```json
{"Download all your Fav Light Novels from": "Unduh semua novel ringan favoritmu dari"}
```

`metadata.json` — final book metadata:
```json
{"title": "Judul Buku (Edisi Indonesia)", "creator": "Nama Penulis", "identifier": "urn:uuid:..."}
```

### TTS duration

Each chapter TXT starts with an estimated speaking time:

```text
Bab 1: ...
Perkiraan durasi TTS: 22 menit 9 detik (140 kata/menit)
```

The default is deliberately conservative. Use `--wpm 150` for a slightly faster estimate, or `--no-duration` to omit the estimate. `daftar-isi.txt` also lists per-chapter and total duration.

### Test

```bash
python3 skills/epub-translation-id/tests/test_pipeline.py
# or
make test
```

The test creates a synthetic EPUB in a temporary directory. It does not include any copyrighted book content.

### Customising for another EPUB

Most books work as-is. If a book uses different front/back matter labels, edit `common_labels` and `title_labels` in `skills/epub-translation-id/scripts/build_epub.py`, or add exact phrase pairs to `auxiliary.json`. If the XHTML uses unusual block markup, adjust the block selectors in `extract_sections.py` and `extract_chapters.py`.

### Legal and ethical use

Only translate and redistribute works you have the rights to translate. This repository contains scripts and documentation, not any book text. Do not commit source EPUBs, translated book content, or cover art unless you have permission.

### License

MIT. See [`LICENSE`](LICENSE).

---

## Bahasa Indonesia

### Ringkasan

`epub-translation-id` adalah **Agent Skill** untuk menerjemahkan EPUB/light novel ke bahasa Indonesia tanpa merusak struktur buku. Semua gambar asli dipertahankan, gambar inline dikembalikan ke posisi paragraf yang benar, EPUB divalidasi, dan setiap chapter bisa diekspor menjadi TXT.

Skill ini mengikuti standar terbuka **Agent Skills** dan bisa dipakai di **OpenCode**, **Claude Code**, **Codex**, **Cursor**, **Gemini CLI**, serta host lain yang mendukung `SKILL.md`.

Skill ini menekankan terjemahan yang sadar konteks, bukan kata per kata. Gunakan bersama `indonesia-eyd-writing-skill` untuk ejaan, tanda baca, dan keputusan editorial bahasa Indonesia.

### Kompatibilitas host

| Host | Instalasi | Invokasi |
|---|---|---|
| OpenCode | `--agent opencode` | `$epub-translation-id` |
| Claude Code | `--agent claude-code` | `/epub-translation-id` |
| Codex | `--agent codex` | `$epub-translation-id` |
| Cursor | `--agent cursor` | skill picker / bahasa alami |
| Gemini CLI | `--agent gemini-cli` | skill picker / bahasa alami |
| Host Agent Skills lain | `--agent universal` | sesuai host |

Skrip Python hanya memakai standard library, jadi tidak terikat pada satu agent. Perintah shell memakai `bash`; di Windows gunakan Git Bash/WSL atau jalankan skrip Python langsung.

### Fitur

- **Selaras paragraf** — satu paragraf sumber menjadi satu baris terjemahan; jumlah paragraf diperiksa terhadap sumber.
- **Gambar aman** — semua file gambar dipertahankan identik secara byte. Gambar inline disisipkan kembali pada indeks paragraf yang tercatat. Cover SVG mendapat fallback `<img>` responsif.
- **Gambar tampil baik** — ukuran lama `height="100%"` diganti dengan lebar responsif, `height:auto`, dan layout blok.
- **TOC dan halaman tambahan** — label chapter, NCX, Color Inserts, Title Page, About the Author, Newsletter, dan baris promosi umum diterjemahkan.
- **Audit konteks** — audit paragraf, kalimat, dan kelompok chapter secara independen, diulang sampai tidak ada kesalahan makna yang pasti.
- **Validasi EPUB** — XML/OPF/NCX, manifest/spine, aturan `mimetype`, hash SHA-256 gambar, jumlah dan posisi gambar, link internal, keselarasan paragraf, dan sisa bahasa Inggris.
- **Ekstrak chapter TXT** — `bab-01.txt`, `selingan-01.txt`, dan `daftar-isi.txt`; scene break `***` dipertahankan.
- **Perkiraan durasi TTS** — setiap TXT chapter mendapat estimasi waktu baca pada 140 kata/menit (estimasi konservatif, bisa diubah dengan `--wpm`); indeks memuat durasi per chapter dan total.
- **Tes sintetis** — EPUB mini tanpa konten berhak cipta untuk menguji seluruh pipeline.

### Kebutuhan

- Python 3.8+ (hanya standard library)
- Salah satu agent yang didukung, atau alat apa pun yang bisa menjalankan skrip Python secara manual
- `gh` dengan `gh skill install` untuk instalasi lintas host termudah (opsional)
- Opsional: `indonesia-eyd-writing-skill` untuk penyuntingan bahasa Indonesia
- Opsional: WeasyPrint dan `pdfimages` untuk pemeriksaan render visual

### Instalasi

Cara yang disarankan adalah GitHub CLI, yang tahu path skill tiap host:

```bash
# Pilih salah satu agent:
gh skill install murafdev/epub-translation-id epub-translation-id \
  --agent claude-code --scope user

# Agent lain:
# --agent opencode
# --agent codex
# --agent cursor
# --agent gemini-cli
# --agent universal
```

Gunakan `--scope project` untuk memasang ke repo saat ini, bukan ke direktori user.

Tanpa `gh skill install`, gunakan installer bawaan:

```bash
git clone https://github.com/murafdev/epub-translation-id.git
cd epub-translation-id
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

Contoh instalasi manual untuk Claude Code:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/epub-translation-id "$HOME/.claude/skills/"

# Codex / universal:
mkdir -p "$HOME/.agents/skills"
cp -R skills/epub-translation-id "$HOME/.agents/skills/"
```

Mulai sesi baru setelah instalasi agar skill terdeteksi.

### Cara pakai

Beri agent file EPUB dan permintaan seperti:

> Gunakan `epub-translation-id` untuk menerjemahkan EPUB ini ke bahasa Indonesia. Pertahankan semua gambar dan posisi paragraf, audit terjemahan, bangun EPUB final, validasi, lalu ekstrak setiap chapter ke TXT.

Atau jalankan pipeline manual. Sesuaikan `SKILL_DIR` dengan host:

```bash
# OpenCode:
SKILL_DIR="$HOME/.config/opencode/skills/epub-translation-id"
# Claude Code:
# SKILL_DIR="$HOME/.claude/skills/epub-translation-id"
# Codex / generic:
# SKILL_DIR="$HOME/.agents/skills/epub-translation-id"
# Gemini CLI:
# SKILL_DIR="$HOME/.gemini/skills/epub-translation-id"

EPUB="/path/ke/buku.epub"
WORK="/path/ke/kerja"
OUT="/path/ke/buku-ID.epub"
CHAPTERS="/path/ke/chapters"

python3 "$SKILL_DIR/scripts/extract_sections.py" "$EPUB" "$WORK"
# Terjemahkan $WORK/src/section-XXXX.txt menjadi $WORK/id/section-XXXX.txt
python3 "$SKILL_DIR/scripts/build_epub.py" "$EPUB" "$WORK" "$OUT"
python3 "$SKILL_DIR/scripts/validate_epub.py" "$EPUB" "$OUT" "$WORK"
python3 "$SKILL_DIR/scripts/extract_chapters.py" "$OUT" "$WORK" "$CHAPTERS"
```

Panduan lengkap ada di [`INSTRUCTIONS.md`](INSTRUCTIONS.md).

### Struktur repo

```text
.
├── AGENTS.md                       # Pointer untuk Codex/agent generik
├── CLAUDE.md                       # Pointer untuk Claude Code
├── GEMINI.md                       # Pointer untuk Gemini CLI
├── INSTRUCTIONS.md                 # Panduan untuk manusia
├── README.md
├── LICENSE
├── install.sh                      # Installer multi-host
├── Makefile
├── .github/workflows/test.yml      # CI: pipeline sintetis
└── skills/
    └── epub-translation-id/
        ├── SKILL.md                # Instruksi untuk agent
        ├── agents/openai.yaml      # Metadata UI Codex (opsional)
        ├── references/
        │   ├── workflow-detail.md
        │   └── audit-checklist.md
        ├── scripts/
        │   ├── extract_sections.py
        │   ├── build_epub.py
        │   ├── validate_epub.py
        │   └── extract_chapters.py
        └── tests/
            └── test_pipeline.py
```

### Skrip

| Skrip | Fungsi |
|---|---|
| `extract_sections.py` | Ekstrak teks selaras paragraf, penanda `{i}`/`{b}`, scene break, dan posisi gambar inline. |
| `build_epub.py` | Bangun EPUB terjemahan, pertahankan head/body XHTML, sisipkan gambar, terjemahkan TOC/NCX dan label tambahan, normalkan gambar, fallback cover. |
| `validate_epub.py` | Validasi ZIP/mimetype, XML, manifest/spine, hash/jumlah/posisi gambar, link, keselarasan paragraf, dan sisa bahasa Inggris. |
| `extract_chapters.py` | Ekspor chapter cerita ke TXT dengan perkiraan durasi TTS dan tulis `daftar-isi.txt`. |

File opsional di workspace:

`auxiliary.json` — penggantian frasa exact untuk halaman promosi/watermark:
```json
{"Download all your Fav Light Novels from": "Unduh semua novel ringan favoritmu dari"}
```

`metadata.json` — metadata buku final:
```json
{"title": "Judul Buku (Edisi Indonesia)", "creator": "Nama Penulis", "identifier": "urn:uuid:..."}
```

### Durasi TTS

Setiap TXT chapter diawali perkiraan waktu baca:

```text
Bab 1: ...
Perkiraan durasi TTS: 22 menit 9 detik (140 kata/menit)
```

Default sengaja dibuat konservatif. Gunakan `--wpm 150` untuk estimasi yang sedikit lebih cepat, atau `--no-duration` untuk menghilangkan estimasi. `daftar-isi.txt` juga memuat durasi per chapter dan total.

### Tes

```bash
python3 skills/epub-translation-id/tests/test_pipeline.py
# atau
make test
```

Tes membuat EPUB sintetis di direktori sementara dan tidak menyertakan konten buku berhak cipta.

### Kustomisasi untuk EPUB lain

Sebagian besar buku bisa langsung dipakai. Jika label front/back matter berbeda, ubah `common_labels` dan `title_labels` di `skills/epub-translation-id/scripts/build_epub.py`, atau tambahkan pasangan frasa exact ke `auxiliary.json`. Jika markup XHTML tidak biasa, sesuaikan selector blok di `extract_sections.py` dan `extract_chapters.py`.

### Etika dan hak cipta

Terjemahkan dan sebarkan hanya karya yang Anda punya haknya. Repo ini berisi skrip dan dokumentasi, bukan teks buku. Jangan commit EPUB sumber, teks terjemahan, atau cover art tanpa izin.

### Lisensi

MIT. Lihat [`LICENSE`](LICENSE).
