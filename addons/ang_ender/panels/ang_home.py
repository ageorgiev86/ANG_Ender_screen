"""Начален екран: рендер на принтера, поздрав, карта „Файлове“, карта за състояние."""
import os

from gi.repository import GLib, Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import AMF_DEFAULT_SLOTS, CHAMBER_SENSOR


class Panel(AngPanel):
    def __init__(self, screen, title, items=None, **kwargs):
        super().__init__(screen, title or "ANG Ender")
        self.items = items or []
        self.latest_file = None
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.5))
        root.get_style_context().add_class("ang-home")

        hero = Gtk.Box(spacing=int(fs * 1.2), vexpand=True)
        self.render = ui.Render("printer_front", int(cw * 0.40), int(ch * 0.55), layers=["light"])
        hero.pack_start(self.render, False, False, 0)
        greet = Gtk.Box(spacing=int(fs * 0.7), valign=Gtk.Align.CENTER)
        bar = Gtk.Box()
        bar.get_style_context().add_class("ang-accent-bar")
        bar.set_size_request(max(3, int(fs * 0.2)), -1)
        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3))
        self.labels["greeting"] = ui.label("Готов за печат", "ang-greeting", wrap=True)
        self.labels["sub"] = ui.label("Да направим още един страхотен печат!", "ang-sub", wrap=True)
        text.add(self.labels["greeting"])
        text.add(self.labels["sub"])
        greet.pack_start(bar, False, False, 0)
        greet.pack_start(text, True, True, 0)
        hero.pack_start(greet, True, True, 0)
        root.pack_start(hero, True, True, 0)

        cards = Gtk.Box(spacing=int(fs * 0.6))
        cards.set_size_request(-1, int(ch * 0.38))

        files = Gtk.Button()
        files.get_style_context().add_class("ang-card")
        files.set_size_request(int(cw * 0.36), -1)
        files.connect("clicked", lambda *_: self.open("print"))
        fbox = Gtk.Box(spacing=int(fs * 0.6), halign=Gtk.Align.CENTER)
        self.labels["thumb"] = gtk.Image("file", fs * 3.2, fs * 3.2)
        fbox.pack_start(self.labels["thumb"], False, False, 0)
        ftext = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        ftext.add(ui.label("Файлове", "ang-card-title"))
        self.labels["file_hint"] = ui.label("за печат", "ang-sub")
        ftext.add(self.labels["file_hint"])
        fbox.pack_start(ftext, False, False, 0)
        files.add(fbox)
        cards.pack_start(files, False, False, 0)

        status = Gtk.Box(homogeneous=False, hexpand=True)
        status.get_style_context().add_class("ang-card")
        self._temps_cell(status)
        self._amf_cell(status)
        self._net_cell(status)
        cards.pack_start(status, True, True, 0)
        root.pack_start(cards, False, False, 0)

        self.content.add(root)
        self._find_latest_file()

    def _temps_cell(self, parent):
        """Един бутон с трите температури (дюза, легло, камера) -> Управление."""
        fs = self._gtk.font_size
        btn = Gtk.Button(hexpand=True, vexpand=True)
        btn.get_style_context().add_class("ang-cell")
        grid = Gtk.Grid(row_spacing=int(fs * 0.25), column_spacing=int(fs * 0.5), halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
        for row, (key, icon) in enumerate((("nozzle", "extruder"), ("bed", "bed"), ("chamber", "heater"))):
            grid.attach(self._gtk.Image(icon, fs * 1.1, fs * 1.1), 0, row, 1, 1)
            val = ui.label("--", "ang-cell-value", markup=True)
            grid.attach(val, 1, row, 1, 1)
            self.labels[key] = val
        btn.add(grid)
        btn.connect("clicked", lambda *_: self.open("ang_control"))
        parent.pack_start(btn, True, True, 0)

    def _net_cell(self, parent):
        """Връзка: Wi-Fi със сила на сигнала, кабел или „Няма връзка“ -> страница Мрежа."""
        fs = self._gtk.font_size
        btn = Gtk.Button(hexpand=True, vexpand=True)
        btn.get_style_context().add_class("ang-cell")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), valign=Gtk.Align.CENTER)
        self.net_icon = Gtk.Image(halign=Gtk.Align.CENTER)
        self.net_lbl = ui.label("Wi-Fi", "ang-caption", xalign=0.5)
        box.add(self.net_icon)
        box.add(self.net_lbl)
        btn.add(box)
        btn.connect("clicked", lambda *_: self.open("network"))
        parent.pack_start(btn, True, True, 0)
        self.net_btn = btn
        self._net_timer = None
        self._update_net()

    def _update_net(self):
        fs = self._gtk.font_size
        kind, q, name = ui.network_status()
        ctx = self.net_btn.get_style_context()
        if kind == "wifi":
            self.net_icon.set_from_pixbuf(self._gtk.PixbufFromIcon(ui.wifi_icon(q), fs * 1.8, fs * 1.8))
            self.net_lbl.set_text(name or "Wi-Fi")
            ctx.remove_class("ang-offline")
        elif kind == "eth":
            self.net_icon.set_from_pixbuf(self._gtk.PixbufFromIcon("network", fs * 1.8, fs * 1.8))
            self.net_lbl.set_text("Кабел")
            ctx.remove_class("ang-offline")
        else:
            self.net_icon.set_from_pixbuf(self._gtk.PixbufFromIcon("wifi_weak", fs * 1.8, fs * 1.8))
            self.net_lbl.set_text("Няма връзка")
            ctx.add_class("ang-offline")
        return True

    def _amf_cell(self, parent):
        fs = self._gtk.font_size
        btn = Gtk.Button(hexpand=True, vexpand=True)
        btn.get_style_context().add_class("ang-cell")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), valign=Gtk.Align.CENTER)
        box.add(ui.label("AMF", "ang-caption", xalign=0.5))
        pills = Gtk.Box(spacing=int(fs * 0.2), halign=Gtk.Align.CENTER)
        self.pills = []
        for _ in range(AMF_DEFAULT_SLOTS):
            sp = ui.Spool(int(fs * 1.1), int(fs * 2.2))
            pills.add(sp)
            self.pills.append(sp)
        box.add(pills)
        btn.add(box)
        btn.connect("clicked", lambda *_: self.open("ang_amf"))
        parent.pack_start(btn, True, True, 0)

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
        size = self._gtk.font_size * 3.2

        def set_thumb(pixbuf):
            if pixbuf is not None:
                self.labels["thumb"].set_from_pixbuf(pixbuf)

        self.load_image_async(self.latest_file, size, size, callback=set_thumb)

    def activate(self):
        self._find_latest_file()
        self.refresh()
        self._update_net()
        if self._net_timer is None:
            self._net_timer = GLib.timeout_add_seconds(10, self._update_net)

    def deactivate(self):
        if self._net_timer is not None:
            GLib.source_remove(self._net_timer)
            self._net_timer = None

    def refresh(self):
        self.labels["nozzle"].set_markup(self.temp_text("extruder"))
        self.labels["bed"].set_markup(self.temp_text("heater_bed"))
        t = self.stat(CHAMBER_SENSOR, "temperature")
        self.labels["chamber"].set_markup(ui.value_markup(f"{t:.0f}", "℃") if t is not None else "--")
        amf = self.stat("amf", "slots", {}) or {}
        active = self.stat("amf", "active_slot")
        for i, sp in enumerate(self.pills):
            s = amf.get(str(i))
            if not s or not s.get("filament"):
                sp.set_state(None)
            else:
                sp.set_state(ui.rgb_hex(s.get("color", "")), active=(active == i), unknown=not s.get("color"))

    def process_update(self, action, data):
        if action == "notify_status_update":
            self.refresh()
