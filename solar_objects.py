# coding: utf-8
# license: GPLv3

"""
Космические тела симуляции.

Иерархия классов (наследование):

    SpaceBody                 ← общее: координаты, скорость, масса, рисование
      ├── Star                ← звезда 
      ├── Planet              ← планета (летает вокруг звезды, имеет спутники)
      └── Satellite           ← спутник (летает вокруг планеты)

Каждое тело САМО умеет:
  • вычислять притяжение к другому телу      (gravity_from)
  • проверять столкновение                    (touches)
  • сливаться с другим телом                  (absorb)
  • двигаться на шаг dt                        (step)
  • рисовать себя на поверхности              (render / render_orbits / render_trail)

"""

import math
from collections import deque

import pygame

from solar_vis import TRAIL_MAX, to_rgb, get_font, ORBIT_COLOR

#  ФИЗИЧЕСКИЕ КОНСТАНТЫ И ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ

G = 6.674e-11

SATELLITE_SUBSTEPS = 20


def gravity_acceleration(x, y, cx, cy, mass_center):
    """
    Ускорение тела в точке (x, y) от притяжения центра (cx, cy) массой mass_center.

        a = G · M / r²   (направлено к центру)

    """
    dx = cx - x
    dy = cy - y
    r2 = dx * dx + dy * dy
    if r2 < 1e-6:
        return 0.0, 0.0
    r = math.sqrt(r2)
    a = G * mass_center / r2
    return a * dx / r, a * dy / r


def circular_speed(mass_center, radius):
    """Скорость круговой орбиты радиуса radius вокруг массы mass_center: v = √(G·M/r)."""
    return math.sqrt(G * mass_center / radius)

#  БАЗОВЫЙ КЛАСС

class SpaceBody:
    """Тело: координаты, скорость, массу, размер и цвет."""

    def __init__(self, x, y, mass, color, R):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.mass = mass
        self.color = color
        self.R = R

    #  Физика, общая для всех тел 
    def gravity_from(self, other):
        """Ускорение этого тела от притяжения."""
        return gravity_acceleration(self.x, self.y, other.x, other.y, other.mass)

    def touches(self, other):
        """True, если тела соприкасаются (расстояние между центрами < сумма радиусов)."""
        dx = other.x - self.x
        dy = other.y - self.y
        rsum = self.R + other.R
        return dx * dx + dy * dy < rsum * rsum

    #  Рисование (immediate-mode pygame: тело рисуется каждый кадр) 
    def render(self, surface, view):
        
        pygame.draw.circle(surface, to_rgb(self.color),
                           (view.sx(self.x), view.sy(self.y)), int(self.R))

#  ЗВЕЗДА

class Star(SpaceBody):
    """Звезда — неподвижный центр."""

    def __init__(self, x, y, mass, color="yellow", R=13, label=""):
        super().__init__(x, y, mass, color, R)
        self.label = label
        self.orbit_radii = []      # радиусы орбит её планет

    def render(self, surface, view):
        """Звезда"""
        sx, sy, r = view.sx(self.x), view.sy(self.y), int(self.R)
        pygame.draw.circle(surface, to_rgb(self.color), (sx, sy), r)
        pygame.draw.circle(surface, (255, 165, 0), (sx, sy), r, 2)   # обводка
        if self.label:
            font = get_font(11, bold=True)
            text = font.render(self.label, True, (255, 255, 255))
            surface.blit(text, (sx - text.get_width() // 2, sy - r - 16))

    def render_orbits(self, surface, view):
        
        cx, cy = view.sx(self.x), view.sy(self.y)
        for r in self.orbit_radii:
            if r >= 1:
                pygame.draw.circle(surface, ORBIT_COLOR, (cx, cy), int(r), 1)

    def absorb(self, planet):
        """Поглощает упавшую планету: набирает её массу и растёт по площади."""
        self.mass += planet.mass
        self.R = math.hypot(self.R, planet.R)   # √(R₁² + R₂²) — сохранение площади

#  ПЛАНЕТА

class Planet(SpaceBody):
    """Планета: движется под притяжением своей звезды."""

    def __init__(self, star, orbit_radius, angle, color="#00FF80", R=6, mass=5.0):
        # Начальное положение — на орбите своей звезды под углом angle.
        x = star.x + orbit_radius * math.cos(angle)
        y = star.y + orbit_radius * math.sin(angle)
        super().__init__(x, y, mass, color, R)

        self.star = star
        self.orbit_radius = orbit_radius   
        self.angle = angle
        self.satellites = []

        self.prev_x = x
        self.prev_y = y

        self._trail_points = deque()

    def set_circular_orbit(self):
        """Задаёт скорость круговой орбиты вокруг своей звезды."""
        v = circular_speed(self.star.mass, self.orbit_radius)
        self.vx = -math.sin(self.angle) * v
        self.vy = math.cos(self.angle) * v

    def step(self, dt):
        
        self.prev_x, self.prev_y = self.x, self.y
        ax, ay = self.gravity_from(self.star)
        self.vx += ax * dt
        self.vy += ay * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    def absorb(self, other):
       
        M = self.mass + other.mass
        self.x = (self.mass * self.x + other.mass * other.x) / M
        self.y = (self.mass * self.y + other.mass * other.y) / M
        self.vx = (self.mass * self.vx + other.mass * other.vx) / M
        self.vy = (self.mass * self.vy + other.mass * other.vy) / M
        self.R = math.hypot(self.R, other.R)
        self.mass = M

        for sat in other.satellites:
            sat.planet = self
            self.satellites.append(sat)
        other.satellites = []

    # ── След ───────────────────────────────────────────────────────
    def record_trail(self, view):
        
        self._trail_points.append((view.sx(self.x), view.sy(self.y)))
        if len(self._trail_points) > TRAIL_MAX:
            self._trail_points.popleft()

    def render_trail(self, surface):
       
        if len(self._trail_points) >= 2:
            pygame.draw.lines(surface, to_rgb(self.color), False,
                              list(self._trail_points), 1)

    def clear_trail(self):
        
        self._trail_points.clear()


#  СПУТНИК

class Satellite(SpaceBody):

    def __init__(self, planet, orbit_radius, angle, color="white", R=3, mass=0.1):
        x = planet.x + orbit_radius * math.cos(angle)
        y = planet.y + orbit_radius * math.sin(angle)
        super().__init__(x, y, mass, color, R)

        self.planet = planet
        self.orbit_radius = orbit_radius
        self.angle = angle

    def set_circular_orbit(self):
        
        v = circular_speed(self.planet.mass, self.orbit_radius)
        self.vx = self.planet.vx - math.sin(self.angle) * v
        self.vy = self.planet.vy + math.cos(self.angle) * v

    def step(self, dt):
        
        planet = self.planet
        star = planet.star
        px0, py0 = planet.prev_x, planet.prev_y  
        px1, py1 = planet.x, planet.y            

        sub_dt = dt / SATELLITE_SUBSTEPS
        for k in range(SATELLITE_SUBSTEPS):
            frac = (k + 0.5) / SATELLITE_SUBSTEPS
            ppx = px0 + (px1 - px0) * frac     
            ppy = py0 + (py1 - py0) * frac

            apx, apy = gravity_acceleration(self.x, self.y, ppx, ppy, planet.mass)
            asx, asy = gravity_acceleration(self.x, self.y, star.x, star.y, star.mass)

            self.vx += (apx + asx) * sub_dt
            self.vy += (apy + asy) * sub_dt
            self.x += self.vx * sub_dt
            self.y += self.vy * sub_dt


if __name__ == "__main__":
    print("This module is not for direct call!")
