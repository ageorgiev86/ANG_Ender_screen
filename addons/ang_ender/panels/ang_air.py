"""Въздух: режим (охлаждане/нагряване) и вентилаторите, свързани с линии към рендера."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import AIR_MODES, CHAMBER_SENSOR, FANS

# Къде е всеки вентилатор върху printer_section.png (относително 0..1).
# Нагласи ги, когато сложиш истинския рендер.
POINTS = {
    "part": (0.42, 0.28),
    "chamber": (0.80, 0.45),
    "aux": (0.25, 0.62),
    "exhaust": (0.82, 0.30),
    "heat": (0.82, 0.70),
    "_temp": (0.55, 0.85),  # температура на камерата
}


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Въздух")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header("Въздух: режими и вентилатори" if AIR_MODES else "Въздух и вентилатори", self.back))

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), vexpand=True)
        card.get_style_context().add_class("ang-card")
        card.get_style_context().add_class("ang-pad")

        seg = Gtk.Box(halign=Gtk.Align.START, no_show_all=not AIR_MODES)
        seg.get_style_context().add_class("ang-segment")
        self.mode_btns = []
        for i, (name, macro) in enumerate(AIR_MODES):
            b = Gtk.Button(label=name)
            b.get_style_context().add_class("ang-seg-btn")
            b.connect("clicked", self._mode, i)
            seg.add(b)
            self.mode_btns.append(b)
        card.add(seg)

        ov = Gtk.Overlay(vexpand=True)
        cols = Gtk.Box(spacing=int(fs * 0.8))
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=int(fs * 1.6))
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=int(fs * 0.9))
        left.set_size_request(int(cw * 0.22), -1)
        right.set_size_request(int(cw * 0.22), -1)
        self.render = ui.Render("printer_section", int(cw * 0.38), int(ch * 0.66), layers=[f[2] for f in FANS.values()])
        cols.pack_start(left, False, False, int(fs * 0.4))
        cols.pack_start(self.render, True, True, 0)
        cols.pack_start(right, False, False, int(fs * 0.4))
        ov.add(cols)
        self.leaders = ui.Leaders(ov, self.render)
        ov.add_overlay(self.leaders)
        ov.set_overlay_pass_through(self.leaders, True)

        self.vals = {}
        # вентилаторите от config.FANS се редуват вляво/вдясно; температурата е вдясно
        for i, (key, (obj, name, layer)) in enumerate(FANS.items()):
            side = left if i % 2 == 0 else right
            w = self._fan_label(name, key)
            side.add(w)
            self.leaders.link(*POINTS.get(key, (0.5, 0.5)), w, "left" if side is left else "right")
        w = self._fan_label("Камера", None)
        right.add(w)
        self.leaders.link(*POINTS["_temp"], w, "right")

        card.pack_start(ov, True, True, 0)
        root.pack_start(card, True, True, 0)
        self.content.add(root)
        self.refresh()

    def _fan_label(self, name, key):
        btn = Gtk.Button()
        btn.get_style_context().add_class("ang-flat")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        box.add(ui.label(f"{name}  ›", "ang-caption"))
        v = ui.label("--", "ang-value", markup=True)
        box.add(v)
        btn.add(box)
        if key:
            btn.connect("clicked", lambda *_: self.open("ang_fan", FANS[key][1], fan=key))
        else:
            btn.connect("clicked", lambda *_: self.open("ang_numpad", "Камера", device="chamber", render="printer_section"))
        self.vals[key or "_temp"] = v
        return btn

    def _mode(self, w, i):
        self._screen.ang_air_mode = i
        self.gcode(AIR_MODES[i][1])
        self.refresh()

    def refresh(self):
        mode = getattr(self._screen, "ang_air_mode", 0)
        for i, b in enumerate(self.mode_btns):
            ctx = b.get_style_context()
            (ctx.add_class if i == mode else ctx.remove_class)("ang-seg-active")
            b.set_label(AIR_MODES[i][0] + ("  ✓" if i == mode else ""))
        for key, (obj, name, layer) in FANS.items():
            speed = self.stat(obj, "speed")
            if speed is None:
                self.vals[key].set_text("--")
                self.render.set_layer(layer, False)
            elif speed <= 0:
                self.vals[key].set_text("ИЗКЛ.")
                self.render.set_layer(layer, False)
            else:
                self.vals[key].set_markup(ui.value_markup(f"{speed * 100:.0f}", "%"))
                self.render.set_layer(layer, True)
        self.vals["_temp"].set_markup(self.temp_text(CHAMBER_SENSOR))
        self.leaders.queue_draw()

    def activate(self):
        self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update":
            self.refresh()
