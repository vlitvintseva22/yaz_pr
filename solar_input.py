# coding: utf-8
# license: GPLv3

"""
Чтение и запись конфигурации системы в .txt файл.

  Star       x  y  mass  color  R  label
  Planet     star_idx    orbit_r  angle_deg  color  R  mass
  Satellite  planet_idx  orbit_r  angle_deg  color  R  mass

  • star_idx / planet_idx — номера в порядке следования (с нуля)
  • angle_deg — начальный угол в градусах (в объектах хранится в радианах)
  • в label пробелы заменяются на _ (Звезда_1 ↔ Звезда 1)

"""

import math

from solar_objects import Star, Planet, Satellite
from solar_model import Simulation


def load_system(filename):
    """Читает файл и возвращает готовую Simulation с пересчитанными скоростями."""
    sim = Simulation()

    with open(filename, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            kind = parts[0]

            if kind == "Star":
                _require(parts, 7, lineno, "Star")
                star = Star(
                    x=float(parts[1]), y=float(parts[2]), mass=float(parts[3]),
                    color=parts[4], R=int(parts[5]), label=parts[6].replace("_", " "),
                )
                sim.stars.append(star)

            elif kind == "Planet":
                _require(parts, 7, lineno, "Planet")
                star_idx = int(parts[1])
                if star_idx >= len(sim.stars):
                    raise ValueError(f"Строка {lineno}: star_idx={star_idx}, "
                                     f"а звёзд загружено {len(sim.stars)}")
                star = sim.stars[star_idx]
                angle = math.radians(float(parts[3]))

                planet = Planet(star, orbit_radius=float(parts[2]), angle=angle,
                                color=parts[4], R=int(parts[5]), mass=float(parts[6]))
                planet.set_circular_orbit()
                sim.planets.append(planet)

                if planet.orbit_radius not in star.orbit_radii:
                    star.orbit_radii.append(planet.orbit_radius)
                    star.orbit_radii.sort()

            elif kind == "Satellite":
                _require(parts, 7, lineno, "Satellite")
                planet_idx = int(parts[1])
                if planet_idx >= len(sim.planets):
                    raise ValueError(f"Строка {lineno}: planet_idx={planet_idx}, "
                                     f"а планет загружено {len(sim.planets)}")
                planet = sim.planets[planet_idx]
                angle = math.radians(float(parts[3]))

                sat = Satellite(planet, orbit_radius=float(parts[2]), angle=angle,
                                color=parts[4], R=int(parts[5]), mass=float(parts[6]))
                sat.set_circular_orbit()
                planet.satellites.append(sat)
                sim.satellites.append(sat)

            else:
                print(f"[solar_input] строка {lineno}: неизвестный тип '{kind}', пропускаю")

    return sim


def save_system(filename, sim):
    """Сохраняет геометрию системы в файл (скорости не пишутся — они пересчитываются)."""
    star_index = {id(s): i for i, s in enumerate(sim.stars)}
    planet_index = {id(p): i for i, p in enumerate(sim.planets)}

    with open(filename, "w", encoding="utf-8") as f:
        f.write("# Солнечная система — конфигурационный файл\n")
        f.write("# Формат:\n")
        f.write("#   Star   x  y  mass  color  R  label\n")
        f.write("#   Planet star_idx  orbit_r  angle_deg  color  R  mass\n")
        f.write("#   Satellite  planet_idx  orbit_r  angle_deg  color  R  mass\n")
        f.write("#\n")
        f.write("# angle_deg — начальный угол в градусах\n")
        f.write("# Скорости пересчитываются при загрузке: v = sqrt(G*M/r)\n\n")

        for star in sim.stars:
            label_safe = star.label.replace(" ", "_")
            f.write(f"Star  {star.x}  {star.y}  {star.mass}  "
                    f"{star.color}  {star.R}  {label_safe}\n")
        f.write("\n")

        for p in sim.planets:
            angle_deg = math.degrees(math.atan2(p.y - p.star.y, p.x - p.star.x)) % 360
            f.write(f"Planet  {star_index[id(p.star)]}  {p.orbit_radius}  "
                    f"{angle_deg:.4f}  {p.color}  {p.R}  {p.mass}\n")
        f.write("\n")

        for sat in sim.satellites:
            angle_deg = math.degrees(
                math.atan2(sat.y - sat.planet.y, sat.x - sat.planet.x)) % 360
            f.write(f"Satellite  {planet_index[id(sat.planet)]}  {sat.orbit_radius}  "
                    f"{angle_deg:.4f}  {sat.color}  {sat.R}  {sat.mass}\n")


def _require(parts, n, lineno, kind):
    """Проверяет, что в строке достаточно полей."""
    if len(parts) < n:
        raise ValueError(f"Строка {lineno}: недостаточно полей для {kind}")


if __name__ == "__main__":
    print("This module is not for direct call!")
