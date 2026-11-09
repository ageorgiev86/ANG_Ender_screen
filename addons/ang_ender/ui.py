"""Общи елементи на ANG Ender UI: рендери, карти, макари, numpad, степер."""
import math
import os

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, Gtk, Pango

ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERS = os.path.join(ADDON_DIR, "assets", "renders")
ACCENT = (0x3D / 255, 0xA5 / 255, 1.0)

_pix_cache = {}


def render_path(name):
    return os.path.join(RENDERS, name + ".png")


def load_render(name):
    path = render_path(name)
    if not os.path.exists(path):
        return None
    mtime = os.path.getmtime(path)
    hit = _pix_cache.get(path)
    if hit and hit[0] == mtime:
        return hit[1]
    try:
        pb = GdkPixbuf.Pixbuf.new_from_file(path)
    except Exception:
        return None
    _pix_cache[path] = (mtime, pb)
    return pb


def rgb_hex(color, default=(0.5, 0.5, 0.5)):
    try:
        c = color.lstrip("#")
        return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except Exception:
        return default


def rounded(cr, x, y, w, h, r):
    r = min(r, w / 2, h / 2)
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()


def label(text, cls=None, xalign=0.0, wrap=False, markup=False):
    lbl = Gtk.Label(xalign=xalign)
    if markup:
        lbl.set_markup(text)
    else:
        lbl.set_text(text)
    if cls:
        for c in cls.split():
            lbl.get_style_context().add_class(c)
    if wrap:
        lbl.set_line_wrap(True)
        lbl.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        # иначе GTK иска ширина за целия текст на един ред и раздува колоната
        lbl.set_max_width_chars(24)
    else:
        lbl.set_ellipsize(Pango.EllipsizeMode.END)
    return lbl


def value_markup(value, unit):
    """'28' '℃' -> голямо число и по-малка единица, както при Bambu."""
    return f"{value}<span size='70%'>{unit}</span>"


class Render(Gtk.DrawingArea):
    """Място за рендер от SolidWorks.

    Ако assets/renders/<name>.png съществува, рисува го (вписан в полето).
    Иначе рисува пунктирна рамка с името на файла и препоръчания размер.
    `layers` са допълнителни прозрачни PNG-та със същата камера; включват се
    с set_layer(name, True) и се рисуват отгоре със синьо сияние.
    `points` е списък от (x, y) в относителни координати 0..1, които
    панелите ползват за пунктирните линии към стойностите.
    """

    def __init__(self, name, width, height, layers=None, compact=False):
        super().__init__()
        self.name = name
        self.compact = compact  # надписът в празната рамка е малък, в горния ляв ъгъл
        self.layers = {n: False for n in (layers or [])}
        self.set_size_request(width, height)
        self.connect("draw", self._draw)
        self.leaders = []  # [(rel_x, rel_y, widget)]

    def set_layer(self, name, on):
        if self.layers.get(name) != on:
            self.layers[name] = on
            self.queue_draw()

    def _fit(self, pb, w, h):
        s = min(w / pb.get_width(), h / pb.get_height())
        dw, dh = pb.get_width() * s, pb.get_height() * s
        return s, (w - dw) / 2, (h - dh) / 2

    def _draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        pb = load_render(self.name)
        if pb is None:
            self._placeholder(cr, w, h)
        else:
            s, ox, oy = self._fit(pb, w, h)
            cr.save()
            cr.translate(ox, oy)
            cr.scale(s, s)
            Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
            cr.paint()
            for lname, on in self.layers.items():
                lpb = load_render(f"{self.name}__{lname}")
                if on and lpb is not None:
                    Gdk.cairo_set_source_pixbuf(cr, lpb, 0, 0)
                    cr.paint()
            cr.restore()
        return False

    def _placeholder(self, cr, w, h):
        rounded(cr, 4, 4, w - 8, h - 8, 14)
        cr.set_source_rgba(1, 1, 1, 0.03)
        cr.fill_preserve()
        cr.set_source_rgba(*ACCENT, 0.55)
        cr.set_line_width(1.5)
        cr.set_dash([6, 5])
        cr.stroke()
        cr.set_dash([])
        cr.select_font_face("Sans")
        if self.compact:
            cr.set_font_size(10)
            cr.set_source_rgba(1, 1, 1, 0.5)
            cr.move_to(12, 18)
            cr.show_text(f"{self.name}.png  {int(w * 2)}×{int(h * 2)}" if w > 160 else self.name)
            return
        cr.set_font_size(max(10, min(15, w / 18)))
        cr.set_source_rgba(1, 1, 1, 0.75)
        lines = [f"{self.name}.png", f"рендер {int(w * 2)}×{int(h * 2)}"]
        lines += [f"+ {self.name}__{n}.png" for n in self.layers]
        y = h / 2 - (len(lines) - 1) * 10
        for i, t in enumerate(lines):
            ext = cr.text_extents(t)
            cr.move_to((w - ext.width) / 2, y + i * 20)
            if i:
                cr.set_source_rgba(1, 1, 1, 0.45)
            cr.show_text(t)
        on = [n for n, v in self.layers.items() if v]
        if on:
            cr.set_source_rgba(*ACCENT, 0.9)
            cr.set_font_size(11)
            t = "активни слоеве: " + ", ".join(on)
            cr.move_to(14, 24)
            cr.show_text(t)


