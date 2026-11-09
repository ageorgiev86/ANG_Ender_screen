"""Табло „Управление“: карти вляво и горе, рендер в разрез вдясно, светлина."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import AIR_MODES, CHAMBER_SENSOR, LIGHT_OBJECT, LIGHT_OFF, LIGHT_ON


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Управление")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        sp = int(fs * 0.5)

        grid = Gtk.Grid(column_spacing=sp, row_spacing=sp)
        grid.get_style_context().add_class("ang-control")

        self.v = {}
        for key in ("air", "speed", "motion", "nozzle", "chamber", "bed"):
            self.v[key] = ui.label("--", "ang-value", markup=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=sp)
        left.set_size_request(int(cw * 0.36), -1)
        left.pack_start(ui.info_card(gtk, "fan", "Въздух", self.v["air"], cb=lambda *_: self.open("ang_air")), True, True, 0)
        left.pack_start(ui.info_card(gtk, "extruder", "Дюза и екструдер", self.v["nozzle"], cb=lambda *_: self.open("ang_nozzle")), True, True, 0)
        left.pack_start(ui.info_card(gtk, "heater", "Камера", self.v["chamber"], cb=lambda *_: self.open("ang_numpad", "Камера", device="chamber", render="printer_section")), True, True, 0)
        left.pack_start(ui.info_card(gtk, "bed", "Легло", self.v["bed"], cb=lambda *_: self.open("ang_numpad", "Легло", device="heater_bed", render="printer_bed")), True, True, 0)
        grid.attach(left, 0, 0, 1, 2)

        top = Gtk.Box(spacing=sp, homogeneous=True)
        top.add(ui.info_card(gtk, "speed+", "Скорост", self.v["speed"], cb=lambda *_: self.open("ang_speed")))
        top.add(ui.info_card(gtk, "move", "Движение", self.v["motion"], cb=lambda *_: self.open("ang_motion")))
        grid.attach(top, 1, 0, 1, 1)

        ov = Gtk.Overlay(hexpand=True, vexpand=True)
        self.render = ui.Render("printer_section", int(cw * 0.60), int(ch * 0.70), layers=["light"])
        ov.add(self.render)
        light = Gtk.Box(spacing=int(fs * 0.4), halign=Gtk.Align.END, valign=Gtk.Align.END)
        light.get_style_context().add_class("ang-pill")
        light.add(gtk.Image("light", fs * 1.2, fs * 1.2))
        light.add(ui.label("Светлина", "ang-caption-strong"))
        self.light = Gtk.Switch(valign=Gtk.Align.CENTER)
        self.light.connect("notify::active", self._light)
        light.add(self.light)
        ov.add_overlay(light)
        grid.attach(ov, 1, 1, 1, 1)

        self.content.add(grid)
        self.refresh()

    def _light(self, sw, _):
        on = sw.get_active()
        self.render.set_layer("light", on)
        if not self._updating:
            self.gcode(LIGHT_ON if on else LIGHT_OFF)

    _updating = False

    def refresh(self):
        self.v["nozzle"].set_markup(self.temp_text("extruder"))
        self.v["bed"].set_markup(self.temp_text("heater_bed"))
        t = self.stat(CHAMBER_SENSOR, "temperature")
        self.v["chamber"].set_markup(ui.value_markup(f"{t:.0f}", "℃") if t is not None else "--")
        speed = self.stat("gcode_move", "speed_factor", 1.0) or 1.0
        self.v["speed"].set_text(f"{speed * 100:.0f}%")
        homed = self.stat("toolhead", "homed_axes", "") or ""
        self.v["motion"].set_text(homed.upper() if homed else "Не е нулиран")
        mode = getattr(self._screen, "ang_air_mode", 0)
        self.v["air"].set_text(AIR_MODES[mode][0])
        val = self.stat(LIGHT_OBJECT, "value")
        if val is not None:
            self._updating = True
            self.light.set_active(val > 0)
            self._updating = False

    def activate(self):
        self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update":
            self.refresh()
