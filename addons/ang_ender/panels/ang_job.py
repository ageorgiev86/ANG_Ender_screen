"""Екран по време на печат по подредбата на Bambu Lab H2S. Замества стандартния job_status.

    ┌──────────────────────┬───────────────────────────────┐
    │ ●REC        Файлове ›│  [рендер в разрез]  │  [глава] │
    │     миниатюра        │   (30℃ камера)      │          │
    │     на модела        │   (46℃ легло)       │ (158℃)   │
    │ benchy_PETG          │                     │          │
    ├──────────────────────┴──────┬──────┬──────┬────┬─────┤
    │ 37%            42/120 | -1ч │Пропус│Пауза │Спри│ ⚙   │
    │ ███████░░░░░░░░░░░░░        │  ни  │      │ ■  │     │
    │ Печат…                      │      │      │    │     │
    └─────────────────────────────┴──────┴──────┴────┴─────┘

Температурите са етикети върху рендерите; позициите им са в TAGS.
Състояния от print_stats.state: printing, paused, complete, cancelled, error, standby.
При край бутоните стават „Отново“ и „Готово“ (затваря към началния екран).
"""
import logging
import os
import time

from gi.repository import Gtk, Pango

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import CHAMBER_SENSOR

# Къде стоят етикетите с температури (относително 0..1 върху рендера).
# Нагласи ги, когато сложиш истинските printer_section.png и toolhead.png.
TAGS = {
    "chamber": ("printer_section", 0.30, 0.22),
    "bed": ("printer_section", 0.55, 0.62),
    "nozzle": ("toolhead", 0.50, 0.82),
}

STATE_TEXT = {
    "printing": "Печат",
    "paused": "Пауза",
    "complete": "Готово",
    "cancelled": "Спрян",
    "cancelling": "Спиране…",
    "error": "Грешка",
    "standby": "Готов",
}


