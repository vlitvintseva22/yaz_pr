# coding: utf-8
# license: GPLv3

"""
Средства экрана (pygame).

  • Viewport — объект-«камера»: переводит физические координаты в экранные.
    Раньше это были ГЛОБАЛЬНЫЕ переменные модуля (_cx, _cy) и функции
    scale_x/scale_y, читавшие эти глобалы. Глобальное изменяемое состояние —
    это не ООП; теперь преобразование инкапсулировано в объекте Viewport,
    который передаётся телам в их методы render().
  • to_rgb / get_font — утилиты-мемоизации (без состояния приложения, просто
    кэш разобранных цветов и шрифтов).
  • draw_legend — рисование легенды (HUD-элемент поверх сцены).

Сами тела (звёзды/планеты/спутники) рисуют себя сами — см. их методы
render()/render_orbits()/render_trail() в solar_objects. Поэтому этот модуль
ничего не знает о классах тел (нет обратной зависимости — импорт не зацикливается).
"""

import pygame

TRAIL_MAX = 140                 # макс. число точек следа на одну планету

ORBIT_COLOR = (58, 58, 106)     # #3a3a6a — цвет окружностей орбит
LEGEND_COLOR = (204, 204, 204)


class Viewport:
    """
    «Камера»: преобразует физические координаты в экранные.

    Центр области рисования соответствует точке (0, 0) физических координат,
    поэтому при любом размере окна система остаётся отцентрованной. Физическая
    ось Y направлена ВВЕРХ, экранная — ВНИЗ, поэтому sy() отражает координату.
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.cx = width // 2
        self.cy = height // 2

    def sx(self, x):
        """Физическая x → экранная x."""
        return int(x) + self.cx

    def sy(self, y):
        """Физическая y → экранная y (с отражением оси)."""
        return -int(y) + self.cy


# ─── Цвета и шрифты (утилиты с кэшем) ──────────────────────────────
# Цвета тел задаются строками («#00FF80», «white», «orange»). pygame рисует
# кортежами RGB, поэтому разбираем строку один раз и запоминаем (мемоизация).

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
