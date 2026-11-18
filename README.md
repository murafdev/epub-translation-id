# epub-translation-id

[![test](https://github.com/murafdev/epub-translation-id/actions/workflows/test.yml/badge.svg)](https://github.com/murafdev/epub-translation-id/actions/workflows/test.yml)

Agent Skill for translating EPUB / light novels into Indonesian while preserving images, paragraph alignment, and EPUB structure.

Works with OpenCode, Claude Code, Codex, Cursor, Gemini CLI, and other Agent Skills hosts.

## Install

```text
Install the `epub-translation-id` Agent Skill from https://github.com/murafdev/epub-translation-id with `npx skills add murafdev/epub-translation-id --skill epub-translation-id -g -a <your-agent> --copy -y`, choosing the correct agent flag (`claude-code`, `opencode`, `codex`, `cursor`, or `gemini-cli`), then verify it appears in your skill list.
```

## Features

- Paragraph-aligned translation with paragraph-count validation.
- All images preserved byte-identical; inline images reinserted at the correct paragraph.
- Responsive images and SVG cover fallback.
- Context, sentence, and independent chapter audits.
- EPUB validation: XML/OPF/NCX, manifest/spine, image hashes/positions, links, and leftover English.
- Clean chapter TXT export; TTS duration only in `daftar-isi.txt`.

## Usage

Ask your agent:

> Use `epub-translation-id` to translate this EPUB into Indonesian. Preserve every image and paragraph position, audit the translation, build and validate the EPUB, then extract chapters to TXT.

Manual workflow: [INSTRUCTIONS.md](INSTRUCTIONS.md).

## Structure

```text
README.md
INSTRUCTIONS.md
skills/epub-translation-id/
  SKILL.md
  agents/openai.yaml
  references/
  scripts/
  tests/
```

## Test

```bash
make test
```

## License

MIT. See [LICENSE](LICENSE).

---

## Bahasa Indonesia

Agent Skill untuk menerjemahkan EPUB / light novel ke bahasa Indonesia tanpa merusak gambar, posisi paragraf, dan struktur EPUB.

Mendukung OpenCode, Claude Code, Codex, Cursor, Gemini CLI, dan host Agent Skills lain.

**Instalasi:** lihat bagian [Install](#install).

### Fitur

- Terjemahan selaras paragraf dengan validasi jumlah paragraf.
- Semua gambar dipertahankan identik; gambar inline dikembalikan ke posisi yang benar.
- Gambar responsif dan fallback cover SVG.
- Audit konteks, kalimat, dan chapter independen.
- Validasi EPUB: XML/OPF/NCX, manifest/spine, hash/posisi gambar, link, dan sisa bahasa Inggris.
- TXT chapter bersih; durasi TTS hanya di `daftar-isi.txt`.

### Cara pakai

Minta agent:

> Gunakan `epub-translation-id` untuk menerjemahkan EPUB ini ke bahasa Indonesia. Pertahankan semua gambar dan posisi paragraf, audit terjemahan, bangun dan validasi EPUB, lalu ekstrak chapter ke TXT.

Alur manual: [INSTRUCTIONS.md](INSTRUCTIONS.md).

### Lisensi

MIT. Lihat [LICENSE](LICENSE).
