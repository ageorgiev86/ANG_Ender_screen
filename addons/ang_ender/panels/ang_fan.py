"""Един вентилатор: рендер на мястото му, вкл./изкл. и регулатор + / % / −."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import FANS

HINTS = {
    "part": "На главата, охлажда детайла.",
    "aux": "Отстрани в камерата, допълнително охлаждане.",
    "exhaust": "На задния панел, изкарва въздуха от камерата.",
    "heat": "Отдолу в камерата, разбърква топлия въздух.",
}


class Panel(AngPanel):
    def __init__(self, screen, title, fan="part", **kwargs):
        self.key = fan
        self.obj, name, layer = FANS[fan]
        super().__init__(screen, title or name)
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header(name, self.back))
        body = Gtk.Box(spacing=int(fs * 0.8), vexpand=True)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4), hexpand=True)
        self.render = ui.Render(f"{layer}_detail", int(cw * 0.62), int(ch * 0.66))
        left.pack_start(self.render, True, True, 0)
        left.pack_start(ui.label(HINTS.get(fan, ""), "ang-sub", wrap=True), False, False, 0)
        body.pack_start(left, True, True, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.6))
        right.set_size_request(int(fs * 6), -1)
        self.switch = Gtk.Switch(halign=Gtk.Align.CENTER)
        self.switch.connect("notify::active", self._toggle)
        right.pack_start(self.switch, False, False, 0)
        self.stepper = ui.Stepper(gtk, 0, 10, 0, 100, "%", on_change=self._set)
        right.pack_start(self.stepper, True, True, 0)
        body.pack_end(right, False, False, 0)

        root.pack_start(body, True, True, 0)
        self.content.add(root)
        self._busy = False
        self.refresh()

    def _cmd(self, pct):
        if self.obj == "fan":
            return f"M106 S{int(pct * 255 / 100)}"
        return f"SET_FAN_SPEED FAN={self.obj.split()[-1]} SPEED={pct / 100:.2f}"

    def _set(self, pct):
        self._busy = True
        self.switch.set_active(pct > 0)
        self._busy = False
        self.gcode(self._cmd(pct))

    def _toggle(self, sw, _):
        if self._busy:
            return
        pct = 100 if sw.get_active() else 0
        self.stepper.set_value(pct)
        self.gcode(self._cmd(pct))

    def refresh(self):
        speed = self.stat(self.obj, "speed")
        if speed is None:
            return
        self._busy = True
        self.stepper.set_value(round(speed * 100))
        self.switch.set_active(speed > 0)
        self._busy = False

    def process_update(self, action, data):
        if action == "notify_status_update" and self.obj in data:
            self.refresh()
