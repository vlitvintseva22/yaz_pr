# coding: utf-8
# license: GPLv3

"""
Вспомогательные функции экрана.

Здесь живёт ТОЛЬКО то, что относится к холсту:
  • размеры окна,
  • преобразование физических координат в экранные,
  • рисование легенды.

Сами тела (звёзды/планеты/спутники) рисуют себя сами — см. их методы
draw()/redraw() в solar_objects. Поэтому этот модуль ничего не знает
о классах тел (нет обратной зависимости — импорт не зацикливается).
"""

# Размеры холста по умолчанию (используются, если экран не запрошен).
# Реальные значения подставляются под размер экрана через set_window_size().
window_width = 1000
window_height = 800

_cx = window_width // 2     # центр холста по X
_cy = window_height // 2    # центр холста по Y

TRAIL_MAX = 140             # макс. число сегментов следа на одну планету


def set_window_size(width, height):
    """
    Задаёт размер холста и пересчитывает его центр.
    Центр холста соответствует точке (0, 0) физических координат, поэтому
    при любом размере экрана система остаётся отцентрованной.
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


# ─── Орбиты ────────────────────────────────────────────────────────

def draw_orbits(canvas, stars):
    """
    Рисует пунктирные окружности орбит для каждой звезды.
    Все орбиты получают тег "orbit" — их можно скрыть/показать через
    canvas.itemconfigure("orbit", state=...).
    """
    for star in stars:
        cx, cy = scale_x(star.x), scale_y(star.y)
        for r in star.orbit_radii:
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                               outline="#3a3a6a", dash=(3, 6), tags="orbit")


# ─── Легенда ───────────────────────────────────────────────────────

def create_legend(canvas, entries):
    """
    Рисует легенду в левом верхнем углу.
    entries — список (подпись, цвет, число_планет).
    """
    x0, y0 = 12, 12
    for label, color, n_planets in entries:
        canvas.create_oval(x0, y0, x0 + 10, y0 + 10, fill=color, outline="")
        canvas.create_text(x0 + 15, y0 + 5,
                           text=f"{label}: {n_planets} планет",
                           fill="#cccccc", anchor="w", font=("Arial", 9))
        y0 += 18


if __name__ == "__main__":
    print("This module is not for direct call!")
