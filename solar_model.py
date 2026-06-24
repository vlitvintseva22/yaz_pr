# coding: utf-8
# license: GPLv3

"""
Модель всей системы.

Класс Simulation хранит все тела (звёзды, планеты, спутники) и временем
управляет одним методом step(dt). Внутри одного шага:

  1) каждая планета делает свой шаг движения      (Planet.step)
  2) касающиеся планеты сливаются                  (_merge_planets)
  3) планеты, упавшие на звезду, поглощаются ею    (_absorb_into_stars)
  4) каждый спутник делает свой шаг                 (Satellite.step)

Сама физика движения и слияния — в методах тел (solar_objects). Здесь
только «оркестровка»: кто за кем ходит и что удалить.

Орбиты ВСЕХ пар звёзд пересекаются (звёзды стоят кучно, см.
build_default_system), но планеты НЕ сталкиваются (по заданию): по
умолчанию interactions=False и планеты спокойно проходят сквозь точки
пересечения орбит. Флаг interactions=True — необязательный режим, в
котором планеты начинают сталкиваться, сливаться и падать на звёзды.

Функция build_default_system() собирает систему из 4 звёзд по умолчанию.
"""

import math

from solar_objects import Star, Planet, Satellite, G


# ═══════════════════════════════════════════════════════════════════
#  КЛАСС СИМУЛЯЦИИ
# ═══════════════════════════════════════════════════════════════════

class Simulation:
    """Содержит все тела и продвигает их во времени."""

    def __init__(self, stars=None, planets=None, satellites=None, interactions=False):
        self.stars = stars if stars is not None else []
        self.planets = planets if planets is not None else []
        self.satellites = satellites if satellites is not None else []
        self.time = 0.0
        # ПО ЗАДАНИЮ планеты НЕ сталкиваются — поэтому по умолчанию False:
        #   планеты проходят сквозь точки пересечения орбит, ничего не сливается.
        # interactions=True — необязательный «весёлый» режим: планеты
        #   сталкиваются, сливаются и падают на звёзды (для зачёта держать False).
        self.interactions = interactions

    def step(self, dt):
        """
        Один шаг всей системы. Возвращает (removed_planets, removed_satellites) —
        тела, исчезнувшие за этот шаг (нужно вызывающему, чтобы стереть их с холста).
        """
        # Положения планет на начало кадра нужны спутникам для интерполяции.
        old_pos = {id(p): (p.x, p.y) for p in self.planets}

        # 1) Планеты движутся под притяжением своих звёзд.
        for planet in self.planets:
            planet.step(dt)

        # 2-3) Столкновения: слияние касающихся планет + поглощение звёздами.
        removed_planets = []
        removed_satellites = []
        if self.interactions:
            removed_planets = self._merge_planets()
            absorbed, removed_satellites = self._absorb_into_stars()
            removed_planets += absorbed

        # 4) Спутники движутся (чувствуют и планету, и звезду).
        for sat in self.satellites:
            sat.step(dt, old_pos[id(sat.planet)])

        self.time += dt
        return removed_planets, removed_satellites

    def fit_to_screen(self, half_w, half_h, margin=12):
        """
        Масштабирует всю систему так, чтобы она крупно заполнила холст
        (центр холста = точка (0, 0)). Все координаты и радиусы орбит
        умножаются на один коэффициент, поэтому пересечения орбит и
        «звёзды вне орбит» сохраняются, а скорости пересчитываются под
        новые радиусы. Вызывать ДО запуска анимации.

        Чем крупнее система, тем мельче планеты относительно орбит —
        тем реже они визуально накладываются.
        """
        ext_x = max(abs(s.x) + max(s.orbit_radii) for s in self.stars)
        ext_y = max(abs(s.y) + max(s.orbit_radii) for s in self.stars)
        s = min((half_w - margin) / ext_x, (half_h - margin) / ext_y)

        for star in self.stars:
            star.x *= s
            star.y *= s
            star.orbit_radii = [r * s for r in star.orbit_radii]
        for p in self.planets:
            p.x *= s
            p.y *= s
            p.orbit_radius *= s
            p.set_circular_orbit()
        for sat in self.satellites:
            sat.x *= s
            sat.y *= s
            sat.orbit_radius *= s
            sat.set_circular_orbit()

    # ── Слияние планет ──────────────────────────────────────────────
    def _merge_planets(self):
        """
        Сливает все касающиеся пары планет. Выживает более массивная
        (при равенстве — первая) и поглощает другую через Planet.absorb.
        Возвращает список исчезнувших планет.
        """
        absorbed = set()
        removed = []
        ps = self.planets
        n = len(ps)

        for i in range(n):
            a = ps[i]
            if id(a) in absorbed:
                continue
            for j in range(i + 1, n):
                b = ps[j]
                if id(b) in absorbed:
                    continue
                if not a.touches(b):
                    continue

                survivor, victim = (a, b) if a.mass >= b.mass else (b, a)
                survivor.absorb(victim)
                absorbed.add(id(victim))
                removed.append(victim)

                if victim is a:          # внешнюю планету a поглотили — её цикл окончен
                    break

        if absorbed:
            self.planets = [p for p in ps if id(p) not in absorbed]
        return removed

    # ── Поглощение планет звёздами ──────────────────────────────────
    def _absorb_into_stars(self):
        """
        Планеты, коснувшиеся любой звезды, падают на неё (Star.absorb).
        Их спутники исчезают вместе с ними.
        Возвращает (removed_planets, removed_satellites).
        """
        survivors = []
        removed_planets = []
        removed_satellites = []

        for p in self.planets:
            hit = next((s for s in self.stars if p.touches(s)), None)
            if hit is None:
                survivors.append(p)
                continue

            hit.absorb(p)
            removed_planets.append(p)
            removed_satellites.extend(p.satellites)
            p.satellites = []

        if removed_planets:
            self.planets = survivors
        if removed_satellites:
            dead = {id(s) for s in removed_satellites}
            self.satellites = [s for s in self.satellites if id(s) not in dead]

        return removed_planets, removed_satellites


