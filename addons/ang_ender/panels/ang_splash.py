"""Екран „Свързване с Klipper“ с логото на ANG Systems.

Наследява стандартния splash_screen (бутоните за рестарт, съобщенията и
поведението остават същите) и само пренарежда екрана: логото голямо в
средата, съобщението под него, бутоните долу.

Логото: addons/ang_ender/assets/logo.png (или logo.svg), за предпочитане
светло/бяло с прозрачен фон. Без файл се показва надпис „ANG SYSTEMS“.
"""
import os

from gi.repository import GdkPixbuf, Gtk

from ks_addons.ang_ender import ui
from panels.splash_screen import Panel as StockSplash


def logo_path():
    for name in ("logo.png", "logo.svg"):
        p = os.path.join(ui.ADDON_DIR, "assets", name)
        if os.path.exists(p):
            return p
    return None


class Panel(StockSplash):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title)
        gtk = self._gtk
        cw, ch = gtk.content_width, gtk.content_height

        # стандартното съдържание: main -> [info(image, scroll), actions]
        main = self.content.get_children()[0]
        info = main.get_children()[0]
        image, scroll = info.get_children()
        info.remove(image)
        info.remove(scroll)
        main.remove(info)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(gtk.font_size * 0.8), valign=Gtk.Align.CENTER)
        path = logo_path()
        if path:
            try:
                pb = GdkPixbuf.Pixbuf.new_from_file_at_size(path, int(cw * 0.6), int(ch * 0.42))
                box.pack_start(Gtk.Image.new_from_pixbuf(pb), False, False, 0)
            except Exception:
                path = None
        if not path:
            box.pack_start(ui.label("ANG SYSTEMS", "ang-splash-name", xalign=0.5), False, False, 0)
        bar = Gtk.Box(halign=Gtk.Align.CENTER)
        bar.get_style_context().add_class("ang-accent-bar")
        bar.set_size_request(int(cw * 0.18), 3)
        box.pack_start(bar, False, False, 0)
        scroll.set_size_request(-1, int(ch * 0.22))
        self.labels["text"].get_style_context().add_class("ang-sub")
        box.pack_start(scroll, False, False, 0)
        main.pack_start(box, True, True, 8)
        self.content.get_style_context().add_class("ang-splash")
