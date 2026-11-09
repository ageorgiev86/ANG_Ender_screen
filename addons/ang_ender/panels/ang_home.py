"""Изчистен начален екран в стил Bambu Lab за KlipperScreen.

Замества "main_menu" (зарежда се от добавката ang_ender). Разположение за 800x480:

    ┌──────────────────────────────────────────────┐
    │  [илюстрация на принтера]  ┃ Готов за печат   │
    │                            ┃ подзаглавие      │
    │ ┌───────────────┐ ┌──────────────────────────┐│
    │ │ миниатюра     │ │ дюза │ легло │ мрежа │ ☰ ││
    │ │ Файлове       │ │      │       │       │   ││
    │ └───────────────┘ └──────────────────────────┘│
    └──────────────────────────────────────────────┘
"""
import logging
import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import GdkPixbuf, Gtk, Pango

from ks_includes.screen_panel import ScreenPanel

ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def _label(text, cls, xalign=0.0, wrap=False):
    lbl = Gtk.Label(label=text, xalign=xalign)
    lbl.get_style_context().add_class(cls)
    if wrap:
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
    else:
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
    return lbl


class Panel(ScreenPanel):
    def __init__(self, screen, title, items=None, **kwargs):
        title = title or "ANG Ender"
        super().__init__(screen, title)
        self.items = items or []
        self.latest_file = None
        cw = self._gtk.content_width
        ch = self._gtk.content_height
        fs = self._gtk.font_size

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.6))
        root.get_style_context().add_class("ang-home")

        # ---------- Горна част: принтер + поздрав ----------
        hero = Gtk.Box(spacing=int(fs), vexpand=True)
        art_h = int(ch * 0.52)
        art = os.path.join(ASSETS, "printer.svg")
        try:
            pb = GdkPixbuf.Pixbuf.new_from_file_at_size(art, int(cw * 0.42), art_h)
            hero.pack_start(Gtk.Image.new_from_pixbuf(pb), False, False, int(fs * 0.5))
        except Exception as e:
            logging.warning(f"ang_home: no printer art: {e}")

        greet = Gtk.Box(spacing=int(fs * 0.7), valign=Gtk.Align.CENTER)
        bar = Gtk.Box()
        bar.get_style_context().add_class("ang-accent-bar")
        bar.set_size_request(max(3, int(fs * 0.2)), -1)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3))
        self.labels["greeting"] = _label("Готов за печат", "ang-greeting", wrap=True)
        self.labels["sub"] = _label("Да направим още един страхотен печат!", "ang-sub", wrap=True)
        text.add(self.labels["greeting"])
        text.add(self.labels["sub"])
        greet.pack_start(bar, False, False, 0)
        greet.pack_start(text, True, True, 0)
        hero.pack_start(greet, True, True, 0)
        root.pack_start(hero, True, True, 0)

        # ---------- Долна част: карти ----------
        cards = Gtk.Box(spacing=int(fs * 0.8), homogeneous=False)
        cards.set_size_request(-1, int(ch * 0.40))

        files = Gtk.Button(hexpand=True)
        files.get_style_context().add_class("ang-card")
        files.connect("clicked", self.open_panel, "print")
        fbox = Gtk.Box(spacing=int(fs * 0.8), halign=Gtk.Align.CENTER)
        self.labels["thumb"] = self._gtk.Image("file", fs * 3.4, fs * 3.4)
        fbox.pack_start(self.labels["thumb"], False, False, 0)
        ftext = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        ftext.add(_label("Файлове", "ang-card-title"))
        self.labels["file_hint"] = _label("за печат", "ang-sub")
        ftext.add(self.labels["file_hint"])
        fbox.pack_start(ftext, False, False, 0)
        files.add(fbox)
        cards.pack_start(files, True, True, 0)

        status = Gtk.Box(homogeneous=True, hexpand=True)
        status.get_style_context().add_class("ang-card")
        self.labels["nozzle"] = self._cell(status, "extruder", "--°", "temperature")
        self.labels["bed"] = self._cell(status, "bed", "--°", "temperature")
        self._cell(status, "network", "Мрежа", "network")
        self._cell(status, "settings", "Меню", None, self.open_menu)
        cards.pack_start(status, True, True, 0)
        root.pack_start(cards, False, False, 0)

        self.content.add(root)
        self._find_latest_file()

    # ---------- помощни ----------
    def _cell(self, parent, icon, text, panel, cb=None):
        fs = self._gtk.font_size
        btn = Gtk.Button(hexpand=True, vexpand=True)
        btn.get_style_context().add_class("ang-cell")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), valign=Gtk.Align.CENTER)
        box.add(self._gtk.Image(icon, fs * 1.7, fs * 1.7))
        lbl = _label(text, "ang-cell-value", xalign=0.5)
        box.add(lbl)
        btn.add(box)
        if cb:
            btn.connect("clicked", cb)
        elif panel:
            btn.connect("clicked", self.open_panel, panel)
        parent.pack_start(btn, True, True, 0)
        return lbl

    def open_panel(self, widget, panel):
        self._screen.show_panel(panel)

    def open_menu(self, widget):
        # Оригиналното главно меню на KlipperScreen (Home, Движение, Калибрация...)
        self._screen.show_panel("menu", "Меню", panel_name="ang_controls", items=self.items)

    def _find_latest_file(self):
        try:
            files = [f for f in self._files.files.values() if f.get("path", "").endswith(".gcode")]
        except Exception:
            files = []
        if not files:
            return
        latest = max(files, key=lambda f: f.get("modified", 0))
        self.latest_file = latest["path"]
        self.labels["file_hint"].set_text(os.path.splitext(os.path.basename(self.latest_file))[0])
        size = self._gtk.font_size * 3.4

        def set_thumb(pixbuf):
            if pixbuf is not None:
                self.labels["thumb"].set_from_pixbuf(pixbuf)

        self.load_image_async(self.latest_file, size, size, callback=set_thumb)

    # ---------- живи данни ----------
    def activate(self):
        self._find_latest_file()

    def process_update(self, action, data):
        if action != "notify_status_update" or not self._printer:
            return
        for dev, key in (("extruder", "nozzle"), ("heater_bed", "bed")):
            if dev not in data:
                continue
            temp = self._printer.get_stat(dev, "temperature")
            target = self._printer.get_stat(dev, "target")
            if temp is None:
                continue
            txt = f"{temp:.0f}°" if not target else f"{temp:.0f}/{target:.0f}°"
            self.labels[key].set_text(txt)