class Leaders(Gtk.DrawingArea):
    """Пунктирни линии от точки върху рендера до етикет (като екрана за въздух)."""

    def __init__(self, overlay, render):
        super().__init__()
        self.overlay = overlay
        self.render = render
        self.links = []  # (rel_x, rel_y, widget, side)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self.connect("draw", self._draw)

    def link(self, rel_x, rel_y, widget, side="left"):
        self.links.append((rel_x, rel_y, widget, side))

    def _draw(self, widget, cr):
        rw, rh = self.render.get_allocated_width(), self.render.get_allocated_height()
        r0 = self.render.translate_coordinates(self, 0, 0)
        if not r0 or rw <= 1:
            return False
        cr.set_source_rgba(1, 1, 1, 0.35)
        cr.set_line_width(1)
        cr.set_dash([2, 3])
        for rx, ry, w, side in self.links:
            ww, wh = w.get_allocated_width(), w.get_allocated_height()
            p = w.translate_coordinates(self, 0, 0)
            if not p or ww <= 1:
                continue
            px, py = r0[0] + rx * rw, r0[1] + ry * rh
            ex = p[0] + ww + 4 if side == "left" else p[0] - 4
            ey = p[1] + wh * 0.35
            cr.move_to(ex, ey)
            cr.line_to(px, py)
            cr.stroke()
            cr.arc(px, py, 3, 0, 2 * math.pi)
            cr.stroke()
        return False


