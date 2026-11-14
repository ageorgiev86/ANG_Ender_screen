"""Снима всички ang_* страници с изкуствени данни, 800x480, в PNG.

Usage: preview_pages.py <KlipperScreen dir> <repo dir> <out dir> [page ...]
Нужни са GTK3 и Xvfb:  xvfb-run -a -s "-screen 0 800x480x24" python3 tools/preview_pages.py ...
"""
import builtins
import importlib
import os
import sys
import types

KS, REPO, OUT = sys.argv[1:4]
ONLY = sys.argv[4:]
sys.path.insert(0, KS)
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

builtins._ = lambda s: s
W, H = 800, 480
FS = min(W / 40, H / 27) * 0.91
THEME = os.path.join(REPO, "styles", "ang-bambu")

css = open(os.path.join(KS, "styles", "base.css")).read().replace("KS_FONT_SIZE", f"{FS}")
css += open(os.path.join(THEME, "style.css")).read().replace("./styles/ang-bambu/", THEME + "/")
prov = Gtk.CssProvider()
prov.load_from_data(css.encode())
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_USER)

parent = types.ModuleType("ks_addons")
parent.__path__ = [os.path.join(REPO, "addons")]
sys.modules["ks_addons"] = parent

DATA = {
    "extruder": {"temperature": 215.2, "target": 215},
    "heater_bed": {"temperature": 60.1, "target": 60},
    "heater_generic chamber": {"temperature": 38.4, "target": 45},
    "fan": {"speed": 1.0},
    "fan_generic chamber_fan": {"speed": 0.35},
    "neopixel bed_leds": {"color_data": [[1.0, 1.0, 1.0, 0.0]] * 17},
    "gcode_move": {"speed_factor": 1.0},
    "toolhead": {"homed_axes": "xyz"},
    "print_stats": {"state": "printing", "filename": "benchy_0.2mm_PETG.gcode", "print_duration": 2280,
                    "info": {"current_layer": 42, "total_layer": 120}},
    "virtual_sdcard": {"progress": 0.37},
    "amf": {
        "active_slot": 1, "max_slots": 6,
        "profiles": ["PLA", "PETG", "ABS", "ASA", "TPU", "PC"],
        "slots": {
            "0": {"filament": True, "color": "F2F2F2", "profile": "PLA", "humidity": 18, "online": True, "temperature": 26},
            "1": {"filament": True, "color": "3DA5FF", "profile": "PETG", "humidity": 22, "online": True, "temperature": 26},
            "2": {"filament": True, "color": "FF7A1A", "profile": "PLA", "humidity": 34, "online": True, "temperature": 48, "target_temp": 55, "drying": True},
            "3": {"filament": False, "online": True, "humidity": 20},
            "4": {"filament": True, "color": "4CAF50", "profile": "TPU", "humidity": 25, "online": True},
            "5": {"filament": True, "color": "161616", "profile": "PC", "humidity": 12, "online": True},
        },
    },
}


class Cfg:
    def get_main_config(self):
        return self

    def getboolean(self, *a, **k):
        return False

    def get(self, *a, **k):
        return k.get("fallback")


class FakeGtk:
    font_size = FS
    content_width = W - int(W * 0.1)
    content_height = H - int(FS * 2)
    bsidescale = 0.55
    img_width = img_height = FS * 3
    _executor = None

    def PixbufFromIcon(self, name, w=None, h=None):
        p = os.path.join(THEME, "images", name + ".svg")
        return GdkPixbuf.Pixbuf.new_from_file_at_size(p, int(w or FS * 3), int(h or FS * 3))

    def Image(self, name, w=None, h=None):
        p = os.path.join(THEME, "images", name + ".svg")
        if not os.path.exists(p):
            return Gtk.Image()
        pb = GdkPixbuf.Pixbuf.new_from_file_at_size(p, int(w or FS * 3), int(h or FS * 3))
        return Gtk.Image.new_from_pixbuf(pb)


class Printer:
    def get_stat(self, obj, key=None):
        d = DATA.get(obj, {})
        return d if key is None else d.get(key)

    def get_config_section_list(self):
        return list(DATA)


class Files:
    files = {}

    def has_thumbnail(self, f):
        return False


