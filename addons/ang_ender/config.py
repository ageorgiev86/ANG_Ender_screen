"""Настройки на ANG Ender UI, които зависят от printer.cfg.

Имената са обектите в Klipper (както ги вижда Moonraker). Ако някой липсва,
съответната плочка показва "--" и не праща команди.
"""

# Камера (затворената): сензор и нагревател
CHAMBER_SENSOR = "temperature_sensor chamber"
CHAMBER_HEATER = "heater_generic chamber"

# Вентилатори: ключ -> (обект в Klipper, име на екрана, рендер-слой)
FANS = {
    "part":    ("fan",                       "Охлаждане на детайла", "fan_part"),
    "aux":     ("fan_generic aux",           "Допълнителен",          "fan_aux"),
    "exhaust": ("fan_generic exhaust",       "Изсмукване",            "fan_exhaust"),
    "heat":    ("fan_generic chamber_circ",  "Циркулация на камерата", "fan_heat"),
}

# Осветление: G-code за вкл./изкл. и обект за четене на състоянието
LIGHT_OBJECT = "output_pin chamber_light"
LIGHT_ON = "SET_PIN PIN=chamber_light VALUE=1"
LIGHT_OFF = "SET_PIN PIN=chamber_light VALUE=0"

# Режими на скорост (M220)
SPEED_MODES = [
    ("Луд", 166),
    ("Спорт", 124),
    ("Стандарт", 100),
    ("Тих", 50),
]

# Режими на въздуха: (име, G-code макрос)
AIR_MODES = [
    ("Охлаждане", "ANG_AIR_COOLING"),
    ("Нагряване", "ANG_AIR_HEATING"),
]

# Колко слота AMF да се показват, ако модулът не съобщава max_slots
AMF_DEFAULT_SLOTS = 4
