"""ANG Ender добавка за KlipperScreen.

Подменя началния екран ("main_menu") с изчистения панел ang_home.
Името на панела остава "main_menu", така че подменютата и навигацията
на KlipperScreen продължават да работят както преди.
"""
import importlib
import logging

# Кой стандартен панел с кой наш модул да се замести
OVERRIDES = {
    "main_menu": "ang_home",
}


def init(screen):
    original = screen._load_panel

    def _load_panel(panel):
        if panel in OVERRIDES:
            name = OVERRIDES[panel]
            try:
                return importlib.import_module(f"{__name__}.panels.{name}")
            except Exception:
                logging.exception(f"ang_ender: cannot load {name}, using stock {panel}")
        return original(panel)

    screen._load_panel = _load_panel
    logging.info("ang_ender: home screen override active")
