"""Въвеждане на температура: рендер вляво, numpad вдясно, „Потвърди“ горе."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import CHAMBER_HEATER

HINTS = {
    "heater_bed": "Леглото задържа зададената температура през целия печат, за да държи детайла.",
    "extruder": "Температурата зависи от материала. Виж профила на филамента.",
    "chamber": "Ниска температура в камерата е за PLA и PETG. Висока — за ABS, ASA, PC и PA.",
}


class Panel(AngPanel):
    def __init__(self, screen, title, device="extruder", render="toolhead", **kwargs):
        self.device = CHAMBER_HEATER if device == "chamber" else device
        self.key = device
        super().__init__(screen, title or "Температура")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header(self.title, self.back, ("Потвърди", self._confirm)))
        body = Gtk.Box(spacing=int(fs * 0.8), vexpand=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        left.pack_start(ui.Render(render, int(cw * 0.40), int(ch * 0.56)), True, True, 0)
        left.pack_start(ui.label(HINTS.get(device, ""), "ang-sub", wrap=True), False, False, 0)
        left.set_size_request(int(cw * 0.42), -1)
        body.pack_start(left, False, False, 0)

        self.pad = ui.Numpad(gtk)
        self.pad.set_hexpand(True)
        body.pack_start(self.pad, True, True, 0)
        root.pack_start(body, True, True, 0)
        self.content.add(root)

    def _confirm(self, *_):
        v = self.pad.value()
        if v is None:
            return
        name = self.device.split()[-1]
        self.gcode(f"SET_HEATER_TEMPERATURE HEATER={name} TARGET={v}")
        self.back()
