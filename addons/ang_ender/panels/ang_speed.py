"""Скорост: рендер вляво, 4 режима вдясно (M220)."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import SPEED_MODES


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Скорост")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header("Скорост", self.back))
        body = Gtk.Box(spacing=int(fs * 1.0), vexpand=True)
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        left.pack_start(ui.Render("toolhead_motion", int(cw * 0.44), int(ch * 0.62)), True, True, 0)
        left.pack_start(ui.label("Препоръчва се Стандарт. Спорт и Луд скъсяват печата, но може да влошат качеството.", "ang-sub", wrap=True), False, False, 0)
        left.set_size_request(int(cw * 0.46), -1)
        body.pack_start(left, False, False, 0)

        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.5), valign=Gtk.Align.CENTER, hexpand=True)
        self.btns = []
        for name, pct in SPEED_MODES:
            b = Gtk.Button(label=f"{name} ({pct}%)")
            b.get_style_context().add_class("ang-option")
            b.set_size_request(-1, int(fs * 2.6))
            b.connect("clicked", self._set, pct)
            col.add(b)
            self.btns.append((b, pct))
        body.pack_start(col, True, True, 0)
        root.pack_start(body, True, True, 0)
        self.content.add(root)
        self.refresh()

    def _set(self, w, pct):
        self.gcode(f"M220 S{pct}")
        self._mark(pct)

    def _mark(self, pct):
        for b, p in self.btns:
            ctx = b.get_style_context()
            (ctx.add_class if p == pct else ctx.remove_class)("ang-option-active")

    def refresh(self):
        f = self.stat("gcode_move", "speed_factor", 1.0) or 1.0
        self._mark(round(f * 100))

    def process_update(self, action, data):
        if action == "notify_status_update" and "gcode_move" in data:
            self.refresh()
