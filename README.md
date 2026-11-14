# ANG_Ender_screen

Нов потребителски интерфейс (тема + нов начален екран) за [KlipperScreen](https://github.com/KlipperScreen/KlipperScreen), вдъхновен от изчистения стил на Bambu Lab принтерите.

Целеви екран: **4.3" 800×480 HDMI тъч екран**.

## Какво има в момента
**Тема `ang-bambu`** (`styles/ang-bambu/`):
- тъмен фон `#141414`, карти `#242424` със заоблени ъгли
- син акцент `#3DA5FF` и синьо сияние около бутоните
- избран елемент: синя рамка и тъмносин фон
- иконите засега са от `material-dark` и ще бъдат заменени

**Добавка `ang_ender`** (`addons/ang_ender/`), зарежда се чрез вградения механизъм за добавки на KlipperScreen (`enable_addons`), без промени по кода му:
- лява навигация: Начало · Управление · AMF · Устройство · Съобщения · авариен стоп
- страници: начало, управление, въздух, вентилатор, дюза и екструдер, температура (numpad), движение, скорост, AMF, редакция на слот, сушене, устройство, списъци (калибрация, инструменти), печат
- местата за рендери се попълват сами, щом сложиш PNG файловете — [docs/RENDERS.md](docs/RENDERS.md)
- имената на обектите в Klipper (камера, вентилатори, светлина) са в `addons/ang_ender/config.py`
- екранът по време на печат (`ang_job`, по подредбата на H2S) замества стандартния; стандартният се връща, като се закоментира `job_status` в `OVERRIDES` в `addons/ang_ender/__init__.py`

## Как изглежда
Снимки 800×480 от истинския код на страниците с изкуствени данни за принтера (`tools/preview_pages.py`).
Пунктирните рамки са местата за рендерите от SolidWorks — списъкът е в [docs/RENDERS.md](docs/RENDERS.md).

| | | |
|---|---|---|
| ![](docs/preview/01-home.png) | ![](docs/preview/02-control.png) | ![](docs/preview/03-air.png) |
| ![](docs/preview/04-fan-part.png) | ![](docs/preview/05-nozzle.png) | ![](docs/preview/06-numpad-bed.png) |
| ![](docs/preview/07-motion.png) | ![](docs/preview/08-speed.png) | ![](docs/preview/09-amf.png) |
| ![](docs/preview/09b-amf-page2.png) | | |
| ![](docs/preview/10-amf-edit.png) | ![](docs/preview/11-amf-dry.png) | ![](docs/preview/12-device.png) |
| ![](docs/preview/13-calibration.png) | ![](docs/preview/14-printing.png) | ![](docs/preview/15-print-done.png) |

Прегенериране (нужни са GTK3, python3-gi-cairo и Xvfb):

```bash
xvfb-run -a -s "-screen 0 800x480x24" python3 tools/preview_pages.py ~/KlipperScreen $PWD $PWD/docs/preview
```

## Инсталация
Изисква **KlipperScreen v0.4.8 или по-нов** (тогава са въведени добавките, `enable_addons`).
По-стара версия спира с „Option enable_addons not recognized“ — обнови с `cd ~/KlipperScreen && git pull`.

На Raspberry Pi-то с KlipperScreen:

```bash
cd ~ && git clone https://github.com/ageorgiev86/ANG_Ender_screen.git
```

```bash
~/ANG_Ender_screen/install.sh
```

След това в KlipperScreen:
1. **Settings → Icon Theme → ang-bambu**
2. **Settings → Enable Add-ons** (включи), после рестартирай KlipperScreen

Препоръчително за 800×480 в `KlipperScreen.conf`, секция `[main]`:

```ini
theme: ang-bambu
font_size: small
enable_addons: True
```

Ако темата не се прилага: KlipperScreen пази настройките, сменени от екрана, най-долу в
`KlipperScreen.conf` (под `#~# --- Do not edit below this line ---`) и те надделяват. Провери:

```bash
grep -n "theme" ~/printer_data/config/KlipperScreen.conf
```

Ред `#~# theme = ...` трябва също да е `ang-bambu`.

Обновяване:

```bash
cd ~/ANG_Ender_screen && git pull
```

## План
- [x] Тема: цветове и форми
- [ ] Собствени икони в стил Bambu
- [x] Изчистен начален екран
- [x] Страници за управление, AMF и устройство (чакат рендерите)
- [ ] Изпробване на истинския принтер и включване на екрана по време на печат
- [ ] Плочки за температури и вентилатори

## Лиценз
AGPL-3.0, както KlipperScreen (иконите са производни на темата material-dark).
