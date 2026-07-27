#!/bin/sh

set -eu

INSTALL_PREFIX=${PREFIX:-"$HOME/.local"}
DATA_ROOT=${XDG_DATA_HOME:-"$HOME/.local/share"}
LAUNCHER_PATH="$INSTALL_PREFIX/bin/ssh-shift"
APPLICATIONS_DIR="$DATA_ROOT/applications"
DESKTOP_PATH="$APPLICATIONS_DIR/ssh-shift.desktop"

rm -f -- "$LAUNCHER_PATH" "$DESKTOP_PATH"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$APPLICATIONS_DIR"
fi
if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental >/dev/null 2>&1 || true
fi

printf '%s\n' 'Uninstalled SSHShift.'
printf '%s\n' 'Known-host data and the KDE Wallet privacy key were preserved.'