class Spool(Gtk.DrawingArea):
    """Макара в цвета на филамента.

    С assets/renders/spool_neutral.png (сива/бяла макара) оцветява рендера;
    без него рисува векторна макара с градиент.
    """

    def __init__(self, width, height):
        super().__init__()
        self.color = None  # (r, g, b) или None = празен слот
        self.active = False
        self.unknown = False
        self.set_size_request(width, height)
        self.connect("draw", self._draw)

    def set_state(self, color=None, active=False, unknown=False):
        self.color, self.active, self.unknown = color, active, unknown
        self.queue_draw()

    def _draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        pad = 4
        x, y, sw, sh = pad, pad, w - 2 * pad, h - 2 * pad
        if self.active:
            for i in range(6, 0, -1):
                rounded(cr, x - i, y - i, sw + 2 * i, sh + 2 * i, sw / 3 + i)
                cr.set_source_rgba(*ACCENT, 0.05)
                cr.fill()
        pb = load_render("spool_neutral")
        if pb is not None and self.color is not None:
            s = min(sw / pb.get_width(), sh / pb.get_height())
            cr.save()
            cr.translate(x + (sw - pb.get_width() * s) / 2, y + (sh - pb.get_height() * s) / 2)
            cr.scale(s, s)
            Gdk.cairo_set_source_pixbuf(cr, pb, 0, 0)
            cr.paint()
            # умножаване с цвета, маскирано с алфата на рендера
            cr.set_operator(12)  # CAIRO_OPERATOR_MULTIPLY
            cr.set_source_rgb(*self.color)
            cr.mask_surface(Gdk.cairo_surface_create_from_pixbuf(pb, 1, None), 0, 0)
            cr.restore()
            return False
        # векторна макара: тъмни фланци отгоре/отдолу, цветна навивка
        fl = sh * 0.07
        rounded(cr, x, y, sw, sh, sw * 0.28)
        cr.set_source_rgb(0.13, 0.13, 0.14)
        cr.fill()
        bx, by, bw, bh = x + sw * 0.08, y + fl, sw * 0.84, sh - 2 * fl
        rounded(cr, bx, by, bw, bh, bw * 0.22)
        if self.color is None:
            cr.set_source_rgb(0.20, 0.20, 0.21)
            cr.fill()
        elif self.unknown:
            cr.save()
            cr.clip()
            n = 6
            cs = bw / n
            for i in range(n):
                for j in range(int(bh / cs) + 1):
                    v = 0.85 if (i + j) % 2 else 0.35
                    cr.set_source_rgb(v, v, v)
                    cr.rectangle(bx + i * cs, by + j * cs, cs, cs)
                    cr.fill()
            cr.restore()
        else:
            import cairo

            r, g, b = self.color
            grad = cairo.LinearGradient(bx, 0, bx + bw, 0)
            grad.add_color_stop_rgb(0.0, r * 0.55, g * 0.55, b * 0.55)
            grad.add_color_stop_rgb(0.35, min(1, r * 1.15 + 0.08), min(1, g * 1.15 + 0.08), min(1, b * 1.15 + 0.08))
            grad.add_color_stop_rgb(1.0, r * 0.45, g * 0.45, b * 0.45)
            cr.set_source(grad)
            cr.fill()
            # фини навивки
            cr.set_source_rgba(0, 0, 0, 0.12)
            cr.set_line_width(1)
            yy = by + 3
            while yy < by + bh - 2:
                cr.move_to(bx + 2, yy)
                cr.line_to(bx + bw - 2, yy)
                cr.stroke()
                yy += 3
        if self.active:
            rounded(cr, x, y, sw, sh, sw * 0.28)
            cr.set_source_rgba(*ACCENT, 1)
            cr.set_line_width(2)
            cr.stroke()
        return False


class HumidityDrop(Gtk.DrawingArea):
    """Капка с ниво (влажност 0..100%)."""

    def __init__(self, width, height):
        super().__init__()
        self.level = None
        self.set_size_request(width, height)
        self.connect("draw", self._draw)

    def set_level(self, pct):
        self.level = pct
        self.queue_draw()

    def _path(self, cr, w, h):
        cx = w / 2
        r = min(w, h) * 0.36
        cy = h - r - 2
        cr.move_to(cx, 2)
        cr.curve_to(cx + r * 0.3, h * 0.25, cx + r, cy - r * 0.4, cx + r, cy)
        cr.arc(cx, cy, r, 0, math.pi)
        cr.curve_to(cx - r, cy - r * 0.4, cx - r * 0.3, h * 0.25, cx, 2)
        cr.close_path()

    def _draw(self, widget, cr):
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        self._path(cr, w, h)
        cr.set_source_rgba(1, 1, 1, 0.9)
        cr.fill_preserve()
        if self.level is not None:
            cr.save()
            cr.clip()
            lvl = max(0, min(100, self.level)) / 100
            cr.rectangle(0, h * (1 - lvl), w, h * lvl)
            cr.set_source_rgb(*ACCENT)
            cr.fill()
            cr.restore()
        return False


