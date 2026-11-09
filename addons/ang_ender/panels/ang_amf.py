"""AMF: блок с макари в цвета на филамента, влажност, път до главата, меню при докосване.

Данни: printer.amf (amf.py) -> active_slot, slots{"0": {...}}, max_slots.
Команди: AMF_SELECT_SLOT, AMF_UNLOAD, AMF_SET_SPOOL, AMF_CLEAR_SPOOL, AMF_DRY_START/STOP.
"""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import AMF_DEFAULT_SLOTS

# Къде лежат макарите върху amf_unit.png: ляв/десен отстъп и горе/долу (относително 0..1).
# Нагласи ги, когато сложиш истинския рендер на корпуса.
SPOOL_AREA = (0.06, 0.20, 0.06, 0.16)  # left, right, top, bottom


class PathLines(Gtk.DrawingArea):
    """Линии от всеки слот към хъба и главата. Активният път е син."""

    def __init__(self, page):
        super().__init__()
        self.page = page
        self.connect("draw", self._draw)

    def _draw(self, w, cr):
        p = self.page
        if not p.spools or p.head.get_allocated_width() <= 1:
            return False

        def pos(widget, fx, fy):
            r = widget.translate_coordinates(p.root, widget.get_allocated_width() * fx, widget.get_allocated_height() * fy)
            return (r[0], r[1]) if r else (0, 0)

        hx, hy = pos(p.head, 0.5, 0.0)
        _, box_bottom = pos(p.unit_ov, 0, 1.0)
        hub_y = box_bottom + (hy - box_bottom) * 0.45
        cr.set_line_width(2)
        for i, sp in enumerate(p.spools):
            sx, _ = pos(sp, 0.5, 1.0)
            cr.set_source_rgba(*ui.ACCENT, 1) if p.active == i else cr.set_source_rgba(1, 1, 1, 0.18)
            cr.move_to(sx, box_bottom)
            cr.line_to(sx, hub_y)
            cr.line_to(hx, hub_y)
            cr.line_to(hx, hy)
            cr.stroke()
        ex, ey = pos(p.ext, 0.5, 1.0)
        cr.set_source_rgba(*ui.ACCENT, 1) if p.active == "ext" else cr.set_source_rgba(1, 1, 1, 0.18)
        cr.move_to(ex, ey + 22)
        cr.line_to(ex, hub_y + 10)
        cr.line_to(hx + 6, hub_y + 10)
        cr.line_to(hx + 6, hy)
        cr.stroke()
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.rectangle(hx - 14, hub_y - 6, 28, 12)
        cr.fill()
        return False


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "AMF")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        self.active = None
        n = int(self.stat("amf", "max_slots", AMF_DEFAULT_SLOTS) or AMF_DEFAULT_SLOTS)

        page = Gtk.Overlay()
        self.root = page
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.2))
        col.get_style_context().add_class("ang-amf")

        # материали над макарите
        top = Gtk.Box(spacing=int(fs * 1.0))
        unit_w, unit_h = int(cw * 0.62), int(ch * 0.50)
        self.mat_row = Gtk.Box(homogeneous=True)
        self.mat_row.set_size_request(unit_w, -1)
        self.mats = [ui.label("", "ang-caption", xalign=0.5) for _ in range(n)]
        for m in self.mats:
            self.mat_row.add(m)
        top.pack_start(self.mat_row, False, False, int(cw * 0.04))
        self.ext_mat = ui.label("", "ang-caption", xalign=0.5)
        top.pack_start(self.ext_mat, True, True, 0)
        col.add(top)

        # блокът: рендер на корпуса + макари отгоре
        row = Gtk.Box(spacing=int(fs * 1.0))
        self.unit_ov = Gtk.Overlay()
        self.unit_ov.add(ui.Render("amf_unit", unit_w, unit_h, compact=True))
        l, r, t, b = SPOOL_AREA
        spools_box = Gtk.Box(homogeneous=True, spacing=int(fs * 0.3))
        spools_box.set_margin_start(int(unit_w * l))
        spools_box.set_margin_end(int(unit_w * r))
        spools_box.set_margin_top(int(unit_h * t))
        spools_box.set_margin_bottom(int(unit_h * b))
        self.spools, self.spool_btns, self.names = [], [], []
        for i in range(n):
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            btn = Gtk.Button()
            btn.get_style_context().add_class("ang-flat")
            sp = ui.Spool(int(unit_w * 0.12), int(unit_h * 0.55))
            btn.add(sp)
            btn.connect("clicked", self._menu, i)
            v.pack_start(btn, True, True, 0)
            name = ui.label(f"A{i + 1}", "ang-slot-name", xalign=0.5)
            v.pack_start(name, False, False, 0)
            spools_box.add(v)
            self.spools.append(sp)
            self.spool_btns.append(btn)
            self.names.append(name)
        self.unit_ov.add_overlay(spools_box)
        # влажност вдясно в корпуса
        hum = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, halign=Gtk.Align.END, valign=Gtk.Align.CENTER)
        hum.set_margin_end(int(unit_w * 0.04))
        self.drop = ui.HumidityDrop(int(fs * 1.6), int(fs * 2.2))
        hum.add(self.drop)
        self.hum_lbl = ui.label("--", "ang-caption-strong", xalign=0.5, markup=True)
        hum.add(self.hum_lbl)
        self.unit_ov.add_overlay(hum)
        row.pack_start(self.unit_ov, False, False, int(cw * 0.04))

        # външна макара
        ext_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
        eb = Gtk.Button()
        eb.get_style_context().add_class("ang-flat")
        self.ext = ui.Spool(int(unit_w * 0.13), int(unit_h * 0.60))
        eb.add(self.ext)
        eb.connect("clicked", self._menu, "ext")
        ext_box.add(eb)
        ext_box.add(ui.label("Външна", "ang-slot-name", xalign=0.5))
        row.pack_start(ext_box, False, False, 0)
        col.add(row)

        # главата (тулхед) отдолу
        bottom = Gtk.Box(vexpand=True)
        self.head = ui.Render("toolhead_small", int(fs * 3.4), int(fs * 3.4), compact=True)
        self.head.set_valign(Gtk.Align.END)
        bottom.pack_start(self.head, False, False, int(cw * 0.04 + unit_w / 2 - fs * 1.7))
        actions = Gtk.Box(spacing=int(fs * 0.4), halign=Gtk.Align.END, valign=Gtk.Align.END, hexpand=True)
        dry = Gtk.Button(label="Сушене")
        dry.get_style_context().add_class("ang-secondary")
        dry.connect("clicked", lambda *_: self.open("ang_amf_dry", "Сушене и влажност", slot=0))
        actions.add(dry)
        bottom.pack_start(actions, True, True, 0)
        col.pack_start(bottom, True, True, 0)

        page.add(col)
        self.lines = PathLines(self)
        page.add_overlay(self.lines)
        page.set_overlay_pass_through(self.lines, True)
        self.content.add(page)
        self.refresh()

    # ---------- меню при докосване на макара ----------
    def _menu(self, btn, slot):
        pop = Gtk.Popover(relative_to=btn)
        pop.get_style_context().add_class("ang-popover")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        items = [("Редактирай", self._edit), ("Зареди", self._load), ("Извади", self._unload)]
        if slot != "ext":
            items.append(("Суши", self._dry))
        for text, cb in items:
            b = Gtk.Button(label=text)
            b.get_style_context().add_class("ang-menu-item")
            b.connect("clicked", lambda w, c=cb: (pop.popdown(), c(slot)))
            box.add(b)
        pop.add(box)
        box.show_all()
        pop.popup()
        self._last_popover = pop

    def _edit(self, slot):
        self.open("ang_amf_edit", "Редакция на филамент", slot=slot)

    def _load(self, slot):
        if slot == "ext":
            self.gcode("ANG_LOAD_EXTERNAL")
        else:
            self.gcode(f"AMF_SELECT_SLOT SLOT={slot}")

    def _unload(self, slot):
        self.gcode("AMF_UNLOAD")

    def _dry(self, slot):
        self.open("ang_amf_dry", "Сушене и влажност", slot=slot)

    # ---------- данни ----------
    def refresh(self):
        slots = self.stat("amf", "slots", {}) or {}
        self.active = self.stat("amf", "active_slot")
        hums = []
        for i, sp in enumerate(self.spools):
            s = slots.get(str(i)) or {}
            present = s.get("filament")
            color = s.get("color")
            sp.set_state(ui.rgb_hex(color) if present else None, active=(self.active == i), unknown=bool(present and not color))
            self.mats[i].set_text(s.get("profile") or ("?" if present else ""))
            ctx = self.names[i].get_style_context()
            (ctx.add_class if self.active == i else ctx.remove_class)("ang-slot-active")
            if s.get("humidity") is not None and s.get("online"):
                hums.append(s["humidity"])
        if hums:
            h = max(hums)
            self.drop.set_level(h)
            self.hum_lbl.set_markup(ui.value_markup(f"{h:.0f}", "%"))
        self.lines.queue_draw()

    def activate(self):
        self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update" and "amf" in data:
            self.refresh()
