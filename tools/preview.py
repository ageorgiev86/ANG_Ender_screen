"""Render approximate KlipperScreen layouts with base.css + a theme, at 800x480, to PNG.
Usage: preview.py <base.css> <theme_dir> <out_dir>
"""
import sys, os
import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, GdkPixbuf, Pango

BASE, THEME_DIR, OUT = sys.argv[1:4]
W, H = 800, 480
FS = min(W / 40, H / 27) * 0.91  # font_size: small
IMG = FS * 2 * 1.38
IMGDIR = os.path.join(THEME_DIR, "images")
KS = os.path.dirname(os.path.dirname(BASE))  # KlipperScreen root, url("./styles/...") is relative to it
os.chdir(KS)

css = open(BASE).read().replace("KS_FONT_SIZE", f"{FS}")
css += open(os.path.join(THEME_DIR, "style.css")).read()
# KlipperScreen sets these per device from style.conf graph_colors; emulate:
css += ".gl-hot{border-left-color:#FF6A3D}.gl-bed{border-left-color:#2F9BFF}.gl-fan{border-left-color:#A5F960}.gl-x{border-left-color:#FFB020}"
css = css.replace("./styles/ang-bambu/", THEME_DIR.rstrip("/") + "/")
prov = Gtk.CssProvider()
prov.load_from_data(css.encode())
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER)


def img(name, scale=1.0):
    s = int(IMG * scale)
    pb = GdkPixbuf.Pixbuf.new_from_file_at_size(os.path.join(IMGDIR, name + ".svg"), s, s)
    return Gtk.Image.new_from_pixbuf(pb)


def btn(icon, label=None, cls=None, scale=1.0, side=False):
    b = Gtk.Button(hexpand=True, vexpand=True)
    if icon:
        b.set_image(img(icon, scale))
        b.set_always_show_image(True)
        b.set_image_position(Gtk.PositionType.LEFT if side else Gtk.PositionType.TOP)
    if label:
        b.set_label(label)
    if cls:
        b.get_style_context().add_class(cls)
    return b


def lbl(text, cls=None, xalign=0.0):
    l = Gtk.Label(label=text, xalign=xalign)
    l.set_ellipsize(Pango.EllipsizeMode.END)
    if cls:
        l.get_style_context().add_class(cls)
    return l


def frame(title, content):
    """KlipperScreen layout: action bar left (10%), title bar on top, content."""
    # Same structure as KlipperScreen panels/base_panel.py (horizontal mode)
    root = Gtk.Grid()
    ab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, homogeneous=True, vexpand=True, hexpand=False)
    ab.get_style_context().add_class("action_bar")
    ab.set_size_request(int(W * 0.1), H)
    for i in ["back", "main", "emergency", "settings"]:
        b = btn(i, scale=0.7)
        b.set_hexpand(False)
        ab.add(b)
    tb = Gtk.Box(spacing=5, valign=Gtk.Align.CENTER)
    tb.get_style_context().add_class("title_bar")
    tb.set_size_request(-1, int(FS * 2))
    tb.pack_start(lbl("  " + title), True, True, 0)
    tb.pack_end(lbl("14:32  ", xalign=1.0), False, False, 0)
    content.get_style_context().add_class("content")
    content.set_size_request(W - int(W * 0.1), H - int(FS * 2))
    root.attach(tb, 1, 0, 1, 1)
    root.attach(content, 1, 1, 1, 1)
    root.attach(ab, 0, 0, 1, 2)
    return root


def heater_row(icon, name, cur, tgt, color):
    b = Gtk.Button(hexpand=True)
    box = Gtk.Box(spacing=8)
    box.pack_start(img(icon, 0.55), False, False, 0)
    n = lbl(name)
    n.get_style_context().add_class("graph_label")
    if color:
        n.get_style_context().add_class("gl-" + color)
    box.pack_start(n, True, True, 0)
    box.pack_end(lbl(f"{cur}° / {tgt}°" if tgt != "" else str(cur), xalign=1.0), False, False, 0)
    b.add(box)
    return b