screen = types.SimpleNamespace(
    _config=Cfg(), files=Files(), printer=Printer(), gtk=FakeGtk(),
    show_panel=lambda *a, **k: None, _menu_go_back=lambda *a, **k: None,
    _send_action=lambda *a, **k: None, state=types.SimpleNamespace(printer_name="ANGEnder"),
)
nav_mod = importlib.import_module("ks_addons.ang_ender.nav")
# в контейнера няма Wi-Fi: показваме примерна връзка
importlib.import_module("ks_addons.ang_ender.ui").network_status = lambda: ("wifi", 82, "ANG-Home")

PAGES = [
    ("01-home", "ang_home", "home", {}),
    ("02-control", "ang_control", "control", {}),
    ("03-air", "ang_air", "control", {}),
    ("04-fan-part", "ang_fan", "control", {"fan": "part"}),
    ("05-nozzle", "ang_nozzle", "control", {}),
    ("06-numpad-bed", "ang_numpad", "control", {"device": "heater_bed", "render": "printer_bed", "title": "Легло"}),
    ("07-motion", "ang_motion", "control", {}),
    ("08-speed", "ang_speed", "control", {}),
    ("09-amf", "ang_amf", "amf", {}),
    ("09b-amf-page2", "ang_amf", "amf", {"_page": 1}),
    ("10-amf-edit", "ang_amf_edit", "amf", {"slot": 1}),
    ("11-amf-dry", "ang_amf_dry", "amf", {"slot": 1}),
    ("12-device", "ang_device", "device", {}),
    ("13-calibration", "ang_list", "device", {"title": "Калибрация", "items": [("Карта на леглото", ""), ("Z отместване", ""), ("Input shaper", ""), ("Pressure advance", "")]}),
    ("14-printing", "ang_job", "home", {}),
]
if ONLY:
    PAGES = [p for p in PAGES if p[0] in ONLY or p[1] in ONLY]


def build(module, kwargs):
    kwargs = dict(kwargs)
    title = kwargs.pop("title", None)
    page = kwargs.pop("_page", None)
    mod = importlib.import_module(f"ks_addons.ang_ender.panels.{module}")
    panel = mod.Panel(screen, title, **kwargs)
    if page is not None:
        panel._goto(None, page)
    if hasattr(panel, "process_update"):
        panel.process_update("notify_status_update", DATA)
    return panel


def frame(panel, active):
    root = Gtk.Grid()
    bar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    bar.get_style_context().add_class("action_bar")
    bar.get_style_context().add_class("ang-action-bar")
    bar.set_size_request(int(W * 0.1), H)
    nav = nav_mod.Nav(screen, FakeGtk(), estop_cb=lambda *a: None)
    nav.set_active(active)
    bar.pack_start(nav.box, True, True, 0)
    panel.content.set_size_request(W - int(W * 0.1), H)
    root.attach(panel.content, 1, 0, 1, 1)
    root.attach(bar, 0, 0, 1, 1)
    return root


def shoot(i=0):
    name, module, active, kwargs = PAGES[i]
    win = Gtk.Window()
    win.set_default_size(W, H)
    win.set_decorated(False)
    try:
        win.add(frame(build(module, kwargs), active))
    except Exception:
        import traceback

        traceback.print_exc()
        print(f"FAILED {name}")
        GLib.idle_add(next_or_quit, i, win)
        return False
    win.show_all()
    win.move(0, 0)

    def snap():
        a = win.get_allocation()
        pb = Gdk.pixbuf_get_from_window(win.get_window(), 0, 0, min(a.width, W), min(a.height, H))
        pb.savev(os.path.join(OUT, name + ".png"), "png", [], [])
        if a.width > W or a.height > H:
            print(f"WARNING {name}: window {a.width}x{a.height} exceeds {W}x{H}")
        next_or_quit(i, win)
        return False

    GLib.timeout_add(700, snap)
    return False


def next_or_quit(i, win):
    win.destroy()
    if i + 1 < len(PAGES):
        GLib.idle_add(shoot, i + 1)
    else:
        Gtk.main_quit()
    return False


os.makedirs(OUT, exist_ok=True)
GLib.idle_add(shoot, 0)
Gtk.main()
