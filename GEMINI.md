# Gemini CLI instructions

This repository packages an Agent Skill for translating EPUB / light novels into Indonesian.

- Read `skills/epub-translation-id/SKILL.md` when the task is EPUB translation, translation repair, EPUB validation, or chapter TXT extraction.
- Do not translate or redistribute works unless the user has the rights to do so.

## Install for Gemini CLI

```bash
gh skill install murafdev/epub-translation-id epub-translation-id --agent gemini-cli --scope user
# or, from this repository:
./install.sh --agent gemini-cli
```

## Test

```bash
make test
```