def main_menu():
    g = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
    left.get_style_context().add_class("heater-list")
    left.add(heater_row("extruder", "Дюза", 215, 215, "hot"))
    left.add(heater_row("bed", "Легло", 60, 60, "bed"))
    left.add(heater_row("fan", "Вентилатор", "100%", "", "fan"))
    left.add(heater_row("heater", "Камера", 34, 0, "x"))
    g.attach(left, 0, 0, 1, 1)
    menu = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
    items = [("home", "Home", "color1"), ("filament", "Филамент", "color2"),
             ("move", "Движение", "color3"), ("bed-level", "Калибрация", "color4"),
             ("print", "Печат", "color1"), ("fan", "Вентилатори", "color2")]
    for i, (ic, t, c) in enumerate(items):
        ic = ic if os.path.exists(os.path.join(IMGDIR, ic + ".svg")) else "printer"
        menu.attach(btn(ic, t, c), i % 3, i // 3, 1, 1)
    g.attach(menu, 1, 0, 1, 1)
    return frame("Ender 3 — Готов", g)


def job_status():
    g = Gtk.Grid(column_homogeneous=False, row_spacing=4, column_spacing=6)
    thumb = Gtk.Box()
    thumb.get_style_context().add_class("printing-thumbnail")
    thumb.set_size_request(int(W * 0.32), int(H * 0.45))
    thumb.pack_start(img("file", 2.2), True, True, 0)
    g.attach(thumb, 0, 0, 1, 2)

    info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4, hexpand=True)
    info.pack_start(lbl("benchy_0.2mm_PLA.gcode", "printing-filename"), False, False, 0)
    info.pack_start(lbl("Печат…  слой 42 / 120", "printing-status"), False, False, 0)
    pr = Gtk.Box(spacing=8)
    bar = Gtk.ProgressBar(fraction=0.37, hexpand=True, valign=Gtk.Align.CENTER)
    pr.pack_start(bar, True, True, 0)
    pr.pack_end(lbl("37%", "printing-progress-text"), False, False, 0)
    info.pack_start(pr, False, False, 0)
    info.pack_start(lbl("Остават 1ч 12м   ·   ETA 15:44", "printing-status"), False, False, 0)
    g.attach(info, 1, 0, 1, 1)

    sec = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
    sec.get_style_context().add_class("printing-info-secondary")
    for i, (ic, t) in enumerate([("extruder", "215 / 215°"), ("bed", "60 / 60°"),
                                 ("fan", "100%"), ("speed+", "100%")]):
        sec.attach(btn(ic, t, scale=0.5, side=True), i % 2, i // 2, 1, 1)
    sec.set_vexpand(True)
    g.attach(sec, 1, 1, 1, 1)

    acts = Gtk.Grid(column_homogeneous=True, hexpand=True)
    for i, (ic, t, c) in enumerate([("pause", "Пауза", "color1"), ("cancel", "Спри", "color2"),
                                    ("fine-tune", "Настройки", "color3"), ("settings", "Контрол", "color4")]):
        acts.attach(btn(ic, t, c, scale=0.8), i, 0, 1, 1)
    acts.set_size_request(-1, int(H * 0.27))
    g.attach(acts, 0, 2, 2, 1)
    return frame("Печат", g)


def temp_panel():
    g = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
    for i, (t, s) in enumerate([("Дюза", 1), ("Легло", 1)]):
        pass
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True)
    left.add(heater_row("extruder", "Дюза", 185, 215, "hot"))
    left.add(heater_row("bed", "Легло", 58, 60, "bed"))
    sc = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 300, 1)
    sc.set_value(215)
    left.add(sc)
    sw = Gtk.Box(spacing=8)
    sw.pack_start(lbl("  Само нагреватели"), True, True, 0)
    s = Gtk.Switch(active=True, valign=Gtk.Align.CENTER)
    sw.pack_end(s, False, False, 8)
    left.add(sw)
    g.attach(left, 0, 0, 1, 1)
    pre = Gtk.Grid(column_homogeneous=True, row_homogeneous=True)
    for i, (t, c) in enumerate([("PLA", "color1"), ("PETG", "color2"), ("ABS", "color3"),
                                ("TPU", "color4"), ("Охлади", "color1"), ("+10°", "color2")]):
        b = btn(None, t, c)
        if i == 0:
            b.get_style_context().add_class("button_active")
        pre.attach(b, i % 2, i // 2, 1, 1)
    g.attach(pre, 1, 0, 1, 1)
    return frame("Температура", g)


screens = [("1-main-menu", main_menu), ("2-printing", job_status), ("3-temperature", temp_panel)]


def shoot(idx=0):
    name, fn = screens[idx]
    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_default_size(W, H)
    win.set_decorated(False)
    win.add(fn())
    win.show_all()
    win.move(0, 0)

    def snap():
        alloc = win.get_allocation()
        pb = Gdk.pixbuf_get_from_window(win.get_window(), 0, 0, alloc.width, alloc.height)
        pb.savev(os.path.join(OUT, name + ".png"), "png", [], [])
        win.destroy()
        if idx + 1 < len(screens):
            GLib.idle_add(shoot, idx + 1)
        else:
            Gtk.main_quit()
        return False

    GLib.timeout_add(700, snap)
    return False


GLib.idle_add(shoot, 0)
Gtk.main()
