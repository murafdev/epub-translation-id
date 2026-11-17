# epub-translation-id

This repository packages an Agent Skill for translating EPUB / light novels into Indonesian while preserving images, paragraph alignment, and EPUB structure.

## Skill package

- `skills/epub-translation-id/SKILL.md`
- `skills/epub-translation-id/scripts/`
- `skills/epub-translation-id/references/`
- `skills/epub-translation-id/tests/`
- Gemini CLI pointer: `GEMINI.md`
- Claude Code pointer: `CLAUDE.md`

## Install

Universal, host-aware installer:

```bash
gh skill install murafdev/epub-translation-id epub-translation-id --agent codex --scope user
# agents: opencode, claude-code, codex, cursor, gemini-cli, universal
```

Local fallback:

```bash
./install.sh --agent all
# or: ./install.sh --agent codex
# or: ./install.sh --dir "$HOME/.local/share/agent-skills"
```

## Use

Read `skills/epub-translation-id/SKILL.md` when the task is EPUB translation, translation repair, EPUB validation, or chapter TXT extraction.

## Test

```bash
make test
```

## Legal

Do not commit EPUBs, translated book text, or cover art without permission. The repository contains scripts and documentation only.
