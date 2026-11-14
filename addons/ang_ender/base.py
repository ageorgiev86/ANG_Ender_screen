"""Базов клас за панелите на ANG Ender."""
import logging

from ks_includes.screen_panel import ScreenPanel

from . import ui


class AngPanel(ScreenPanel):
    def __init__(self, screen, title, **kwargs):
        super().__init__(screen, title)
        self.content.get_style_context().add_class("ang-page")

    # --- данни ---
    def stat(self, obj, key, default=None):
        try:
            v = self._printer.get_stat(obj, key)
        except Exception:
            return default
        return default if v in (None, {}) else v

    def has(self, obj):
        try:
            return obj in self._printer.get_config_section_list() or bool(self._printer.get_stat(obj))
        except Exception:
            return False

    def temp_text(self, obj):
        t = self.stat(obj, "temperature")
        if t is None:
            return "--"
        tg = self.stat(obj, "target")
        return ui.value_markup(f"{t:.0f}/{tg:.0f}" if tg is not None else f"{t:.0f}", "℃")

    # --- действия ---
    def gcode(self, script):
        logging.info(f"ang_ender gcode: {script}")
        try:
            self._screen._send_action(None, "printer.gcode.script", {"script": script})
        except Exception:
            logging.exception("ang_ender: gcode failed")

    def open(self, panel, title=None, **kw):
        # KlipperScreen пази отворените страници по име. Страница с параметри
        # (кой нагревател, кой вентилатор, кой слот) получава собствено име,
        # иначе би се показала старата.
        if (kw or title) and "panel_name" not in kw:
            parts = [title] if title else []
            parts += [str(v) for v in kw.values() if isinstance(v, (str, int))]
            kw["panel_name"] = "_".join([panel] + parts)
        self._screen.show_panel(panel, title, **kw)

    def light_on(self, obj):
        """output_pin -> value; neopixel/led -> някой канал > 0."""
        val = self.stat(obj, "value")
        if val is not None:
            return val > 0
        data = self.stat(obj, "color_data")
        if data:
            return any(c > 0 for px in data for c in px)
        return None

    def back(self, *args):
        self._screen._menu_go_back()
