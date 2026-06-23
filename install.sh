#!/bin/sh
# commando installer — clone repo to $HOME/.commando and wire PATH.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Frank-Pu/commando/main/install.sh | sh
#
# Env:
#   COMMANDO_HOME   install dir (default: $HOME/.commando)
#   COMMANDO_REPO   git URL (default: https://github.com/Frank-Pu/commando.git)

set -e

REPO="${COMMANDO_REPO:-https://github.com/Frank-Pu/commando.git}"
INSTALL_DIR="${COMMANDO_HOME:-$HOME/.commando}"
BIN_DIR="$INSTALL_DIR/bin"

# ── colors (best-effort, no-op on dumb terminals) ────────────────────────────
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    C_RED="$(tput setaf 1)"; C_GREEN="$(tput setaf 2)"; C_YELLOW="$(tput setaf 3)"
    C_CYAN="$(tput setaf 6)"; C_DIM="$(tput dim)"; C_BOLD="$(tput bold)"; C_RESET="$(tput sgr0)"
else
    C_RED=""; C_GREEN=""; C_YELLOW=""; C_CYAN=""; C_DIM=""; C_BOLD=""; C_RESET=""
fi

say()  { printf '%s\n' "$*"; }
ok()   { printf '    %s✓%s  %s\n' "$C_GREEN" "$C_RESET" "$*"; }
warn() { printf '    %s!%s  %s\n' "$C_YELLOW" "$C_RESET" "$*"; }
bad()  { printf '    %s✗%s  %s\n' "$C_RED" "$C_RESET" "$*"; }
dim()  { printf '    %s%s%s\n' "$C_DIM" "$*" "$C_RESET"; }

say ""
printf '  %s%scommando installer%s\n' "$C_BOLD" "$C_CYAN" "$C_RESET"
printf '  %sRuntime is commodity. Configuration is the moat.%s\n' "$C_DIM" "$C_RESET"
say ""

# ── Step 1 · prerequisites ───────────────────────────────────────────────────
say "  Step 1 · Checking prerequisites"
missing=""
command -v git     >/dev/null 2>&1 || missing="$missing git"
command -v python3 >/dev/null 2>&1 || missing="$missing python3"
if [ -n "$missing" ]; then
    bad "missing:$missing"
    say ""
    say "  Install the missing tools and re-run the installer."
    exit 1
fi
ok "git, python3"

# ── Step 2 · clone or update ─────────────────────────────────────────────────
say ""
say "  Step 2 · Installing to $INSTALL_DIR"
if [ -d "$INSTALL_DIR/.git" ]; then
    warn "existing install — pulling latest"
    git -C "$INSTALL_DIR" pull --ff-only >/dev/null
    ok "updated"
else
    git clone --depth 1 "$REPO" "$INSTALL_DIR" >/dev/null 2>&1 || {
        bad "git clone failed. Try: git clone $REPO $INSTALL_DIR"
        exit 1
    }
    ok "cloned"
fi

# ── Step 3 · wire PATH ───────────────────────────────────────────────────────
say ""
say "  Step 3 · Wiring PATH"
SHELL_NAME=$(basename "${SHELL:-/bin/zsh}")
case "$SHELL_NAME" in
    zsh)   RC="$HOME/.zshrc";  PATH_LINE='export PATH="$HOME/.commando/bin:$PATH"' ;;
    bash)  RC="$HOME/.bashrc"; PATH_LINE='export PATH="$HOME/.commando/bin:$PATH"' ;;
    fish)  RC="$HOME/.config/fish/config.fish"; PATH_LINE='set -gx PATH $HOME/.commando/bin $PATH' ;;
    *)     RC=""; PATH_LINE='export PATH="$HOME/.commando/bin:$PATH"' ;;
esac

if [ -n "$RC" ]; then
    mkdir -p "$(dirname "$RC")"
    [ -f "$RC" ] || touch "$RC"
    if grep -q ".commando/bin" "$RC" 2>/dev/null; then
        dim "(${RC} already wired)"
    else
        {
            echo ""
            echo "# commando"
            echo "$PATH_LINE"
        } >> "$RC"
        ok "added to $RC"
    fi
else
    warn "could not detect shell rc — add this line manually:"
    printf '      %s\n' "$PATH_LINE"
fi

# ── Step 4 · done ────────────────────────────────────────────────────────────
say ""
printf '  %s✓ commando installed%s\n' "$C_GREEN$C_BOLD" "$C_RESET"
say ""
say "  Next:"
say ""
say "    1) Open a new terminal  (or:  source $RC)"
say "    2) commando onboard"
say ""
say "  Docs:  https://github.com/Frank-Pu/commando"
say ""