def icon_circle(gtk, icon, size):
    """Иконка в тъмен кръг (както в картите на Bambu)."""
    box = Gtk.Box(halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    box.get_style_context().add_class("ang-icon-circle")
    box.set_size_request(int(size), int(size))
    img = gtk.Image(icon, size * 0.6, size * 0.6)
    img.set_hexpand(True)
    box.pack_start(img, True, True, 0)
    return box


def info_card(gtk, icon, caption, value_widget, chevron=True, cb=None):
    """Карта: [кръг с иконка] малък надпис / голяма стойност  ›"""
    fs = gtk.font_size
    btn = Gtk.Button(hexpand=True)
    btn.get_style_context().add_class("ang-card")
    btn.get_style_context().add_class("ang-info-card")
    row = Gtk.Box(spacing=int(fs * 0.6))
    row.pack_start(icon_circle(gtk, icon, fs * 2.2), False, False, 0)
    col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER)
    col.add(label(caption, "ang-caption"))
    col.add(value_widget)
    row.pack_start(col, True, True, 0)
    if chevron:
        row.pack_end(label("›", "ang-chevron", xalign=1.0), False, False, 0)
    btn.add(row)
    if cb:
        btn.connect("clicked", cb)
    return btn


def page_header(title, back_cb=None, action=None):
    """Заглавие на подстраница: '‹ Заглавие' и бутон-действие вдясно."""
    bar = Gtk.Box(spacing=8)
    bar.get_style_context().add_class("ang-header")
    if back_cb:
        b = Gtk.Button(label="‹")
        b.get_style_context().add_class("ang-back")
        b.connect("clicked", back_cb)
        bar.pack_start(b, False, False, 0)
    bar.pack_start(label(title, "ang-title"), True, True, 0)
    if action:
        text, cb = action
        a = Gtk.Button(label=text)
        a.get_style_context().add_class("ang-primary")
        a.connect("clicked", cb)
        bar.pack_end(a, False, False, 0)
    return bar


class Stepper(Gtk.Box):
    """Вертикален регулатор  +  /  стойност  /  −  (като вентилаторите при Bambu)."""

    def __init__(self, gtk, value=0, step=10, lo=0, hi=100, unit="%", on_change=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.get_style_context().add_class("ang-stepper")
        self.value, self.step, self.lo, self.hi, self.unit = value, step, lo, hi, unit
        self.on_change = on_change
        fs = gtk.font_size
        plus = Gtk.Button(label="+", vexpand=True)
        minus = Gtk.Button(label="−", vexpand=True)
        for b in (plus, minus):
            b.get_style_context().add_class("ang-step-btn")
        self.lbl = label("", "ang-step-value", xalign=0.5, markup=True)
        self.lbl.set_size_request(int(fs * 5), int(fs * 3.2))
        plus.connect("clicked", lambda *_: self.set_value(self.value + self.step, True))
        minus.connect("clicked", lambda *_: self.set_value(self.value - self.step, True))
        self.pack_start(plus, True, True, 0)
        self.pack_start(self.lbl, False, False, 0)
        self.pack_start(minus, True, True, 0)
        self.set_value(value)

    def set_value(self, v, user=False):
        self.value = max(self.lo, min(self.hi, v))
        self.lbl.set_markup(value_markup(int(self.value), self.unit))
        if user and self.on_change:
            self.on_change(self.value)


class Numpad(Gtk.Grid):
    """Цифрова клавиатура 3x4 с поле за стойност отгоре."""

    def __init__(self, gtk, unit="℃", on_change=None):
        super().__init__(row_homogeneous=True, column_homogeneous=True, row_spacing=6, column_spacing=6)
        self.text = ""
        self.unit = unit
        self.on_change = on_change
        self.display = label("", "ang-numpad-display", xalign=0.5, markup=True)
        self.attach(self.display, 0, 0, 3, 1)
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "", "0", "⌫"]
        for i, k in enumerate(keys):
            if not k:
                continue
            b = Gtk.Button(label=k)
            b.get_style_context().add_class("ang-numkey")
            b.connect("clicked", self._key, k)
            self.attach(b, i % 3, 1 + i // 3, 1, 1)
        self._refresh()

    def _key(self, w, k):
        self.text = self.text[:-1] if k == "⌫" else (self.text + k)[:3]
        self._refresh()

    def _refresh(self):
        shown = self.text or ""
        self.display.set_markup(value_markup(shown, self.unit) if shown else self.unit)
        if self.on_change:
            self.on_change(self.value())

    def value(self):
        return int(self.text) if self.text else None
