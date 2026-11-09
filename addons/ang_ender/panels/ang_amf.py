"""AMF: макари в цвета на филамента, влажност и сушене на всеки слот, път до главата.

Слотовете са отделни модули и се добавят; показват се по SLOTS_PER_PAGE на
страница с табове горе (1–4, 5–8 …).

Данни: printer.amf (amf.py) -> active_slot, slots{"0": {...}}, max_slots.
Команди: AMF_SELECT_SLOT, AMF_UNLOAD, AMF_SET_SPOOL, AMF_CLEAR_SPOOL, AMF_DRY_START/STOP.
"""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import AMF_DEFAULT_SLOTS

# Къде лежат макарите върху amf_unit.png: ляв/десен отстъп и горе/долу (относително 0..1).
# Нагласи ги, когато сложиш истинския рендер на корпуса.
SLOTS_PER_PAGE = 4
HUMIDITY_WARN = 30  # % — над това влажността се оцветява в оранжево

SPOOL_AREA = (0.06, 0.06, 0.06, 0.16)  # left, right, top, bottom


class PathLines(Gtk.DrawingArea):
    """Линии от всеки видим слот към хъба и главата. Активният път е син."""

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
        _, box_bottom = pos(p.info_row, 0, 1.0)
        hub_y = box_bottom + (hy - box_bottom) * 0.45
        cr.set_line_width(2)
        for sid, sp in zip(p.slot_ids, p.spools):
            sx, _ = pos(sp, 0.5, 1.0)
            if p.active == sid:
                cr.set_source_rgba(*ui.ACCENT, 1)
            else:
                cr.set_source_rgba(1, 1, 1, 0.18)
            cr.move_to(sx, box_bottom)
            cr.line_to(sx, hub_y)
            cr.line_to(hx, hub_y)
            cr.line_to(hx, hy)
            cr.stroke()
        # активният слот е на друга страница: синя линия от хъба надолу
        if isinstance(p.active, int) and p.active not in p.slot_ids:
            cr.set_source_rgba(*ui.ACCENT, 1)
            cr.move_to(hx, hub_y)
            cr.line_to(hx, hy)
            cr.stroke()
        cr.set_source_rgb(0.3, 0.3, 0.3)
        cr.rectangle(hx - 14, hub_y - 6, 28, 12)
        cr.fill()
        return False


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "AMF")
        gtk = self._gtk
        fs = self.fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        self.active = None
        self.n = int(self.stat("amf", "max_slots", AMF_DEFAULT_SLOTS) or AMF_DEFAULT_SLOTS)
        self.page_idx = 0
        self.unit_w, self.unit_h = int(cw * 0.66), int(ch * 0.48)

        root = Gtk.Overlay()
        self.root = root
        col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.2))
        col.get_style_context().add_class("ang-amf")

        # табове, ако слотовете са повече от един екран
        self.tabs = []
        pages = (self.n + SLOTS_PER_PAGE - 1) // SLOTS_PER_PAGE
        if pages > 1:
            seg = Gtk.Box(halign=Gtk.Align.START)
            seg.get_style_context().add_class("ang-segment")
            for pg in range(pages):
                a, b = pg * SLOTS_PER_PAGE + 1, min(self.n, (pg + 1) * SLOTS_PER_PAGE)
                t = Gtk.Button(label=f"{a}–{b}")
                t.get_style_context().add_class("ang-seg-btn")
                t.connect("clicked", self._goto, pg)
                seg.add(t)
                self.tabs.append(t)
            col.add(seg)

        # материали / блок с макари / влажност и сушене — пълнят се от _build_page
        self.mat_row = Gtk.Box(homogeneous=True)
        self.unit_ov = Gtk.Overlay()
        self.unit_ov.add(ui.Render("amf_unit", self.unit_w, self.unit_h, compact=True))
        self.spools_box = Gtk.Box(homogeneous=True, spacing=int(fs * 0.3))
        l, r, t, b = SPOOL_AREA
        self.spools_box.set_margin_start(int(self.unit_w * l))
        self.spools_box.set_margin_end(int(self.unit_w * r))
        self.spools_box.set_margin_top(int(self.unit_h * t))
        self.spools_box.set_margin_bottom(int(self.unit_h * b))
        self.unit_ov.add_overlay(self.spools_box)
        self.info_row = Gtk.Box(homogeneous=True, spacing=int(fs * 0.3))
        for box in (self.mat_row, self.info_row):
            box.set_margin_start(int(self.unit_w * l))
            box.set_margin_end(int(self.unit_w * r))

        unit_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.2), halign=Gtk.Align.CENTER)
        unit_col.add(self.mat_row)
        unit_col.add(self.unit_ov)
        unit_col.add(self.info_row)
        col.add(unit_col)

        # главата (тулхед) отдолу, под средата на блока
        bottom = Gtk.Overlay(vexpand=True)
        self.head = ui.Render("toolhead_small", int(fs * 3.4), int(fs * 3.4), compact=True)
        self.head.set_valign(Gtk.Align.END)
        self.head.set_halign(Gtk.Align.CENTER)
        bottom.add(self.head)
        dry = Gtk.Button(label="Сушене", halign=Gtk.Align.END, valign=Gtk.Align.END)
        dry.get_style_context().add_class("ang-secondary")
        dry.connect("clicked", lambda *_: self._dry(self.active if isinstance(self.active, int) else self.slot_ids[0]))
        bottom.add_overlay(dry)
        col.pack_start(bottom, True, True, 0)

        root.add(col)
        self.lines = PathLines(self)
        root.add_overlay(self.lines)
        root.set_overlay_pass_through(self.lines, True)
        self.content.add(root)

        active = self.stat("amf", "active_slot")
        if isinstance(active, int) and active < self.n:
            self.page_idx = active // SLOTS_PER_PAGE
        self._build_page()

    # ---------- страници ----------
    def _goto(self, w, pg):
        if pg != self.page_idx:
            self.page_idx = pg
            self._build_page()

    def _build_page(self):
        fs = self.fs
        for box in (self.mat_row, self.spools_box, self.info_row):
            for c in box.get_children():
                box.remove(c)
        first = self.page_idx * SLOTS_PER_PAGE
        self.slot_ids = list(range(first, min(self.n, first + SLOTS_PER_PAGE)))
        self.spools, self.names, self.mats = [], [], []
        self.drops, self.hum_lbls, self.dry_lbls = [], [], []
        # празни места, за да е същата ширина на макарите и на последната непълна страница
        for k in range(SLOTS_PER_PAGE):
            sid = self.slot_ids[k] if k < len(self.slot_ids) else None
            m = ui.label("", "ang-caption", xalign=0.5)
            self.mat_row.add(m)
            v = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            cell = Gtk.Button()
            cell.get_style_context().add_class("ang-slot-info")
            if sid is None:
                self.spools_box.add(v)
                self.info_row.add(cell)
                continue
            btn = Gtk.Button()
            btn.get_style_context().add_class("ang-flat")
            sp = ui.Spool(int(self.unit_w * 0.12), int(self.unit_h * 0.55))
            btn.add(sp)
            btn.connect("clicked", self._menu, sid)
            v.pack_start(btn, True, True, 0)
            name = ui.label(str(sid + 1), "ang-slot-name", xalign=0.5)
            v.pack_start(name, False, False, 0)
            self.spools_box.add(v)

            cv = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            hrow = Gtk.Box(spacing=int(fs * 0.2), halign=Gtk.Align.CENTER)
            drop = ui.HumidityDrop(int(fs * 0.8), int(fs * 1.1))
            hl = ui.label("--", "ang-caption-strong", markup=True)
            hrow.add(drop)
            hrow.add(hl)
            cv.add(hrow)
            dl = ui.label("", "ang-drying", xalign=0.5)
            cv.add(dl)
            cell.add(cv)
            cell.connect("clicked", lambda w, k=sid: self._dry(k))
            self.info_row.add(cell)

            self.spools.append(sp)
            self.names.append(name)
            self.mats.append(m)
            self.drops.append(drop)
            self.hum_lbls.append(hl)
            self.dry_lbls.append(dl)
        for i, t in enumerate(self.tabs):
            ctx = t.get_style_context()
            (ctx.add_class if i == self.page_idx else ctx.remove_class)("ang-seg-active")
        self.root.show_all()
        self.refresh()

    # ---------- меню при докосване на макара ----------
    def _menu(self, btn, slot):
        pop = Gtk.Popover(relative_to=btn)
        pop.get_style_context().add_class("ang-popover")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        for text, cb in (("Редактирай", self._edit), ("Зареди", self._load), ("Извади", self._unload), ("Суши", self._dry)):
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
        self.gcode(f"AMF_SELECT_SLOT SLOT={slot}")

    def _unload(self, slot):
        self.gcode("AMF_UNLOAD")

    def _dry(self, slot):
        self.open("ang_amf_dry", "Сушене и влажност", slot=slot)

    # ---------- данни ----------
    def refresh(self):
        slots = self.stat("amf", "slots", {}) or {}
        self.active = self.stat("amf", "active_slot")
        for k, sid in enumerate(self.slot_ids):
            s = slots.get(str(sid)) or {}
            present = s.get("filament")
            color = s.get("color")
            self.spools[k].set_state(ui.rgb_hex(color) if present else None, active=(self.active == sid), unknown=bool(present and not color))
            self.mats[k].set_text(s.get("profile") or ("?" if present else ""))
            ctx = self.names[k].get_style_context()
            (ctx.add_class if self.active == sid else ctx.remove_class)("ang-slot-active")
            h = s.get("humidity") if s.get("online", True) else None
            self.drops[k].set_level(h)
            self.hum_lbls[k].set_markup(ui.value_markup(f"{h:.0f}", "%") if h is not None else "--")
            dctx = self.hum_lbls[k].get_style_context()
            (dctx.add_class if h is not None and h >= HUMIDITY_WARN else dctx.remove_class)("ang-humid")
            if s.get("drying"):
                t, tg = s.get("temperature"), s.get("target_temp")
                self.dry_lbls[k].set_text(f"♨ {t:.0f}/{tg:.0f}℃" if t is not None and tg else "♨ суши")
            else:
                self.dry_lbls[k].set_text("")
        self.lines.queue_draw()

    def activate(self):
        self.refresh()

    def process_update(self, action, data):
        if action == "notify_status_update" and "amf" in data:
            self.refresh()
