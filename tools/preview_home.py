"""Render the real ang_home panel with a stubbed KlipperScreen, at 800x480, to PNG.
Usage: preview_home.py <KlipperScreen dir> <repo dir> <out.png>
"""
import os
import sys
import types

KS, REPO, OUT = sys.argv[1:4]
sys.path.insert(0, KS)
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

W, H = 800, 480
FS = min(W / 40, H / 27) * 0.91
THEME = os.path.join(REPO, "styles", "ang-bambu")

css = open(os.path.join(KS, "styles", "base.css")).read().replace("KS_FONT_SIZE", f"{FS}")
css += open(os.path.join(THEME, "style.css")).read().replace("./styles/ang-bambu/", THEME + "/")
prov = Gtk.CssProvider()
prov.load_from_data(css.encode())
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER)

# Load the add-on the way KlipperScreen does: as package ks_addons.ang_ender
parent = types.ModuleType("ks_addons")
parent.__path__ = [os.path.join(REPO, "addons")]
sys.modules["ks_addons"] = parent
import builtins

builtins._ = lambda s: s
import importlib


class Cfg:
    def get_main_config(self):
        return self

    def getboolean(self, *a, **k):
        return False


class FakeGtk:
    font_size = FS
    content_width = W - int(W * 0.1)
    content_height = H - int(FS * 2)
    bsidescale = 0.55
    img_width = img_height = FS * 3

    def Image(self, name, w=None, h=None):
        p = os.path.join(THEME, "images", name + ".svg")
        pb = GdkPixbuf.Pixbuf.new_from_file_at_size(p, int(w or FS * 3), int(h or FS * 3))
        return Gtk.Image.new_from_pixbuf(pb)


class Printer:
    data = {"extruder": (24, 0), "heater_bed": (23, 0)}

    def get_stat(self, dev, key):
        t, tg = self.data[dev]
        return t if key == "temperature" else tg


class Files:
    files = {}

    def has_thumbnail(self, f):
        return False


screen = types.SimpleNamespace(
    _config=Cfg(), files=Files(), printer=Printer(), gtk=FakeGtk(),
    show_panel=lambda *a, **k: None,
)
mod = importlib.import_module("ks_addons.ang_ender.panels.ang_home")
panel = mod.Panel(screen, "ANG Ender", items=[])
panel.process_update("notify_status_update", {"extruder": {}, "heater_bed": {}})


def btn(icon):
    b = Gtk.Button()
    b.set_image(FakeGtk().Image(icon, FS * 1.9, FS * 1.9))
    b.set_always_show_image(True)
    return b


# Same frame as panels/base_panel.py (horizontal)
root = Gtk.Grid()
ab = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5, homogeneous=True, vexpand=True)
ab.get_style_context().add_class("action_bar")
ab.set_size_request(int(W * 0.1), H)
for i in ["main", "settings", "emergency", "shutdown"]:
    ab.add(btn(i))
tb = Gtk.Box(spacing=5)
tb.get_style_context().add_class("title_bar")
tb.set_size_request(-1, int(FS * 2))
tb.pack_start(Gtk.Label(label="  ANG Ender", xalign=0), True, True, 0)
tb.pack_end(Gtk.Label(label="14:32  ", xalign=1), False, False, 0)
panel.content.set_size_request(FakeGtk.content_width, FakeGtk.content_height)
root.attach(tb, 1, 0, 1, 1)
root.attach(panel.content, 1, 1, 1, 1)
root.attach(ab, 0, 0, 1, 2)

win = Gtk.Window()
win.set_default_size(W, H)
win.set_decorated(False)
win.add(root)
win.show_all()
win.move(0, 0)


def snap():
    a = win.get_allocation()
    pb = Gdk.pixbuf_get_from_window(win.get_window(), 0, 0, a.width, a.height)
    pb.savev(OUT, "png", [], [])
    Gtk.main_quit()


GLib.timeout_add(800, snap)
Gtk.main()
