"""Движение: кръгъл джойстик за XY (пръстени ±1/±10, Home в средата) и колона за Z."""
import math

import cairo
from gi.repository import Gdk, Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel
from ks_addons.ang_ender.config import Z_MOVES

FEED_XY = 6000
FEED_Z = 600


class JogPad(Gtk.DrawingArea):
    """Кръг с 4 сектора (Y, X, -Y, -X), вътрешен пръстен 1 mm, външен 10 mm, център Home."""

    def __init__(self, size, on_move, on_home):
        super().__init__()
        self.set_size_request(size, size)
        self.on_move, self.on_home = on_move, on_home
        self.pressed = None
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        self.connect("draw", self._draw)
        self.connect("button-press-event", self._press)
        self.connect("button-release-event", self._release)

    def _geom(self):
        w, h = self.get_allocated_width(), self.get_allocated_height()
        R = min(w, h) / 2 - 4
        return w / 2, h / 2, R, R * 0.66, R * 0.28

    def _hit(self, x, y):
        cx, cy, R, r1, r0 = self._geom()
        dx, dy = x - cx, y - cy
        d = math.hypot(dx, dy)
        if d <= r0:
            return ("home", None, None)
        if d > R:
            return None
        ang = math.degrees(math.atan2(-dy, dx)) % 360
        axis = ("X", 1) if ang < 45 or ang >= 315 else ("Y", 1) if ang < 135 else ("X", -1) if ang < 225 else ("Y", -1)
        return ("move", axis, 1 if d <= r1 else 10)

    def _press(self, w, ev):
        self.pressed = self._hit(ev.x, ev.y)
        self.queue_draw()

    def _release(self, w, ev):
        hit = self.pressed
        self.pressed = None
        self.queue_draw()
        if not hit:
            return
        if hit[0] == "home":
            self.on_home()
        else:
            (ax, sign), dist = hit[1], hit[2]
            self.on_move(ax, sign * dist)

    def _draw(self, w, cr):
        cx, cy, R, r1, r0 = self._geom()
        # външен и вътрешен пръстен
        for rad, shade in ((R, 0.17), (r1, 0.22)):
            cr.arc(cx, cy, rad, 0, 2 * math.pi)
            cr.set_source_rgb(shade, shade, shade)
            cr.fill()
        # натиснат сектор
        if self.pressed and self.pressed[0] == "move":
            (ax, sign), dist = self.pressed[1], self.pressed[2]
            mid = {("X", 1): 0, ("Y", 1): 90, ("X", -1): 180, ("Y", -1): 270}[(ax, sign)]
            a0, a1 = math.radians(-(mid + 45)), math.radians(-(mid - 45))
            outer, inner = (R, r1) if dist == 10 else (r1, r0)
            cr.arc(cx, cy, outer, a0, a1)
            cr.arc_negative(cx, cy, inner, a1, a0)
            cr.close_path()
            cr.set_source_rgba(*ui.ACCENT, 0.35)
            cr.fill()
        # разделители по диагоналите
        cr.set_source_rgb(0.08, 0.08, 0.08)
        cr.set_line_width(R * 0.07)
        for a in (45, 135, 225, 315):
            ra = math.radians(a)
            cr.move_to(cx + math.cos(ra) * r0, cy - math.sin(ra) * r0)
            cr.line_to(cx + math.cos(ra) * (R + 2), cy - math.sin(ra) * (R + 2))
            cr.stroke()
        # център (Home)
        cr.arc(cx, cy, r0, 0, 2 * math.pi)
        cr.set_source_rgb(0.24, 0.24, 0.24)
        cr.fill_preserve()
        if self.pressed and self.pressed[0] == "home":
            cr.set_source_rgba(*ui.ACCENT, 0.5)
            cr.fill_preserve()
        cr.set_source_rgba(*ui.ACCENT, 0.9)
        cr.set_line_width(1.5)
        cr.stroke()
        # къщичка
        s = r0 * 0.45
        cr.move_to(cx - s, cy)
        cr.line_to(cx, cy - s)
        cr.line_to(cx + s, cy)
        cr.move_to(cx - s * 0.65, cy - s * 0.1)
        cr.line_to(cx - s * 0.65, cy + s * 0.75)
        cr.line_to(cx + s * 0.65, cy + s * 0.75)
        cr.line_to(cx + s * 0.65, cy - s * 0.1)
        cr.set_source_rgb(*ui.ACCENT)
        cr.set_line_width(2)
        cr.stroke()
        # надписи
        cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_source_rgb(0.92, 0.92, 0.92)
        cr.set_font_size(R * 0.11)
        mid_r = (R + r1) / 2
        for t, a in (("Y", 90), ("X", 0), ("-Y", 270), ("-X", 180)):
            ra = math.radians(a)
            e = cr.text_extents(t)
            cr.move_to(cx + math.cos(ra) * mid_r - e.width / 2, cy - math.sin(ra) * mid_r + e.height / 2)
            cr.show_text(t)
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.set_font_size(R * 0.08)
        for t, rr in (("+10", (R + r1) / 2), ("+1", (r1 + r0) / 2)):
            ra = math.radians(28)
            cr.move_to(cx + math.cos(ra) * rr, cy - math.sin(ra) * rr)
            cr.show_text(t)
        return False


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Движение")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header("Движение: XYZ", self.back))
        card = Gtk.Box(spacing=int(fs * 1.0), vexpand=True)
        card.get_style_context().add_class("ang-card")
        card.get_style_context().add_class("ang-pad")

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3), hexpand=True)
        left.add(ui.label("Глава", "ang-caption", xalign=0.5))
        size = int(ch * 0.70)
        pad = JogPad(size, self._move, self._home)
        pad.set_halign(Gtk.Align.CENTER)
        left.pack_start(pad, True, True, 0)
        card.pack_start(left, True, True, 0)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3))
        right.set_size_request(int(cw * 0.32), -1)
        right.add(ui.label("Легло" if Z_MOVES == "bed" else "Портал (Z)", "ang-caption", xalign=0.5))
        zcol = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)
        zcol.get_style_context().add_class("ang-zcol")
        # „↑“ винаги движи видимо нагоре: порталът нагоре = +Z;
        # леглото нагоре (към дюзата) = −Z
        sign = -1 if Z_MOVES == "bed" else 1
        for txt, dz in (("↑  10", 10 * sign), ("↑  1", 1 * sign), ("↓  1", -1 * sign), ("↓  10", -10 * sign)):
            b = Gtk.Button(label=txt, vexpand=True)
            b.get_style_context().add_class("ang-zbtn")
            b.connect("clicked", lambda w, d=dz: self._move("Z", d))
            zcol.pack_start(b, True, True, 0)
        right.pack_start(zcol, True, True, 0)
        card.pack_start(right, False, False, 0)

        root.pack_start(card, True, True, 0)
        self.content.add(root)

    def _move(self, axis, dist):
        feed = FEED_Z if axis == "Z" else FEED_XY
        self.gcode(f"G91\nG1 {axis}{dist} F{feed}\nG90")

    def _home(self):
        self.gcode("G28")
