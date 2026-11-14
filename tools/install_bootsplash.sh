#!/usr/bin/env bash
# Логото на ANG Systems при пускане на системата (Plymouth), вместо текст и малинки.
# Ползва addons/ang_ender/assets/logo.png. Пуска се веднъж:  sudo ./tools/install_bootsplash.sh
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOGO="$REPO/addons/ang_ender/assets/logo.png"
THEME_DIR=/usr/share/plymouth/themes/ang
CONFIG=/boot/firmware/config.txt
CMDLINE=/boot/firmware/cmdline.txt

[ "$(id -u)" -eq 0 ] || { echo "Пусни го със sudo." >&2; exit 1; }
[ -f "$LOGO" ] || { echo "Няма $LOGO — сложи логото (PNG, прозрачен фон) и пусни пак." >&2; exit 1; }

apt-get install -y plymouth plymouth-themes

mkdir -p "$THEME_DIR"
cp "$LOGO" "$THEME_DIR/logo.png"

cat > "$THEME_DIR/ang.plymouth" <<'EOF'
[Plymouth Theme]
Name=ANG Systems
Description=ANG Systems logo on black
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/ang
ScriptFile=/usr/share/plymouth/themes/ang/ang.script
EOF

cat > "$THEME_DIR/ang.script" <<'EOF'
Window.SetBackgroundTopColor(0, 0, 0);
Window.SetBackgroundBottomColor(0, 0, 0);

logo = Image("logo.png");
# логото заема до 60% от ширината на екрана
scale = Math.Min(Window.GetWidth() * 0.6 / logo.GetWidth(), Window.GetHeight() * 0.45 / logo.GetHeight());
if (scale < 1) logo = logo.Scale(logo.GetWidth() * scale, logo.GetHeight() * scale);
sprite = Sprite(logo);
sprite.SetX(Window.GetWidth() / 2 - logo.GetWidth() / 2);
sprite.SetY(Window.GetHeight() / 2 - logo.GetHeight() / 2);

opacity = 0;
fun refresh_callback() {
    if (opacity < 1) { opacity = opacity + 0.04; sprite.SetOpacity(opacity); }
}
Plymouth.SetRefreshFunction(refresh_callback);
EOF

plymouth-set-default-theme ang

# копия, преди да пипнем файловете за зареждане
cp -n "$CONFIG" "$CONFIG.bak-ang" || true
cp -n "$CMDLINE" "$CMDLINE.bak-ang" || true

# без цветния квадрат на Raspberry Pi при пускане
grep -q '^disable_splash=1' "$CONFIG" || echo 'disable_splash=1' >> "$CONFIG"

# cmdline.txt е един ред: добавяме липсващите опции в края му
for opt in quiet splash plymouth.ignore-serial-consoles logo.nologo vt.global_cursor_default=0; do
    grep -qw -- "$opt" "$CMDLINE" || sed -i "1 s|\$| $opt|" "$CMDLINE"
done
# съобщенията на ядрото — на tty3, не на екрана
sed -i '1 s|console=tty1|console=tty3|' "$CMDLINE"

update-initramfs -u

echo "Готово. Рестартирай: sudo reboot"
echo "Връщане: sudo cp $CMDLINE.bak-ang $CMDLINE && sudo cp $CONFIG.bak-ang $CONFIG"
