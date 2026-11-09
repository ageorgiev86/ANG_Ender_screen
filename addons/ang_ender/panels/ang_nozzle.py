"""Дюза и екструдер: рендер на главата, бутони ▲/▼ за екструдера, температура на дюзата."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel

STEP_MM = 10
FEED = 300  # mm/min


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Дюза и екструдер")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header("Дюза и екструдер", self.back))
        body = Gtk.Box(spacing=int(fs * 1.2), vexpand=True)

        self.render = ui.Render("toolhead", int(cw * 0.42), int(ch * 0.80), layers=["heat"])
        body.pack_start(self.render, False, False, 0)

        ext = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.5), valign=Gtk.Align.CENTER)
        ext.add(ui.label("Екструдер", "ang-caption", xalign=0.5))
        up = Gtk.Button(label="▲")
        dn = Gtk.Button(label="▼")
        for b in (up, dn):
            b.get_style_context().add_class("ang-square")
            b.set_size_request(int(fs * 3.4), int(fs * 2.6))
        up.connect("clicked", lambda *_: self._extrude(-STEP_MM))
        dn.connect("clicked", lambda *_: self._extrude(STEP_MM))
        ext.add(up)
        ext.add(dn)
        ext.add(ui.label(f"{STEP_MM} mm", "ang-sub", xalign=0.5))
        body.pack_start(ext, False, False, 0)

        noz = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.5), valign=Gtk.Align.CENTER)
        noz.add(ui.label("Дюза", "ang-caption"))
        self.temp_btn = Gtk.Button()
        self.temp_btn.get_style_context().add_class("ang-field")
        self.temp_lbl = ui.label("--", "ang-value", xalign=0.5, markup=True)
        self.temp_btn.add(self.temp_lbl)
        self.temp_btn.set_size_request(int(fs * 7), int(fs * 2.4))
        self.temp_btn.connect("clicked", lambda *_: self.open("ang_numpad", "Температура на дюзата", device="extruder", render="toolhead"))
        noz.add(self.temp_btn)
        self.info = ui.label("Стандартна\nМесинг\n0.4 mm", "ang-sub", wrap=True)
        noz.add(self.info)
        body.pack_start(noz, True, True, 0)

        root.pack_start(body, True, True, 0)
        self.content.add(root)
        self.refresh()

    def _extrude(self, mm):
        self.gcode(f"M83\nG1 E{mm} F{FEED}")

    def refresh(self):
        self.temp_lbl.set_markup(self.temp_text("extruder"))
        tgt = self.stat("extruder", "target", 0) or 0
        self.render.set_layer("heat", tgt > 0)

    def process_update(self, action, data):
        if action == "notify_status_update" and "extruder" in data:
            self.refresh()
