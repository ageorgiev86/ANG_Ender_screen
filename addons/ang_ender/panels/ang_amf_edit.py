"""Редакция на слот: материал (профил), цвят, температури от профила. AMF_SET_SPOOL / AMF_CLEAR_SPOOL."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel

COLORS = [
    "FFFFFF", "161616", "8A8A8A", "E53935", "FF7A1A", "FFD21F",
    "4CAF50", "1E88E5", "3DA5FF", "8E24AA", "F06292", "8D6E63",
]


class Panel(AngPanel):
    def __init__(self, screen, title, slot=0, **kwargs):
        super().__init__(screen, title or "Редакция на филамент")
        self.slot = slot
        gtk = self._gtk
        fs = gtk.font_size
        s = (self.stat("amf", "slots", {}) or {}).get(str(slot), {})
        self.color = (s.get("color") or "").lstrip("#").upper() or None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        name = f"слот {int(slot) + 1}"
        root.add(ui.page_header(f"Редакция на филамент · {name}", self.back))
        card = Gtk.Grid(row_spacing=int(fs * 0.7), column_spacing=int(fs * 0.8), vexpand=True)
        card.get_style_context().add_class("ang-card")
        card.get_style_context().add_class("ang-pad")

        card.attach(ui.label("Материал", "ang-caption-strong"), 0, 0, 1, 1)
        self.combo = Gtk.ComboBoxText(hexpand=True)
        profiles = self.stat("amf", "profiles", []) or ["PLA", "PETG", "ABS", "ASA", "TPU", "PC", "PA-CF"]
        for p in profiles:
            self.combo.append_text(p)
        cur = s.get("profile")
        self.combo.set_active(profiles.index(cur) if cur in profiles else 0)
        card.attach(self.combo, 1, 0, 1, 1)

        card.attach(ui.label("Цвят", "ang-caption-strong"), 0, 1, 1, 1)
        sw = Gtk.FlowBox(max_children_per_line=6, selection_mode=Gtk.SelectionMode.NONE, column_spacing=6, row_spacing=6)
        self.swatches = []
        for c in COLORS:
            b = Gtk.Button()
            b.set_size_request(int(fs * 2.2), int(fs * 1.8))
            b.get_style_context().add_class("ang-swatch")
            b.get_style_context().add_class(f"ang-c-{c}")
            b.connect("clicked", self._pick, c)
            sw.add(b)
            self.swatches.append((b, c))
        card.attach(sw, 1, 1, 1, 1)

        card.attach(ui.label("Дюза", "ang-caption-strong"), 0, 2, 1, 1)
        self.temps = ui.label("мин. 190℃     макс. 230℃   (от профила)", "ang-sub")
        card.attach(self.temps, 1, 2, 1, 1)

        btns = Gtk.Box(spacing=int(fs * 0.5), halign=Gtk.Align.END)
        clear = Gtk.Button(label="Изчисти")
        clear.get_style_context().add_class("ang-secondary")
        clear.connect("clicked", self._clear)
        save = Gtk.Button(label="Запази")
        save.get_style_context().add_class("ang-primary")
        save.connect("clicked", self._save)
        btns.add(clear)
        btns.add(save)
        card.attach(btns, 0, 3, 2, 1)

        root.pack_start(card, True, True, 0)
        self.content.add(root)
        self._mark()

    def _pick(self, w, c):
        self.color = c
        self._mark()

    def _mark(self):
        for b, c in self.swatches:
            ctx = b.get_style_context()
            (ctx.add_class if c == self.color else ctx.remove_class)("ang-swatch-active")

    def _save(self, *_):
        prof = self.combo.get_active_text()
        cmd = f"AMF_SET_SPOOL SLOT={self.slot} PROFILE={prof}"
        if self.color:
            cmd += f" COLOR={self.color}"
        self.gcode(cmd)
        self.back()

    def _clear(self, *_):
        self.gcode(f"AMF_CLEAR_SPOOL SLOT={self.slot}")
        self.back()
