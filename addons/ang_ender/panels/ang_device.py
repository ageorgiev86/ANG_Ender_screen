"""Устройство: карта на принтера, редове (мрежа, файлове, система), плочки (калибрация, инструменти, настройки)."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel

CALIBRATION = [
    ("Карта на леглото", "bed_mesh"),
    ("Z отместване", "zcalibrate"),
    ("Input shaper", "input_shaper"),
    ("Pressure advance", "pressure_advance"),
]
TOOLS = [
    ("Конзола", "console"),
    ("Макроси", "gcode_macros"),
    ("Ограничения", "limits"),
    ("Ретракция", "retraction"),
    ("Изключване на обекти", "exclude"),
]


class Panel(AngPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title or "Устройство")
        gtk = self._gtk
        fs = gtk.font_size
        cw, ch = gtk.content_width, gtk.content_height
        sp = int(fs * 0.5)

        grid = Gtk.Grid(column_spacing=sp, row_spacing=sp, column_homogeneous=True)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3))
        info.get_style_context().add_class("ang-card")
        info.get_style_context().add_class("ang-pad")
        info.add(ui.label("Принтер", "ang-caption"))
        info.pack_start(ui.Render("printer_front", int(cw * 0.25), int(ch * 0.30)), True, True, 0)
        name = getattr(getattr(screen, "state", None), "printer_name", None) or "ANGEnder"
        info.add(ui.label(name, "ang-card-title", xalign=0.5))
        grid.attach(info, 0, 0, 1, 1)

        rows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=sp)
        self.net = self._row(rows, "Мрежа", "", lambda *_: self.open("network"))
        self._row(rows, "Файлове", "", lambda *_: self.open("print"))
        self.ver = self._row(rows, "Система", "", lambda *_: self.open("system"))
        self._row(rows, "Изключване", "", lambda *_: self.open("shutdown"))
        grid.attach(rows, 1, 0, 2, 1)

        for i, (icon, text, cb) in enumerate([
            ("bed-level", "Калибрация", lambda *_: self.open("ang_list", "Калибрация", items=CALIBRATION)),
            ("custom-script", "Инструменти", lambda *_: self.open("ang_list", "Инструменти", items=TOOLS)),
            ("settings", "Настройки", lambda *_: self.open("settings")),
        ]):
            b = Gtk.Button(vexpand=True)
            b.get_style_context().add_class("ang-card")
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4), valign=Gtk.Align.CENTER)
            box.add(gtk.Image(icon, fs * 2.4, fs * 2.4))
            box.add(ui.label(text, "ang-card-title", xalign=0.5))
            b.add(box)
            b.connect("clicked", cb)
            grid.attach(b, i, 1, 1, 1)

        self.content.add(grid)

    def _row(self, parent, name, value, cb):
        b = Gtk.Button(vexpand=True)
        b.get_style_context().add_class("ang-card")
        b.get_style_context().add_class("ang-row")
        r = Gtk.Box()
        r.pack_start(ui.label(name, "ang-row-name"), True, True, 0)
        v = ui.label(value, "ang-row-value", xalign=1.0)
        r.pack_start(v, False, False, 8)
        r.pack_end(ui.label("›", "ang-chevron"), False, False, 0)
        b.add(r)
        b.connect("clicked", cb)
        parent.pack_start(b, True, True, 0)
        return v
