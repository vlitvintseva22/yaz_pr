# coding: utf-8
# license: GPLv3

"""Классы космических объектов для симуляции Солнечной системы."""

import math


class Star:
    """Звезда — неподвижный центр системы."""
    type = "star"

    def __init__(self, x, y, color="yellow", R=13, label="", mass=100.0):
        self.x = x
        self.y = y
        self.color = color
        self.R = R
        self.label = label
        self.mass = mass            # масса звезды (нормализованные единицы)
        self.image = None
        self.orbit_radii = []       # радиусы орбит планет этой звезды


class Planet:
    """Планета, движущаяся под действием гравитации своей звезды."""
    type = "planet"

    def __init__(self, star, orbit_radius, angle0, color="#00FF80", R=6, mass=5.0):
        """
        star          — родительская звезда
        orbit_radius  — начальный радиус орбиты (пикс.)
        angle0        — начальный угол (рад.)
        mass          — масса планеты (нужна спутникам)
        vx, vy задаются снаружи сразу после создания
        """
        self.star = star
        self.orbit_radius = orbit_radius   # хранится для отрисовки орбит
        self.angle = angle0
        self.mass = mass
        self.color = color
        self.R = R
        self.x = star.x + orbit_radius * math.cos(angle0)
        self.y = star.y + orbit_radius * math.sin(angle0)
        self.vx = 0.0
        self.vy = 0.0
        self.image = None
        self.satellites = []        # список спутников этой планеты


class Satellite:
    """Спутник, движущийся под действием гравитации своей планеты."""
    type = "satellite"

    def __init__(self, planet, orbit_radius, angle0, color="white", R=3, mass=0.1):
        """
        planet        — родительская планета
        orbit_radius  — начальный радиус орбиты (пикс.)
        angle0        — начальный угол (рад.)
        vx, vy задаются снаружи сразу после создания
        """
        self.planet = planet
        self.orbit_radius = orbit_radius
        self.angle = angle0
        self.mass = mass
        self.color = color
        self.R = R
        self.x = planet.x + orbit_radius * math.cos(angle0)
        self.y = planet.y + orbit_radius * math.sin(angle0)
        self.vx = 0.0
        self.vy = 0.0
        self.image = None


if __name__ == "__main__":
    print("This module is not for direct call!")