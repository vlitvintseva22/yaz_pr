# coding: utf-8
# license: GPLv3

"""
Чтение и запись конфигурации Солнечной системы из/в .txt файл.

Формат файла
============
Комментарии начинаются с #. Пустые строки игнорируются.
Три типа записей:

  Star   x  y  mass  color  R  label
  Planet star_idx  orbit_r  angle_deg  color  R  mass
  Satellite  planet_idx  orbit_r  angle_deg  color  R  mass

Пример:
  Star -110 90 100.0 #FFD700 13 Звезда_1
  Planet 0 30 45.0 #00FF80 6 5.0
  Satellite 3 20 0.0 white 3 0.1

Примечания:
  - star_idx   — номер звезды в порядке следования Star-строк (с нуля)
  - planet_idx — номер планеты в порядке следования Planet-строк (с нуля)
  - angle_deg  — начальный угол в ГРАДУСАХ (в файле градусы, в объектах радианы)
  - label содержит пробелы → в файле заменяются на _ (Звезда_1 ↔ Звезда 1)
  - начальные скорости ВЫЧИСЛЯЮТСЯ из условия круговой орбиты v=sqrt(G*M/r),
    а НЕ хранятся в файле — файл описывает геометрию, физика пересчитывается
"""

import math
from solar_objects import Star, Planet, Satellite


def read_space_objects_data_from_file(input_filename):
    """
    Читает конфигурацию из файла, возвращает (stars, planets, satellites).

    Начальные скорости объектов вычисляются автоматически:
      - планета:  v = sqrt(G*M_star / r), направление — перпендикулярно радиусу (CCW)
      - спутник:  v_sat = sqrt(G*M_planet / r_sat), добавляется к скорости планеты
    """
    from solar_model import G

    stars      = []
    planets    = []
    satellites = []

    with open(input_filename, encoding="utf-8") as f:
        for lineno, raw in enumerate(f, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            obj_type = parts[0]

            # ── Star ──────────────────────────────────────────────────
            if obj_type == "Star":
                if len(parts) < 7:
                    raise ValueError(f"Строка {lineno}: недостаточно полей для Star")
                x, y   = float(parts[1]), float(parts[2])
                mass   = float(parts[3])
                color  = parts[4]
                R      = int(parts[5])
                label  = parts[6].replace("_", " ")

                star = Star(x, y, color=color, R=R, label=label, mass=mass)
                stars.append(star)

            # ── Planet ────────────────────────────────────────────────
            elif obj_type == "Planet":
                if len(parts) < 7:
                    raise ValueError(f"Строка {lineno}: недостаточно полей для Planet")
                star_idx = int(parts[1])
                orbit_r  = float(parts[2])
                angle    = math.radians(float(parts[3]))
                color    = parts[4]
                R        = int(parts[5])
                mass     = float(parts[6])

                if star_idx >= len(stars):
                    raise ValueError(
                        f"Строка {lineno}: star_idx={star_idx}, "
                        f"а звёзд загружено только {len(stars)}"
                    )
                star = stars[star_idx]

                p = Planet(star, orbit_r, angle, color=color, R=R, mass=mass)

                # Скорость круговой орбиты: v = sqrt(G*M_star/r), CCW
                v = math.sqrt(G * star.mass / orbit_r)
                p.vx = -math.sin(angle) * v
                p.vy =  math.cos(angle) * v

                # Обновляем список орбитальных радиусов звезды
                if orbit_r not in star.orbit_radii:
                    star.orbit_radii.append(orbit_r)
                    star.orbit_radii.sort()

                planets.append(p)

            # ── Satellite ─────────────────────────────────────────────
            elif obj_type == "Satellite":
                if len(parts) < 7:
                    raise ValueError(f"Строка {lineno}: недостаточно полей для Satellite")
                planet_idx = int(parts[1])
                orbit_r    = float(parts[2])
                angle      = math.radians(float(parts[3]))
                color      = parts[4]
                R          = int(parts[5])
                mass       = float(parts[6])

                if planet_idx >= len(planets):
                    raise ValueError(
                        f"Строка {lineno}: planet_idx={planet_idx}, "
                        f"а планет загружено только {len(planets)}"
                    )
                planet = planets[planet_idx]

                sat = Satellite(planet, orbit_r, angle, color=color, R=R, mass=mass)

                # Скорость в инерциальной СО = v_планеты + орбитальная_скорость
                from solar_model import G
                v_sat = math.sqrt(G * planet.mass / orbit_r)
                sat.vx = planet.vx + (-math.sin(angle) * v_sat)
                sat.vy = planet.vy + ( math.cos(angle) * v_sat)

                planet.satellites.append(sat)
                satellites.append(sat)

            else:
                # Неизвестный тип — игнорируем с предупреждением
                print(f"[solar_input] строка {lineno}: неизвестный тип '{obj_type}', пропускаю")

    return stars, planets, satellites


def write_space_objects_data_to_file(output_filename, stars, planets, satellites):
    """
    Записывает текущую геометрию системы в файл.

    Сохраняются: положение, масса, цвет, размер всех объектов.
    Скорости НЕ сохраняются — при загрузке они пересчитываются из orbit_r и angle.
    (Если нужен save/resume, достаточно сохранить текущий angle = atan2(y-cy, x-cx).)
    """
    star_idx   = {id(s): i for i, s in enumerate(stars)}
    planet_idx = {id(p): i for i, p in enumerate(planets)}

    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("# Солнечная система — конфигурационный файл\n")
        f.write("# Формат:\n")
        f.write("#   Star   x  y  mass  color  R  label\n")
        f.write("#   Planet star_idx  orbit_r  angle_deg  color  R  mass\n")
        f.write("#   Satellite  planet_idx  orbit_r  angle_deg  color  R  mass\n")
        f.write("#\n")
        f.write("# angle_deg — начальный угол в градусах\n")
        f.write("# Скорости пересчитываются при загрузке: v = sqrt(G*M/r)\n")
        f.write("\n")

        # ── Звёзды ────────────────────────────────────────────────────
        for star in stars:
            label_safe = star.label.replace(" ", "_")
            f.write(
                f"Star  {star.x}  {star.y}  {star.mass}  "
                f"{star.color}  {star.R}  {label_safe}\n"
            )

        f.write("\n")

        # ── Планеты ───────────────────────────────────────────────────
        for p in planets:
            # Берём угол из текущего положения (актуально при save mid-run)
            angle_deg = math.degrees(
                math.atan2(p.y - p.star.y, p.x - p.star.x)
            ) % 360
            s_idx = star_idx[id(p.star)]
            f.write(
                f"Planet  {s_idx}  {p.orbit_radius}  {angle_deg:.4f}  "
                f"{p.color}  {p.R}  {p.mass}\n"
            )

        f.write("\n")

        # ── Спутники ──────────────────────────────────────────────────
        for sat in satellites:
            angle_deg = math.degrees(
                math.atan2(sat.y - sat.planet.y, sat.x - sat.planet.x)
            ) % 360
            p_idx = planet_idx[id(sat.planet)]
            f.write(
                f"Satellite  {p_idx}  {sat.orbit_radius}  {angle_deg:.4f}  "
                f"{sat.color}  {sat.R}  {sat.mass}\n"
            )


if __name__ == "__main__":
    print("This module is not for direct call!")
