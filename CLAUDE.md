# Claude Code instructions

This repository packages an Agent Skill for translating EPUB / light novels into Indonesian.

- Read `skills/epub-translation-id/SKILL.md` when the task is EPUB translation, translation repair, EPUB validation, or chapter TXT extraction.
- Do not translate or redistribute works unless the user has the rights to do so.

## Install for Claude Code

```bash
npx skills add murafdev/epub-translation-id --skill epub-translation-id -g -a claude-code --copy -y
# or, from this repository:
./install.sh --agent claude-code
```

The skill is then available as `/epub-translation-id`.

## Test

```bash
make test
```
