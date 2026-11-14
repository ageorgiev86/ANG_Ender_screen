"""ANG Ender добавка за KlipperScreen.

- Зарежда страниците panels/ang_*.py (имената им започват с "ang_").
- Подменя началния екран ("main_menu") с ang_home. Името остава "main_menu",
  така че подменютата и навигацията на KlipperScreen работят както преди.
- Заменя лявата лента с навигация като при Bambu (Начало, Управление, AMF,
  Устройство, Съобщения, авариен стоп) и мести бутона „назад“ в заглавието.
- На страниците ang_* заглавната лента на KlipperScreen се скрива — те имат
  собствено заглавие „‹ …“.
"""
import importlib
import logging

# Стандартен панел -> наш модул. За да върнеш стандартния екран по време на
# печат, закоментирай реда за job_status.
OVERRIDES = {
    "main_menu": "ang_home",
    "job_status": "ang_job",
    "splash_screen": "ang_splash",
}


def _is_ang(panel_obj):
    return type(panel_obj).__module__.startswith(__name__ + ".panels.")


def init(screen):
    original = screen._load_panel

    def _load_panel(panel):
        name = OVERRIDES.get(panel, panel if panel.startswith("ang_") else None)
        if name:
            try:
                return importlib.import_module(f"{__name__}.panels.{name}")
            except Exception:
                logging.exception(f"ang_ender: cannot load {name}")
                if panel.startswith("ang_"):
                    raise
        return original(panel)

    screen._load_panel = _load_panel

    try:
        _install_nav(screen)
    except Exception:
        logging.exception("ang_ender: navigation not installed, keeping stock action bar")
    logging.info("ang_ender: active")


def _install_nav(screen):
    from .nav import Nav

    bp = screen.base_panel
    def estop(widget):
        # винаги с потвърждение: бутонът е в навигацията, лесно се натиска по погрешка
        screen._confirm_send_action(widget, "Аварийно спиране на принтера?", "printer.emergency_stop")

    nav = Nav(screen, screen.gtk, estop_cb=estop)
    # махаме стандартните бутони от лентата (обектите остават в bp.control,
    # за да може KlipperScreen да им сменя видимостта без грешки)
    for key in ("home", "printer_select", "shortcut", "estop", "shutdown"):
        btn = bp.control.get(key)
        if btn is not None and btn.get_parent() is bp.action_bar:
            bp.action_bar.remove(btn)
    # „назад“ отива в заглавната лента вляво (за стандартните панели)
    back = bp.control["back"]
    bp.action_bar.remove(back)
    bp.titlebar.pack_start(back, False, False, 0)
    bp.titlebar.reorder_child(back, 0)
    bp.action_bar.pack_start(nav.box, True, True, 0)
    bp.action_bar.get_style_context().add_class("ang-action-bar")
    screen.ang_nav = nav

    orig_add = bp.add_content

    def add_content(panel):
        orig_add(panel)
        ang = _is_ang(panel)
        bp.titlebar.set_no_show_all(ang)
        bp.titlebar.set_visible(not ang)
        back.set_visible(len(screen._cur_panels) > 1)
        nav.sync(screen._cur_panels)

    bp.add_content = add_content
    nav.box.show_all()
