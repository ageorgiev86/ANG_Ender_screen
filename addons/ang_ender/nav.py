"""Лява навигация в стил Bambu: Начало, Управление, AMF, Устройство, Съобщения + авариен стоп."""
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

# (ключ, иконка в темата, панел или None за начало)
ITEMS = [
    ("home", "home", None),
    ("control", "fine-tune", "ang_control"),
    ("amf", "filament", "ang_amf"),
    ("device", "settings", "ang_device"),
    ("messages", "notifications", "notifications"),
]
ROOT_OF = {panel: key for key, _, panel in ITEMS if panel}


class Nav:
    def __init__(self, screen, gtk, estop_cb=None):
        self.screen = screen
        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, homogeneous=True, vexpand=True)
        self.box.get_style_context().add_class("ang-nav")
        self.buttons = {}
        size = gtk.font_size * 1.9
        for key, icon, panel in ITEMS:
            b = Gtk.Button()
            b.get_style_context().add_class("ang-nav-btn")
            b.set_image(gtk.Image(icon, size, size))
            b.set_always_show_image(True)
            b.connect("clicked", self._go, panel)
            self.box.pack_start(b, True, True, 0)
            self.buttons[key] = b
        if estop_cb:
            # празно място, за да не е авариен стоп точно под „Съобщения“
            self.box.set_homogeneous(False)
            for b in self.buttons.values():
                b.set_size_request(-1, int(gtk.font_size * 3.2))
            self.box.pack_start(Gtk.Box(vexpand=True), True, True, 0)
            e = Gtk.Button()
            e.get_style_context().add_class("ang-nav-btn")
            e.get_style_context().add_class("ang-nav-estop")
            e.set_image(gtk.Image("emergency", size, size))
            e.set_always_show_image(True)
            e.connect("clicked", estop_cb)
            e.set_size_request(-1, int(gtk.font_size * 3.2))
            self.box.pack_start(e, False, False, 0)
        self.set_active("home")

    def _go(self, w, panel):
        s = self.screen
        if hasattr(s, "_menu_go_back"):
            s._menu_go_back(home=True)
        if panel:
            s.show_panel(panel)

    def set_active(self, key):
        for k, b in self.buttons.items():
            ctx = b.get_style_context()
            (ctx.add_class if k == key else ctx.remove_class)("ang-nav-active")

    def sync(self, cur_panels):
        key = "home"
        for p in cur_panels[1:]:
            if p in ROOT_OF:
                key = ROOT_OF[p]
                break
        self.set_active(key)
