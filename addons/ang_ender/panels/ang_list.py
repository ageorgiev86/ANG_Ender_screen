"""Списък в стил Bambu: редове „име … ›“ и колона с големи ▲/▼ за превъртане."""
from gi.repository import Gtk

from ks_addons.ang_ender import ui
from ks_addons.ang_ender.base import AngPanel


class Panel(AngPanel):
    def __init__(self, screen, title, items=None, **kwargs):
        super().__init__(screen, title or "")
        gtk = self._gtk
        fs = gtk.font_size
        items = items or []

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        root.add(ui.page_header(self.title, self.back))
        body = Gtk.Box(spacing=int(fs * 0.5), vexpand=True)

        self.scroll = Gtk.ScrolledWindow(hexpand=True)
        self.scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        lst = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.3))
        for name, panel in items:
            b = Gtk.Button()
            b.get_style_context().add_class("ang-card")
            b.get_style_context().add_class("ang-row")
            b.set_size_request(-1, int(fs * 2.4))
            r = Gtk.Box()
            r.pack_start(ui.label(name, "ang-row-name"), True, True, 0)
            r.pack_end(ui.label("›", "ang-chevron"), False, False, 0)
            b.add(r)
            b.connect("clicked", lambda w, p=panel, n=name: self.open(p, n))
            lst.add(b)
        self.scroll.add(lst)
        body.pack_start(self.scroll, True, True, 0)

        arrows = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=int(fs * 0.4))
        arrows.set_size_request(int(fs * 2.8), -1)
        for txt, d in (("▲", -1), ("▼", 1)):
            b = Gtk.Button(label=txt, vexpand=True)
            b.get_style_context().add_class("ang-scroll-btn")
            b.connect("clicked", self._scroll, d)
            arrows.pack_start(b, True, True, 0)
        body.pack_end(arrows, False, False, 0)

        root.pack_start(body, True, True, 0)
        self.content.add(root)

    def _scroll(self, w, d):
        adj = self.scroll.get_vadjustment()
        adj.set_value(adj.get_value() + d * adj.get_page_size() * 0.8)
