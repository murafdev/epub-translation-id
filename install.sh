#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_NAME="epub-translation-id"
SRC="$SCRIPT_DIR/skills/$SKILL_NAME"
ALL_AGENTS=(opencode claude-code codex cursor gemini-cli universal)
AGENTS=()
SCOPE="user"
DEST=""
MODE="auto"

usage() {
  cat <<'EOF'
Install the epub-translation-id Agent Skill for one or more hosts.

Usage:
  ./install.sh [options]

Options:
  --agent NAME    Host to install for. Repeatable.
                  opencode | claude-code | codex | cursor |
                  gemini-cli | universal | all
                  Default: auto-detect installed hosts, else universal.
  --scope SCOPE   user (default) or project.
  --dir DIR       Install into DIR/epub-translation-id instead of a host path.
  --copy          Copy files instead of symlinking.
  --link          Symlink the skill folder instead of copying.
  --help          Show this help.

Recommended cross-host installer:
  npx skills add murafdev/epub-translation-id --skill epub-translation-id -g -a claude-code --copy -y

Examples:
  ./install.sh
  ./install.sh --agent all
  ./install.sh --agent claude-code --agent codex
  ./install.sh --agent opencode --scope project
  ./install.sh --dir "$HOME/.local/share/agent-skills"
  ./install.sh --agent all --copy
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      [[ $# -ge 2 ]] || { echo "Missing value for --agent" >&2; exit 1; }
      if [[ "$2" == "all" ]]; then
        AGENTS+=("${ALL_AGENTS[@]}")
      else
        AGENTS+=("$2")
      fi
      shift 2
      ;;
    --agent=*)
      value="${1#*=}"
      if [[ "$value" == "all" ]]; then
        AGENTS+=("${ALL_AGENTS[@]}")
      else
        AGENTS+=("$value")
      fi
      shift
      ;;
    --scope)
      [[ $# -ge 2 ]] || { echo "Missing value for --scope" >&2; exit 1; }
      SCOPE="$2"
      shift 2
      ;;
    --scope=*)
      SCOPE="${1#*=}"
      shift
      ;;
    --dir)
      [[ $# -ge 2 ]] || { echo "Missing value for --dir" >&2; exit 1; }
      DEST="$2"
      shift 2
      ;;
    --dir=*)
      DEST="${1#*=}"
      shift
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --link)
      MODE="link"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ ! -f "$SRC/SKILL.md" ]]; then
  echo "Skill package not found: $SRC/SKILL.md" >&2
  exit 1
fi
if [[ "$SCOPE" != "user" && "$SCOPE" != "project" ]]; then
  echo "--scope must be user or project" >&2
  exit 1
fi

# Auto-detect installed hosts when no --agent was supplied.
if [[ ${#AGENTS[@]} -eq 0 ]]; then
  if command -v opencode >/dev/null 2>&1 || [[ -d "$HOME/.config/opencode" ]]; then
    AGENTS+=(opencode)
  fi
  if command -v claude >/dev/null 2>&1 || [[ -d "$HOME/.claude" ]]; then
    AGENTS+=(claude-code)
  fi
  if command -v codex >/dev/null 2>&1 || [[ -d "$HOME/.codex" ]]; then
    AGENTS+=(codex)
  fi
  if command -v cursor >/dev/null 2>&1 || [[ -d "$HOME/.cursor" ]]; then
    AGENTS+=(cursor)
  fi
  if command -v gemini >/dev/null 2>&1 || [[ -d "$HOME/.gemini" ]]; then
    AGENTS+=(gemini-cli)
  fi
  if [[ ${#AGENTS[@]} -eq 0 ]]; then
    AGENTS+=(universal)
  fi
fi

# De-duplicate while preserving order (Bash 3.2 compatible).
UNIQUE=()
for agent in "${AGENTS[@]}"; do
  case " ${UNIQUE[*]-} " in
    *" $agent "*) ;;
    *) UNIQUE+=("$agent") ;;
  esac
done
AGENTS=("${UNIQUE[@]}")

install_copy() {
  local source="$1"
  local dest="$2"
  mkdir -p "$dest"
  cp -R "$source/." "$dest/"
  find "$dest" -type d -name __pycache__ -prune -exec rm -rf {} +
}

install_link() {
  local source="$1"
  local dest="$2"
  rm -rf "$dest"
  mkdir -p "$(dirname "$dest")"
  ln -s "$source" "$dest"
}

direct_dest() {
  local agent="$1"
  if [[ -n "$DEST" ]]; then
    printf '%s/%s\n' "$DEST" "$SKILL_NAME"
    return 0
  fi
  if [[ "$SCOPE" == "project" ]]; then
    case "$agent" in
      opencode) printf './.opencode/skills/%s\n' "$SKILL_NAME" ;;
      claude-code) printf './.claude/skills/%s\n' "$SKILL_NAME" ;;
      gemini-cli) printf './.gemini/skills/%s\n' "$SKILL_NAME" ;;
      codex|cursor|universal) printf './.agents/skills/%s\n' "$SKILL_NAME" ;;
      *)
        echo "Project-scope direct copy is not supported for $agent; use npx skills add." >&2
        return 1
        ;;
    esac
    return 0
  fi
  case "$agent" in
    opencode) printf '%s\n' "${OPENCODE_SKILLS_DIR:-$HOME/.config/opencode/skills}/$SKILL_NAME" ;;
    claude-code) printf '%s\n' "${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}/$SKILL_NAME" ;;
    codex) printf '%s\n' "${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}/$SKILL_NAME" ;;
    cursor) printf '%s\n' "${CURSOR_SKILLS_DIR:-$HOME/.cursor/skills}/$SKILL_NAME" ;;
    gemini-cli) printf '%s\n' "${GEMINI_SKILLS_DIR:-$HOME/.gemini/skills}/$SKILL_NAME" ;;
    universal) printf '%s\n' "${AGENTS_SKILLS_DIR:-$HOME/.agents/skills}/$SKILL_NAME" ;;
    *)
      echo "Unknown agent: $agent" >&2
      return 1
      ;;
  esac
}

install_direct() {
  local agent="$1"
  local dest
  dest="$(direct_dest "$agent")" || return 1
  if [[ "$MODE" == "link" ]]; then
    install_link "$SRC" "$dest"
  else
    install_copy "$SRC" "$dest"
  fi
  printf '  %-12s %s\n' "$agent" "$dest"
}

# --dir installs once to an explicit parent directory.
if [[ -n "$DEST" ]]; then
  mkdir -p "$DEST"
  DEST="$(cd "$DEST" && pwd)"
  dest="$DEST/$SKILL_NAME"
  if [[ "$MODE" == "link" ]]; then
    install_link "$SRC" "$dest"
  else
    install_copy "$SRC" "$dest"
  fi
  echo "Installed $SKILL_NAME to: $dest"
  exit 0
fi

# --copy/--link always uses direct installation.
if [[ "$MODE" != "auto" ]]; then
  echo "Installing $SKILL_NAME directly:"
  for agent in "${AGENTS[@]}"; do
    install_direct "$agent"
  done
  echo
  echo "Done. Restart the host or start a new session if the skill is not listed."
  exit 0
fi

echo "Installing $SKILL_NAME directly:"
for agent in "${AGENTS[@]}"; do
  install_direct "$agent"
done

echo
echo "Done. Invoke the skill by name in your host:"
echo "  OpenCode:    \$epub-translation-id"
echo "  Claude Code: /epub-translation-id"
echo "  Codex:       \$epub-translation-id"
echo "  Cursor/Gemini/other: mention epub-translation-id or use the skill picker."
echo "Restart the host if it does not appear automatically."
