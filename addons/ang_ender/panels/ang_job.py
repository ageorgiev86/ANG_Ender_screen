"""Екран по време на печат (собствен дизайн; в архива на H2S такъв няма).

Голяма миниатюра вляво; вдясно име, прогрес, оставащо време, слой;
чипове с температури и скорост; долу Пауза / Спри / Настройки / AMF.
Засега НЕ замества стандартния job_status (виж OVERRIDES в __init__.py).
"""
import os
import time

from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import CHAMBER_SENSOR


def fmt_time(sec):
    if sec is None or sec < 0:
        return "--"
    h, m = int(sec // 3600), int(sec % 3600 // 60)
    return f"{h}ч {m:02d}м" if h else f"{m}м"


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Печат")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        sp = int(fs * 0.5)

        grid = Gtk.Grid(column_spacing=sp, row_spacing=sp)

        thumb_card = Gtk.Box()
        thumb_card.get_style_context().add_class("ang-card")
        thumb_card.set_size_request(int(cw * 0.40), int(ch * 0.66))
        self.thumb = gtk.Image("file", fs * 6, fs * 6)
        thumb_card.pack_start(self.thumb, True, True, 0)
        grid.attach(thumb_card, 0, 0, 1, 2)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.35), hexpand=True)
        info.get_style_context().add_class("ang-card")
        info.get_style_context().add_class("ang-pad")
        self.fname = ui.label("--", "ang-card-title")
        info.add(self.fname)
        self.state = ui.label("Печат", "ang-caption")
        info.add(self.state)
        prow = Gtk.Box(spacing=int(fs * 0.6))
        self.bar = Gtk.ProgressBar(hexpand=True, valign=Gtk.Align.CENTER)
        self.bar.get_style_context().add_class("ang-progress")
        prow.pack_start(self.bar, True, True, 0)
        self.pct = ui.label("0%", "ang-big", xalign=1.0, markup=True)
        prow.pack_end(self.pct, False, False, 0)
        info.add(prow)
        meta = Gtk.Box(homogeneous=True)
        self.left = self._meta(meta, "Остава")
        self.eta = self._meta(meta, "Край")
        self.layer = self._meta(meta, "Слой")
        info.add(meta)
        grid.attach(info, 1, 0, 1, 1)

        chips = Gtk.Grid(column_homogeneous=True, row_homogeneous=True, column_spacing=sp, row_spacing=sp)
        self.c = {}
        for i, (key, icon) in enumerate([("nozzle", "extruder"), ("bed", "bed"), ("chamber", "heater"), ("speed", "speed+")]):
            b = Gtk.Button()
            b.get_style_context().add_class("ang-card")
            r = Gtk.Box(spacing=int(fs * 0.5), halign=Gtk.Align.CENTER)
            r.add(gtk.Image(icon, fs * 1.4, fs * 1.4))
            v = ui.label("--", "ang-value", markup=True)
            r.add(v)
            b.add(r)
            self.c[key] = v
            chips.attach(b, i % 2, i // 2, 1, 1)
        grid.attach(chips, 1, 1, 1, 1)

        acts = Gtk.Box(spacing=sp, homogeneous=True)
        acts.set_size_request(-1, int(ch * 0.26))
        self.pause_btn = self._act(acts, "pause", "Пауза", self._pause)
        self._act(acts, "cancel", "Спри", lambda *_: self.gcode("CANCEL_PRINT"))
        self._act(acts, "fine-tune", "Настройки", lambda *_: self.open("fine_tune"))
        self._act(acts, "filament", "AMF", lambda *_: self.open("ang_amf"))
        grid.attach(acts, 0, 2, 2, 1)

        self.content.add(grid)
        self._file = None
        self.refresh()

    def _meta(self, parent, cap):
        b = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        b.add(ui.label(cap, "ang-caption"))
        v = ui.label("--", "ang-value")
        b.add(v)
        parent.add(b)
        return v

    def _act(self, parent, icon, text, cb):
        fs = self._gtk.font_size
        b = Gtk.Button()
        b.get_style_context().add_class("ang-card")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), valign=Gtk.Align.CENTER)
        box.add(self._gtk.Image(icon, fs * 1.8, fs * 1.8))
        box.add(ui.label(text, "ang-caption-strong", xalign=0.5))
        b.add(box)
        b.connect("clicked", cb)
        parent.add(b)
        return b

    def _pause(self, *_):
        st = self.stat("print_stats", "state", "")
        self.gcode("RESUME" if st == "paused" else "PAUSE")

    def refresh(self):
        fn = self.stat("print_stats", "filename", "") or ""
        if fn and fn != self._file:
            self._file = fn
            self.fname.set_text(os.path.splitext(os.path.basename(fn))[0])
            s = self._gtk.font_size * 9
            self.load_image_async(fn, s, s, callback=lambda pb: pb and self.thumb.set_from_pixbuf(pb))
        prog = self.stat("virtual_sdcard", "progress", 0.0) or 0.0
        self.bar.set_fraction(prog)
        self.pct.set_markup(ui.value_markup(f"{prog * 100:.0f}", "%"))
        st = self.stat("print_stats", "state", "") or ""
        self.state.set_text({"printing": "Печат…", "paused": "Пауза", "complete": "Готово", "cancelled": "Спрян", "error": "Грешка"}.get(st, st))
        el = self.stat("print_stats", "print_duration", 0) or 0
        left = el / prog - el if prog > 0.01 else None
        self.left.set_text(fmt_time(left))
        self.eta.set_text(time.strftime("%H:%M", time.localtime(time.time() + left)) if left else "--")
        info = self.stat("print_stats", "info", {}) or {}
        cl, tl = info.get("current_layer"), info.get("total_layer")
        self.layer.set_text(f"{cl} / {tl}" if cl is not None and tl else "--")
        self.c["nozzle"].set_markup(self.temp_text("extruder"))
        self.c["bed"].set_markup(self.temp_text("heater_bed"))
        t = self.stat(CHAMBER_SENSOR, "temperature")
        self.c["chamber"].set_markup(ui.value_markup(f"{t:.0f}", "℃") if t is not None else "--")
        f = self.stat("gcode_move", "speed_factor", 1.0) or 1.0
        self.c["speed"].set_markup(ui.value_markup(f"{f * 100:.0f}", "%"))

    def process_update(self, action, data):
        if action == "notify_status_update":
            self.refresh()
