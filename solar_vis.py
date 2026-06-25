# coding: utf-8
# license: GPLv3

"""
Вспомогательные функции экрана (pygame).

Здесь живёт ТОЛЬКО то, что относится к поверхности рисования:
  • размеры окна,
  • преобразование физических координат в экранные,
  • разбор цветов (строка «#RRGGBB»/имя → RGB) и кэш шрифтов,
  • рисование орбит и легенды.

Сами тела (звёзды/планеты/спутники) рисуют себя сами — см. их методы
render()/render_trail() в solar_objects. Поэтому этот модуль ничего не
знает о классах тел (нет обратной зависимости — импорт не зацикливается).
"""

import pygame

# Размеры поверхности по умолчанию (используются, если экран не запрошен).
# Реальные значения подставляются под размер экрана через set_window_size().
window_width = 1000
window_height = 800

_cx = window_width // 2     # центр поверхности по X
_cy = window_height // 2    # центр поверхности по Y

TRAIL_MAX = 140             # макс. число точек следа на одну планету

ORBIT_COLOR = (58, 58, 106)     # #3a3a6a — цвет окружностей орбит
LEGEND_COLOR = (204, 204, 204)


def set_window_size(width, height):
    """
    Задаёт размер области рисования и пересчитывает её центр.
    Центр соответствует точке (0, 0) физических координат, поэтому при
    любом размере экрана система остаётся отцентрованной.
    """
    global window_width, window_height, _cx, _cy
    window_width = width
    window_height = height
    _cx = width // 2
    _cy = height // 2


# ─── Преобразование координат ──────────────────────────────────────
# Физическая ось Y направлена ВВЕРХ, экранная — ВНИЗ, поэтому scale_y
# отражает координату: y_экр = -y + центр.

def scale_x(x):
    """Физическая x → экранная x."""
    return int(x) + _cx


def scale_y(y):
    """Физическая y → экранная y (с отражением оси)."""
    return -int(y) + _cy


# ─── Цвета и шрифты ────────────────────────────────────────────────
# Цвета тел задаются строками («#00FF80», «white», «orange»). pygame
# рисует кортежами RGB, поэтому разбираем строку один раз и кэшируем.

_color_cache = {}
_font_cache = {}


def to_rgb(color):
    """Строка цвета («#RRGGBB» или имя) → кортеж (r, g, b). С кэшем."""
    rgb = _color_cache.get(color)
    if rgb is None:
        rgb = tuple(pygame.Color(color))[:3]
        _color_cache[color] = rgb
    return rgb


def get_font(size=14, bold=False):
    """Возвращает кэшированный системный шрифт Arial нужного размера."""
    key = (size, bold)
    font = _font_cache.get(key)
    if font is None:
        font = pygame.font.SysFont("Arial", size, bold=bold)
        _font_cache[key] = font
    return font


# ─── Орбиты ────────────────────────────────────────────────────────

def draw_orbits(surface, stars):
    """Рисует тонкие окружности орбит для каждой звезды."""
    for star in stars:
        cx, cy = scale_x(star.x), scale_y(star.y)
        for r in star.orbit_radii:
            if r >= 1:
                pygame.draw.circle(surface, ORBIT_COLOR, (cx, cy), int(r), 1)


# ─── Легенда ───────────────────────────────────────────────────────

def draw_legend(surface, entries):
    """
    Рисует легенду в левом верхнем углу.
    entries — список (подпись, цвет, число_планет).
    """
    font = get_font(13)
    x0, y0 = 12, 12
    for label, color, n_planets in entries:
        pygame.draw.circle(surface, to_rgb(color), (x0 + 5, y0 + 7), 5)
        text = font.render(f"{label}: {n_planets} планет", True, LEGEND_COLOR)
        surface.blit(text, (x0 + 16, y0))
        y0 += 20


if __name__ == "__main__":
    print("This module is not for direct call!")