def fmt_time(sec):
    if sec is None or sec < 0:
        return "--"
    h, m = int(sec // 3600), int(sec % 3600 // 60)
    return f"{h}ч {m:02d}м" if h else f"{m}м"


class TagRender(Gtk.Overlay):
    """Рендер с етикети отгоре, поставени на относителни позиции."""

    def __init__(self, render):
        super().__init__()
        self.render = render
        self.add(render)
        self.tags = []
        render.connect("size-allocate", self._place)

    def add_tag(self, widget, rx, ry):
        widget.set_halign(Gtk.Align.START)
        widget.set_valign(Gtk.Align.START)
        self.add_overlay(widget)
        self.tags.append((widget, rx, ry))

    def _place(self, render, alloc):
        for w, rx, ry in self.tags:
            tw, th = w.get_preferred_width()[1], w.get_preferred_height()[1]
            w.set_margin_start(max(0, int(alloc.width * rx - tw / 2)))
            w.set_margin_top(max(0, int(alloc.height * ry - th / 2)))


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Печат")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        sp = int(fs * 0.5)
        self.state = None
        self.filename = None
        self.meta = {}

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=sp)

        # ---------- горе вляво: модел ----------
        top = Gtk.Box(spacing=sp, vexpand=True)
        model = Gtk.Overlay()
        mcard = Gtk.Box()
        mcard.get_style_context().add_class("ang-card")
        mcard.set_size_request(int(cw * 0.38), int(ch * 0.62))
        self.thumb_size = int(ch * 0.46)
        self.thumb = gtk.Image("file", fs * 5, fs * 5)
        mcard.pack_start(self.thumb, True, True, 0)
        model.add(mcard)
        files = Gtk.Button(label="Файлове ›", halign=Gtk.Align.END, valign=Gtk.Align.START)
        files.get_style_context().add_class("ang-link")
        files.connect("clicked", lambda *_: self.open("gcodes"))
        model.add_overlay(files)
        self.fname = ui.label("--", "ang-caption-strong")
        self.fname.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self.fname.set_halign(Gtk.Align.FILL)
        self.fname.set_valign(Gtk.Align.END)
        self.fname.get_style_context().add_class("ang-thumb-name")
        model.add_overlay(self.fname)
        top.pack_start(model, False, False, 0)

        # ---------- горе вдясно: принтер и глава с температури ----------
        pcard = Gtk.Box(spacing=sp, hexpand=True)
        pcard.get_style_context().add_class("ang-card")
        pcard.get_style_context().add_class("ang-pad")
        self.tag = {}
        renders = {}
        for name, w, h in (("printer_section", cw * 0.26, ch * 0.56), ("toolhead", cw * 0.13, ch * 0.56)):
            renders[name] = TagRender(ui.Render(name, int(w), int(h), layers=["heat"] if name == "toolhead" else [], compact=True))
        for key, (rname, rx, ry) in TAGS.items():
            b = Gtk.Button()
            b.get_style_context().add_class("ang-temp-tag")
            row = Gtk.Box(spacing=int(fs * 0.25))
            row.add(gtk.Image({"chamber": "heater", "bed": "bed", "nozzle": "extruder"}[key], fs * 0.9, fs * 0.9))
            lbl = ui.label("--", "ang-tag-value", markup=True)
            row.add(lbl)
            b.add(row)
            dev, title, render = {
                "chamber": ("chamber", "Камера", "printer_section"),
                "bed": ("heater_bed", "Легло", "printer_bed"),
                "nozzle": ("extruder", "Температура на дюзата", "toolhead"),
            }[key]
            b.connect("clicked", lambda w, d=dev, t=title, r=render: self.open("ang_numpad", t, device=d, render=r))
            renders[rname].add_tag(b, rx, ry)
            self.tag[key] = lbl
        self.head_render = renders["toolhead"].render
        pcard.pack_start(renders["printer_section"], True, True, 0)
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        pcard.pack_start(sep, False, False, 0)
        pcard.pack_start(renders["toolhead"], False, False, 0)
        top.pack_start(pcard, True, True, 0)
        root.pack_start(top, True, True, 0)

        # ---------- долу: прогрес + бутони ----------
        bottom = Gtk.Box(spacing=sp)
        bottom.set_size_request(-1, int(ch * 0.30))
        prog = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), hexpand=True)
        prog.get_style_context().add_class("ang-card")
        prog.get_style_context().add_class("ang-pad")
        prow = Gtk.Box(spacing=sp)
        self.pct = ui.label("0%", "ang-job-pct", markup=True)
        prow.pack_start(self.pct, False, False, 0)
        self.meta_lbl = ui.label("", "ang-caption", xalign=1.0)
        prow.pack_end(self.meta_lbl, False, False, 0)
        prog.add(prow)
        self.bar = Gtk.ProgressBar(hexpand=True)
        self.bar.get_style_context().add_class("ang-progress")
        prog.add(self.bar)
        self.state_lbl = ui.label("Печат", "ang-job-state")
        prog.add(self.state_lbl)
        bottom.pack_start(prog, True, True, 0)

        self.btn_box = Gtk.Box(spacing=sp)
        self.btn_box.get_style_context().add_class("ang-card")
        self.btn_box.get_style_context().add_class("ang-btn-group")
        bottom.pack_start(self.btn_box, False, False, 0)

        tune = Gtk.Button()
        tune.get_style_context().add_class("ang-card")
        tune.set_image(gtk.Image("fine-tune", fs * 1.6, fs * 1.6))
        tune.set_always_show_image(True)
        tune.set_size_request(int(fs * 3.0), -1)
        tune.connect("clicked", lambda *_: self.open("fine_tune"))
        bottom.pack_start(tune, False, False, 0)
        root.pack_start(bottom, False, False, 0)

        self.buttons = {
            "skip": self._square("refresh", "Пропусни", lambda *_: self.open("exclude")),
            "pause": self._square("pause", "Пауза", self._pause),
            "resume": self._square("resume", "Продължи", self._resume),
            "cancel": self._square("stop", "Спри", self._cancel, danger=True),
            "again": self._square("refresh", "Отново", self._again),
            "done": self._square("complete", "Готово", self._close, primary=True),
        }

        self.content.add(root)
        self._set_state("printing")

    # ---------- бутони ----------
    def _square(self, icon, text, cb, danger=False, primary=False):
        fs = self._gtk.font_size
        b = Gtk.Button()
        b.get_style_context().add_class("ang-square-btn")
        if danger:
            b.get_style_context().add_class("ang-danger")
        if primary:
            b.get_style_context().add_class("ang-square-primary")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.2), valign=Gtk.Align.CENTER)
        if danger:
            stop = Gtk.Box(halign=Gtk.Align.CENTER)
            stop.get_style_context().add_class("ang-stop-square")
            stop.set_size_request(int(fs * 1.2), int(fs * 1.2))
            box.add(stop)
        else:
            box.add(self._gtk.Image(icon, fs * 1.4, fs * 1.4))
        box.add(ui.label(text, "ang-caption", xalign=0.5))
        b.add(box)
        b.set_size_request(int(fs * 3.6), -1)
        b.connect("clicked", cb)
        return b

    def _show_buttons(self, *names):
        for c in self.btn_box.get_children():
            self.btn_box.remove(c)
        for n in names:
            self.btn_box.add(self.buttons[n])
        self.btn_box.show_all()

    # ---------- действия ----------
    def _pause(self, *_):
        self._screen._send_action(None, "printer.print.pause", {})

    def _resume(self, *_):
        self._screen._send_action(None, "printer.print.resume", {})

    def _cancel(self, *_):
        buttons = [
            {"name": "Спри печата", "response": Gtk.ResponseType.OK, "style": "dialog-error"},
            {"name": "Назад", "response": Gtk.ResponseType.CANCEL, "style": "dialog-info"},
        ]
        objects = self.stat("exclude_object", "objects", []) or []
        if len(objects) > 1:
            buttons.insert(0, {"name": "Изключи обект", "response": Gtk.ResponseType.APPLY})
        lbl = Gtk.Label(label="Сигурен ли си, че искаш да спреш печата?", hexpand=True, vexpand=True, wrap=True)
        self._gtk.Dialog("Спиране", buttons, lbl, self._cancel_confirm)

    def _cancel_confirm(self, dialog, response):
        self._gtk.remove_dialog(dialog)
        if response == Gtk.ResponseType.APPLY:
            self.open("exclude")
        elif response == Gtk.ResponseType.OK:
            self._set_state("cancelling")
            self._screen._ws.api.print_cancel()

    def _again(self, *_):
        if not self.filename:
            return
        if self.state == "error":
            self._screen._ws.api.gcode_script("SDCARD_RESET_FILE")
        self._screen._ws.api.print_start(self.filename)
        if "virtual_sdcard" in self._printer.data:
            self._printer.data["virtual_sdcard"]["progress"] = 0
        self._set_state("printing")

    def _close(self, *_):
        # връща към началния екран (същото като „Main Menu“ в стандартния екран)
        self._screen.state_ready(wait=False)

    # ---------- състояние ----------
    def _set_state(self, state):
        if state == "standby" and self.state in ("cancelled", "cancelling"):
            state = "cancelled"
        if state == self.state:
            return
        logging.info(f"ang_job: {self.state} -> {state}")
        self.state = state
        text = STATE_TEXT.get(state, state)
        self.state_lbl.set_text(("✓ " if state == "complete" else "") + text)
        ctx = self.state_lbl.get_style_context()
        for c in ("ang-job-ok", "ang-job-err", "ang-job-paused"):
            ctx.remove_class(c)
        if state == "complete":
            ctx.add_class("ang-job-ok")
        elif state in ("error", "cancelled"):
            ctx.add_class("ang-job-err")
        elif state == "paused":
            ctx.add_class("ang-job-paused")
        try:
            self._screen.set_panel_title(text)
        except Exception:
            pass
        if state == "printing":
            self._show_buttons("skip", "pause", "cancel")
        elif state == "paused":
            self._show_buttons("skip", "resume", "cancel")
        elif state == "cancelling":
            self._show_buttons()
        else:
            self._show_buttons("again", "done")

    def _load_file(self, fn):
        self.filename = fn
        self.fname.set_text(os.path.splitext(os.path.basename(fn))[0])
        self.meta = self._files.get_file_info(fn) if self._files else {}
        size = int(self.thumb_size * 0.9)

        def set_thumb(pb):
            if pb is not None:
                self.thumb.set_from_pixbuf(pb)
            return False

        self.load_image_async(fn, size, size, callback=set_thumb)

    # ---------- данни ----------
    def refresh(self):
        ps_state = self.stat("print_stats", "state")
        if ps_state:
            self._set_state(ps_state)
        fn = self.stat("print_stats", "filename", "") or ""
        if fn and fn != self.filename:
            self._load_file(fn)
        elif fn and not self.meta and self._files:
            self.meta = self._files.get_file_info(fn)

        prog = self.stat("virtual_sdcard", "progress", 0.0) or 0.0
        if self.state == "complete":
            prog = 1.0
        self.bar.set_fraction(prog)
        self.pct.set_markup(ui.value_markup(f"{int(prog * 100)}", "%"))

        info = self.stat("print_stats", "info", {}) or {}
        cl, tl = info.get("current_layer"), info.get("total_layer")
        layer = f"{cl}/{tl}" if cl is not None and tl else ""

        dur = self.stat("print_stats", "print_duration", 0) or 0
        slicer = (self.meta or {}).get("estimated_time") or 0
        if self.state in ("complete", "cancelled", "error"):
            total = self.stat("print_stats", "total_duration", dur) or dur
            self.meta_lbl.set_text(" | ".join(x for x in (layer, fmt_time(total)) if x))
        else:
            if slicer:
                left = max(slicer - dur, 0)
            elif prog > 0.01:
                left = dur / prog - dur
            else:
                left = None
            eta = time.strftime("%H:%M", time.localtime(time.time() + left)) if left else ""
            parts = [layer, f"-{fmt_time(left)}" if left is not None else "", eta]
            self.meta_lbl.set_text(" | ".join(x for x in parts if x))

        # съобщение под прогреса: M117 от слайсера/макросите или състоянието
        msg = self.stat("display_status", "message") or ""
        text = STATE_TEXT.get(self.state, self.state or "")
        if self.state == "printing" and msg:
            text = msg
        self.state_lbl.set_text(("✓ " if self.state == "complete" else "") + text)

        # върху рендерите само текущата температура, както при Bambu
        for key, obj in (("nozzle", "extruder"), ("bed", "heater_bed"), ("chamber", CHAMBER_SENSOR)):
            t = self.stat(obj, "temperature")
            self.tag[key].set_markup(ui.value_markup(f"{t:.0f}", "℃") if t is not None else "--")
        self.head_render.set_layer("heat", (self.stat("extruder", "target", 0) or 0) > 0)

    def activate(self):
        self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update":
            self.refresh()
        elif action == "notify_metadata_update" and data.get("filename") == self.filename:
            self.meta = self._files.get_file_info(self.filename)
