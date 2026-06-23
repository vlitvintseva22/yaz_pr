# coding: utf-8
# license: GPLv3

"""
Главный модуль симуляции «Солнечной системы».

╔══════════════════════════════════════════════════════════════════╗
║  СОСТАВ СИСТЕМЫ                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║  Звезда 1: 10 планет  → 4 орбиты  (3+3+3+1)                     ║
║  Звезда 2: 15 планет  → 5 орбит   (3+3+3+3+3)                   ║
║            каждая планета на 5-й орбите имеет по 2 спутника     ║
║  Звезда 3: 20 планет  → 7 орбит   (3+3+3+3+3+3+2)              ║
║  Звезда 4: 25 планет  → 9 орбит   (3+3+3+3+3+3+3+3+1)          ║
║            планета на 9-й орбите имеет 2 спутника               ║
╠══════════════════════════════════════════════════════════════════╣
║  МЕХАНИКИ                                                        ║
║  • Все объекты вращаются в одном направлении (ω > 0)            ║
║  • Кинематические орбиты: столкновения исключены по построению  ║
║  • Орбиты планет всех 4 звёзд попарно пересекаются              ║
║  • Кнопка «Скрыть / Показать орбиты» в панели управления        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import tkinter
import math
import os

from solar_objects import Star, Planet, Satellite
from solar_model  import recalculate_positions, G
from solar_input  import (read_space_objects_data_from_file,
                          write_space_objects_data_to_file)
from solar_vis    import (
    window_width, window_height,
    add_trail_segment, clear_trail, toggle_trails,
    create_star_image, create_star_label,
    create_planet_image, create_satellite_image,
    update_object_position,
    create_legend,
)

# ═══════════════════════════════════════════════════════════════════
#  ПАРАМЕТРЫ ОРБИТ И ДВИЖЕНИЯ
# ═══════════════════════════════════════════════════════════════════

ORBIT_BASE    = 30      # радиус первой орбиты (пикс.)
ORBIT_STEP    = 25      # шаг между орбитами (пикс.)
MAX_PER_ORBIT = 3       # максимум планет на одной орбите
SAT_ORBIT_R   = 10      # радиус орбиты спутника (мал — внутри сферы Хилла,
                        # чтобы спутник как настоящее тело не улетал)
SAT_RADIUS    = 2       # визуальный размер спутника (пикс.)

# Массы выбраны так, чтобы G*M совпадало со старыми значениями (100/5/0.1
# при G=1) — орбиты и скорости визуально не меняются, просто G теперь
# настоящая гравитационная постоянная, а не выдуманная "1".
STAR_MASS     = 100.0 / G   # ≈ 1.498e12 кг
PLANET_MASS   = 5.0   / G   # ≈ 7.49e10  кг
SAT_MASS      = 0.1   / G   # ≈ 1.498e9  кг

# Файл конфигурации системы
SOLAR_FILE = "solar_system.txt"

# Цвета планет (по индексу звезды)
PLANET_COLORS = ["#00FF80", "#00AAFF", "#FF8800", "#FF44FF"]
# Цвета самих звёзд
STAR_COLORS   = ["#FFD700", "#AAD4FF", "#FFA040", "#FFFFFF"]


def orbit_radius(n: int) -> float:
    """Радиус n-й орбиты (n начинается с 1)."""
    return ORBIT_BASE + (n - 1) * ORBIT_STEP


def circular_velocity(r: float, M: float) -> float:
    """
    Скорость круговой орбиты радиуса r вокруг тела массой M.
    Из баланса: G*M/r² = v²/r  →  v = sqrt(G*M/r)
    G импортируется из solar_model.
    """
    from solar_model import G
    return math.sqrt(G * M / r)


# ═══════════════════════════════════════════════════════════════════
#  ПОСТРОЕНИЕ СИСТЕМЫ
# ═══════════════════════════════════════════════════════════════════

#
#  Расположение звёзд в модельных координатах (центр холста = (0,0)):
#
#      Звезда 1 (-110, 90)          Звезда 2 (110, 90)
#
#
#      Звезда 3 (-80, -90)          Звезда 4 (80, -90)
#
#  Расстояния между звёздами vs сумма максимальных радиусов орбит:
#
#   пара 1-2: dist=220   r1_max+r2_max=105+130=235  ✓ пересекаются
#   пара 1-3: dist=182   r1_max+r3_max=105+180=285  ✓
#   пара 1-4: dist=262   r1_max+r4_max=105+230=335  ✓
#   пара 2-3: dist=262   r2_max+r3_max=130+180=310  ✓
#   пара 2-4: dist=182   r2_max+r4_max=130+230=360  ✓
#   пара 3-4: dist=160   r3_max+r4_max=180+230=410  ✓
#
#  => орбиты планет ВСЕХ пар звёзд попарно пересекаются.
#

def create_solar_system():
    """
    Создаёт четыре звезды со всеми планетами и спутниками.
    Возвращает (stars, planets, satellites).
    """
    # (x, y, количество планет, есть ли спутники на последней орбите)
    star_configs = [
        (-110,  90, 10, False),   # Звезда 1
        ( 110,  90, 15, True),    # Звезда 2  — спутники на последней орбите
        ( -80, -90, 20, False),   # Звезда 3
        (  80, -90, 25, True),    # Звезда 4  — спутники на последней орбите
    ]

    stars:      list[Star]      = []
    planets:    list[Planet]    = []
    satellites: list[Satellite] = []

    for s_idx, (sx, sy, n_pl, has_sats) in enumerate(star_configs):
        label = f"Звезда {s_idx + 1}"
        star  = Star(sx, sy, color=STAR_COLORS[s_idx], label=label,
                     mass=STAR_MASS)

        n_orbits         = math.ceil(n_pl / MAX_PER_ORBIT)
        star.orbit_radii = [orbit_radius(i + 1) for i in range(n_orbits)]
        stars.append(star)

        # Начальный фазовый сдвиг для каждой звезды —
        # планеты разных звёзд не «толпятся» в одной точке при старте
        star_phase = s_idx * math.pi / 4.0

        planet_count = 0
        for o_idx in range(n_orbits):
            r         = star.orbit_radii[o_idx]
            remaining = n_pl - planet_count
            count     = min(MAX_PER_ORBIT, remaining)
            is_last   = (o_idx == n_orbits - 1)

            # Дополнительный фазовый сдвиг — соседние орбиты стартуют
            # с разных углов, планеты распределены красивее
            orbit_phase = o_idx * 0.8 + star_phase

            # Скорость круговой орбиты для данного радиуса
            v_orb = circular_velocity(r, star.mass)

            for k in range(count):
                phase = 2.0 * math.pi * k / count + orbit_phase
                p = Planet(star, r, phase,
                           color=PLANET_COLORS[s_idx],
                           mass=PLANET_MASS)

                # v = sqrt(G*M/r) перпендикулярно радиус-вектору (CCW)
                # радиус-вектор: (cos θ, sin θ)
                # перпендикуляр CCW: (−sin θ, cos θ)
                p.vx = -math.sin(phase) * v_orb
                p.vy =  math.cos(phase) * v_orb

                planets.append(p)

                # Спутники — только у планет на ПОСЛЕДНЕЙ орбите звёзд 2 и 4
                if has_sats and is_last:
                    v_sat = circular_velocity(SAT_ORBIT_R, PLANET_MASS)
                    for sat_k in range(2):
                        # 0 и π рад — спутники всегда по разные стороны
                        sat_phase = math.pi * sat_k
                        sat = Satellite(p, SAT_ORBIT_R, sat_phase,
                                        mass=SAT_MASS, R=SAT_RADIUS)

                        # Скорость в инерциальной СО =
                        #   скорость планеты + скорость по орбите вокруг планеты
                        sat.vx = p.vx + (-math.sin(sat_phase) * v_sat)
                        sat.vy = p.vy + ( math.cos(sat_phase) * v_sat)

                        p.satellites.append(sat)
                        satellites.append(sat)

                planet_count += 1

    return stars, planets, satellites


# ═══════════════════════════════════════════════════════════════════
#  ГЛОБАЛЬНОЕ СОСТОЯНИЕ
# ═══════════════════════════════════════════════════════════════════

perform_execution: bool  = False
physical_time:     float = 0.0
show_trails:       bool  = True

stars:      list = []
planets:    list = []
satellites: list = []

space          = None
start_button   = None
orbit_button   = None
displayed_time = None
time_step      = None
time_speed     = None


# ═══════════════════════════════════════════════════════════════════
#  УПРАВЛЕНИЕ АНИМАЦИЕЙ
# ═══════════════════════════════════════════════════════════════════

def execution():
    """Один шаг анимации."""
    global physical_time

    dt = time_step.get()
    # Удалённые за шаг тела (слияние планет + падение на звёзды)
    removed_planets, removed_sats = recalculate_positions(
        planets, satellites, stars, dt)
    for victim in removed_planets:
        if victim.image is not None:
            space.delete(victim.image)
        clear_trail(space, victim)       # стираем и его след
    for sat in removed_sats:
        if sat.image is not None:
            space.delete(sat.image)

    # Звёзды могли подрасти, поглотив планеты — обновляем их размер
    for star in stars:
        update_object_position(space, star)

    for p in planets:
        add_trail_segment(space, p)      # планета «дорисовывает» свою орбиту
        update_object_position(space, p)
    for sat in satellites:
        update_object_position(space, sat)

    physical_time += dt
    displayed_time.set("%.1f сек." % physical_time)

    if perform_execution:
        # задержка от 1 мс (скорость=100) до 101 мс (скорость=0)
        delay = 101 - int(time_speed.get())
        space.after(delay, execution)


def start_execution():
    global perform_execution
    perform_execution = True
    start_button.config(text="Пауза", command=stop_execution)
    execution()


def stop_execution():
    global perform_execution
    perform_execution = False
    start_button.config(text="Старт", command=start_execution)


def toggle_trail_display():
    """Переключает отображение следов и обновляет текст кнопки."""
    global show_trails
    show_trails = not show_trails
    toggle_trails(space, show_trails)
    orbit_button.config(
        text="Скрыть след" if show_trails else "Показать след"
    )


# ═══════════════════════════════════════════════════════════════════
#  ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════

def main():
    global physical_time, show_trails
    global stars, planets, satellites
    global space, start_button, orbit_button, displayed_time, time_step, time_speed

    physical_time = 0.0
    show_trails   = True

    # ── Загружаем систему из файла или генерируем дефолт ───────────
    if os.path.exists(SOLAR_FILE):
        print(f"[main] Загружаю конфигурацию из '{SOLAR_FILE}'")
        stars, planets, satellites = read_space_objects_data_from_file(SOLAR_FILE)
    else:
        print(f"[main] Файл '{SOLAR_FILE}' не найден — генерирую систему по умолчанию")
        stars, planets, satellites = create_solar_system()
        write_space_objects_data_to_file(SOLAR_FILE, stars, planets, satellites)
        print(f"[main] Конфигурация сохранена в '{SOLAR_FILE}'")

    # ── Окно ────────────────────────────────────────────────────────
    root = tkinter.Tk()
    root.title("Солнечная система — 4 звезды")
    root.resizable(False, False)

    space = tkinter.Canvas(root,
                           width=window_width,
                           height=window_height,
                           bg="#05050f")
    space.pack(side=tkinter.TOP)

    # ── Порядок отрисовки (нижние слои сначала) ─────────────────────
    # 1) Следы планет рисуются на лету в execution() и всегда уходят
    #    в самый нижний слой (tag_lower) — статичные орбиты больше не нужны.

    # 2) Звёзды + подписи
    for star in stars:
        create_star_image(space, star)
        create_star_label(space, star)

    # 3) Планеты
    for p in planets:
        create_planet_image(space, p)

    # 4) Спутники — поверх всего
    for sat in satellites:
        create_satellite_image(space, sat)

    # 5) Легенда (поверх фона, не перекрывает объекты)
    legend_data = [
        (f"Звезда {i+1} ({n}п)", PLANET_COLORS[i], n)
        for i, (_, _, n, _) in enumerate([
            (-110,  90, 10, False),
            ( 110,  90, 15, True),
            ( -80, -90, 20, False),
            (  80, -90, 25, True),
        ])
    ]
    create_legend(space, [(lbl, clr, n) for lbl, clr, n in legend_data])

    # ── Панель управления ────────────────────────────────────────────
    ctrl = tkinter.Frame(root, bg="#0d0d1f", pady=5)
    ctrl.pack(side=tkinter.BOTTOM, fill=tkinter.X)

    # Кнопка Старт/Пауза
    start_button = tkinter.Button(
        ctrl, text="Старт", command=start_execution,
        width=8, bg="#1e3a5f", fg="white", relief=tkinter.FLAT
    )
    start_button.pack(side=tkinter.LEFT, padx=8)

    # Шаг по времени
    tkinter.Label(ctrl, text="dt:", bg="#0d0d1f", fg="#aaaaaa").pack(side=tkinter.LEFT)
    time_step = tkinter.DoubleVar(value=1.0)
    tkinter.Entry(ctrl, textvariable=time_step, width=5,
                  bg="#1a1a2e", fg="white", insertbackground="white"
                  ).pack(side=tkinter.LEFT, padx=4)

    # Ползунок скорости
    tkinter.Label(ctrl, text="  Скорость:", bg="#0d0d1f", fg="#aaaaaa").pack(side=tkinter.LEFT)
    time_speed = tkinter.DoubleVar(value=50)
    tkinter.Scale(ctrl, variable=time_speed,
                  from_=0, to=100, orient=tkinter.HORIZONTAL,
                  length=130, showvalue=False,
                  bg="#0d0d1f", fg="white",
                  troughcolor="#1e3a5f", highlightthickness=0
                  ).pack(side=tkinter.LEFT)

    # Кнопка следов
    orbit_button = tkinter.Button(
        ctrl, text="Скрыть след", command=toggle_trail_display,
        width=15, bg="#1e3a5f", fg="white", relief=tkinter.FLAT
    )
    orbit_button.pack(side=tkinter.LEFT, padx=10)

    # Счётчик времени
    displayed_time = tkinter.StringVar(value="0.0 сек.")
    tkinter.Label(ctrl, textvariable=displayed_time,
                  width=16, bg="#0d0d1f", fg="#88aacc"
                  ).pack(side=tkinter.RIGHT, padx=8)

    root.mainloop()


if __name__ == "__main__":
    main()