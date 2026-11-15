"""Настройки на ANG Ender UI, които зависят от printer.cfg.

Имената са обектите в Klipper (както ги вижда Moonraker). Ако някой липсва,
съответната плочка показва "--" и не праща команди.
"""

# Камера (затворената): сензор и нагревател.
# В printer.cfg камерата е [heater_generic chamber] със собствен термистор,
# затова температурата се чете от нагревателя.
CHAMBER_SENSOR = "heater_generic chamber"
CHAMBER_HEATER = "heater_generic chamber"

# Вентилатори: ключ -> (обект в Klipper, име на екрана, рендер-слой)
# Показват се само тези, които съществуват в Klipper. Новите вентилатори от
# CoreXY преработката (допълнителен, изсмукване, циркулация) се добавят тук.
FANS = {
    "part":    ("fan",                    "Охлаждане на детайла",  "fan_part"),
    "chamber": ("fan_generic chamber_fan", "Вентилатор на камерата", "fan_chamber"),
    # "aux":     ("fan_generic aux",           "Допълнителен",           "fan_aux"),
    # "exhaust": ("fan_generic exhaust",       "Изсмукване",             "fan_exhaust"),
    # "heat":    ("fan_generic chamber_circ",  "Циркулация на камерата", "fan_heat"),
}

# Осветление: обект за четене на състоянието и G-code за вкл./изкл.
# Сега е лентата [neopixel bed_leds]; за output_pin смени и трите реда.
LIGHT_OBJECT = "neopixel bed_leds"
LIGHT_ON = "SET_LED LED=bed_leds RED=1 GREEN=1 BLUE=1"
LIGHT_OFF = "LED_OFF"

# Какво се движи по Z: "gantry" (порталът, както на Ender 3) или "bed"
# (леглото, след CoreXY преработката). Определя посоката на стрелките ↑/↓.
Z_MOVES = "gantry"

# Режими на скорост (M220)
SPEED_MODES = [
    ("Луд", 166),
    ("Спорт", 124),
    ("Стандарт", 100),
    ("Тих", 50),
]

# Режими на въздуха: (име, G-code макрос). Празно = изборът не се показва.
# Когато направиш макросите в printer.cfg, разкоментирай:
AIR_MODES = [
    # ("Охлаждане", "ANG_AIR_COOLING"),
    # ("Нагряване", "ANG_AIR_HEATING"),
]

# Колко слота AMF да се показват, ако модулът не съобщава max_slots
AMF_DEFAULT_SLOTS = 4
