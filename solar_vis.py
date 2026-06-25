# coding: utf-8
# license: GPLv3

"""
(pygame).

  Viewport — переводит физические координаты в экранные.
  to_rgb / get_font — утилиты-мемоизации (просто кэш разобранных цветов и шрифтов).
  draw_legend — рисование легенды.
"""

import os

import pygame

TRAIL_MAX = 140                 # макс. число точек следа на одну планету

_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    r"C:\Windows\Fonts\tahoma.ttf",
)

ORBIT_COLOR = (58, 58, 106)     
LEGEND_COLOR = (204, 204, 204)


class Viewport:
    """
    Преобразует физические координаты в экранные.

    Центр области рисования соответствует точке (0, 0) физических координат
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2

    def sx(self, x):
        
        return int(x) + self.cx

    def sy(self, y):
       
        return -int(y) + self.cy


# Цвета и шрифты 
# Цвета тел задаются строками («#00FF80», «white», «orange»).

_color_cache = {}
_font_cache = {}


def to_rgb(color):
    """Строка цвета («#RRGGBB» или имя) → кортеж (r, g, b). """
    rgb = _color_cache.get(color)
    if rgb is None:
        rgb = tuple(pygame.Color(color))[:3]
        _color_cache[color] = rgb
    return rgb


def get_font(size=14, bold=False):
    
    key = (size, bold)
    font = _font_cache.get(key)
    if font is None:
        path = next((p for p in _FONT_CANDIDATES if os.path.exists(p)), None)
        font = pygame.font.Font(path, size)   # path=None → встроенный шрифт pygame
        font.set_bold(bold)
        _font_cache[key] = font
    return font


#  Легенда 

def draw_legend(surface, entries):
    
    font = get_font(13)
    x0, y0 = 12, 12
    for label, color, n_planets in entries:
        pygame.draw.circle(surface, to_rgb(color), (x0 + 5, y0 + 7), 5)
        text = font.render(f"{label}: {n_planets} планет", True, LEGEND_COLOR)
        surface.blit(text, (x0 + 16, y0))
        y0 += 20


if __name__ == "__main__":
    print("This module is not for direct call!")
