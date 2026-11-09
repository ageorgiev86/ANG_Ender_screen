"""Сушене и влажност за слот: капка с влажността, материал, температура, време, Старт/Стоп."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel


class Panel(AngPanel):
    def __init__(self, screen, title, slot=0, **kwargs):
        super().__init__(screen, title or "Сушене и влажност")
        self.slot = slot
        gtk = self._gtk
        fs = gtk.font_size
        s = (self.stat("amf", "slots", {}) or {}).get(str(slot), {})

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header(f"Сушене и влажност · A{int(slot) + 1}", self.back))
        card = Gtk.Box(spacing=int(fs * 1.5), vexpand=True)
        card.get_style_context().add_class("ang-card")
        card.get_style_context().add_class("ang-pad")

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, spacing=int(fs * 0.3))
        drop = ui.HumidityDrop(int(fs * 5), int(fs * 6.5))
        hum = s.get("humidity")
        drop.set_level(hum)
        left.add(drop)
        left.add(ui.label(ui.value_markup(f"{hum:.0f}", "%") if hum is not None else "--", "ang-value", xalign=0.5, markup=True))
        t = s.get("temperature")
        left.add(ui.label(f"{t:.0f}℃" if t is not None else "", "ang-sub", xalign=0.5))
        card.pack_start(left, False, False, int(fs * 2))

        right = Gtk.Grid(row_spacing=int(fs * 0.6), column_spacing=int(fs * 0.6), valign=Gtk.Align.CENTER, hexpand=True)
        right.attach(ui.label("Настройки за сушене", "ang-caption-strong"), 0, 0, 3, 1)
        self.combo = Gtk.ComboBoxText()
        profiles = self.stat("amf", "profiles", []) or ["PLA", "PETG", "ABS", "TPU", "PC"]
        for p in profiles:
            self.combo.append_text(p)
        cur = s.get("profile")
        self.combo.set_active(profiles.index(cur) if cur in profiles else 0)
        right.attach(self.combo, 0, 1, 3, 1)
        self.temp = Gtk.SpinButton.new_with_range(25, 80, 5)
        self.temp.set_value(s.get("target_temp") or 55)
        self.hours = Gtk.SpinButton.new_with_range(1, 24, 1)
        self.hours.set_value(8)
        right.attach(self.temp, 0, 2, 1, 1)
        right.attach(ui.label("℃", "ang-sub"), 1, 2, 1, 1)
        right.attach(self.hours, 0, 3, 1, 1)
        right.attach(ui.label("часа", "ang-sub"), 1, 3, 1, 1)
        drying = s.get("drying")
        go = Gtk.Button(label="Стоп" if drying else "Старт", halign=Gtk.Align.START)
        go.get_style_context().add_class("ang-primary")
        go.connect("clicked", self._go, drying)
        right.attach(go, 0, 4, 2, 1)
        card.pack_start(right, True, True, 0)

        root.pack_start(card, True, True, 0)
        self.content.add(root)

    def _go(self, w, drying):
        if drying:
            self.gcode(f"AMF_DRY_STOP SLOT={self.slot}")
        else:
            minutes = int(self.hours.get_value() * 60)
            self.gcode(f"AMF_DRY_START SLOT={self.slot} TEMP={self.temp.get_value():.0f} TIME={minutes}")
        self.back()