# ═══════════════════════════════════════════════════════════════════
#  ПОСТРОЕНИЕ СИСТЕМЫ ПО УМОЛЧАНИЮ
# ═══════════════════════════════════════════════════════════════════

ORBIT_BASE = 30      # радиус первой орбиты (пикс.)
ORBIT_STEP = 25      # шаг между орбитами (пикс.)
MAX_PER_ORBIT = 3    # максимум планет на одной орбите
PLANET_RADIUS = 6    # визуальный размер планеты (пикс.)
SAT_ORBIT_R = 10     # радиус орбиты спутника
SAT_RADIUS = 2       # визуальный размер спутника (пикс.)

# Массы подобраны так, чтобы G·M совпадало со «старыми» числами (100/5/0.1),
# поэтому скорости и орбиты выглядят как раньше, а G — настоящая.
STAR_MASS = 100.0 / G
PLANET_MASS = 5.0 / G
SAT_MASS = 0.1 / G

PLANET_COLORS = ["#00FF80", "#00AAFF", "#FF8800", "#FF44FF"]
STAR_COLORS = ["#FFD700", "#AAD4FF", "#FFA040", "#FFFFFF"]


def orbit_radius(n):
    """Радиус n-й орбиты (n начинается с 1)."""
    return ORBIT_BASE + (n - 1) * ORBIT_STEP


def build_default_system():
    """
    Собирает систему из 4 звёзд с планетами и спутниками.

    Главный приём (чтобы орбиты пересекались, а планеты НЕ сталкивались, и
    при этом БЕЗ кинематики): орбиты разных звёзд имеют ОБЩИЕ радиусы, а
    звёзды стоят почти в одной точке (тесный квадрат, меньше шага орбит).
    Тогда:
      • пересекаются ТОЛЬКО орбиты одинакового радиуса. У них одинаковый
        период (T=2π√(r³/GM)), поэтому планеты на них движутся синхронно и
        держат постоянное расстояние;
      • орбиты разных радиусов друг с другом не пересекаются вовсе.
    Стартовые фазы звёзд подобраны (перебором) так, что синхронные планеты
    разных звёзд никогда не сближаются → планеты не сталкиваются и не
    проходят сквозь чужие звёзды, хотя орбиты пересекаются.

    Радиусы по уровням (индекс L → радиус 30+25·L). Каждый уровень есть как
    минимум у двух звёзд → каждая орбита с кем-то пересекается:
      Звезда1: 0,1,2,3                 Звезда2: 0,1,2,7,8
      Звезда3: 0,1,2,3,4,5,6           Звезда4: 0,1,2,3,4,5,6,7,8
    """
    # (x, y, индексы уровней орбит (по возрастанию), спутники?, фаза°)
    star_data = [
        (-6,  6, [0, 1, 2, 3],                False, 324.2),
        ( 6,  6, [0, 1, 2, 7, 8],             True,  138.3),
        (-6, -6, [0, 1, 2, 3, 4, 5, 6],       False, 137.3),
        ( 6, -6, [0, 1, 2, 3, 4, 5, 6, 7, 8], True,  205.7),
    ]
    n_planets_per_star = [10, 15, 20, 25]

    sim = Simulation()
    for s_idx, (sx, sy, levels, has_sats, phase_deg) in enumerate(star_data):
        star = Star(sx, sy, mass=STAR_MASS, color=STAR_COLORS[s_idx],
                    label=f"Звезда {s_idx + 1}")
        star.orbit_radii = [orbit_radius(L + 1) for L in levels]   # 30 + 25·L
        sim.stars.append(star)

        phase0 = math.radians(phase_deg)
        n_planets = n_planets_per_star[s_idx]
        placed = 0
        for li, r in enumerate(star.orbit_radii):
            count = min(MAX_PER_ORBIT, n_planets - placed)
            is_last = (li == len(star.orbit_radii) - 1)   # последняя = внешняя орбита
            for k in range(count):
                angle = phase0 + 2.0 * math.pi * k / count
                planet = Planet(star, r, angle, R=PLANET_RADIUS,
                                color=PLANET_COLORS[s_idx], mass=PLANET_MASS)
                planet.set_circular_orbit()
                sim.planets.append(planet)

                # Спутники — у планет последней (внешней) орбиты звёзд 2 и 4.
                if has_sats and is_last:
                    for sat_k in range(2):
                        sat = Satellite(planet, SAT_ORBIT_R, math.pi * sat_k,
                                        mass=SAT_MASS, R=SAT_RADIUS)
                        sat.set_circular_orbit()
                        planet.satellites.append(sat)
                        sim.satellites.append(sat)
                placed += 1

    return sim


if __name__ == "__main__":
    print("This module is not for direct call!")
