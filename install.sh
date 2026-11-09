#!/usr/bin/env bash
# Инсталира темата ANG Bambu в KlipperScreen (символна връзка, лесно обновяване с git pull).
set -euo pipefail

KS_DIR="${KS_DIR:-$HOME/KlipperScreen}"
THEME="ang-bambu"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/styles/$THEME"
DEST="$KS_DIR/styles/$THEME"

if [ ! -d "$KS_DIR/styles" ]; then
    echo "Не намирам KlipperScreen в $KS_DIR. Задай пътя: KS_DIR=/път/до/KlipperScreen ./install.sh" >&2
    exit 1
fi

if [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
    echo "$DEST вече съществува и не е символна връзка — премести го и опитай пак." >&2
    exit 1
fi

ln -sfn "$SRC" "$DEST"
echo "Темата е свързана: $DEST -> $SRC"

# Добавка с новия начален екран
ADDON_SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/addons/ang_ender"
ADDON_DEST="$KS_DIR/addons/ang_ender"
mkdir -p "$KS_DIR/addons"
if [ -e "$ADDON_DEST" ] && [ ! -L "$ADDON_DEST" ]; then
    echo "$ADDON_DEST вече съществува и не е символна връзка — пропускам добавката." >&2
else
    ln -sfn "$ADDON_SRC" "$ADDON_DEST"
    echo "Добавката е свързана: $ADDON_DEST -> $ADDON_SRC"
fi

if command -v systemctl >/dev/null 2>&1 && systemctl list-units --type=service --all | grep -q KlipperScreen; then
    sudo systemctl restart KlipperScreen
    echo "KlipperScreen е рестартиран."
fi

echo "1) Избери темата: Settings -> Icon Theme -> $THEME"
echo "2) Включи добавките: Settings -> Enable Add-ons, после рестартирай KlipperScreen"
