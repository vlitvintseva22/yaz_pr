# coding: utf-8
# license: GPLv3

"""
Модуль визуализации.

Все экранные координаты вычисляются здесь.
Физическая ось Y направлена вверх; на экране — вниз, поэтому
scale_y выполняет отражение: y_screen = -y_model + cy.
"""

window_width  = 1000
window_height = 800

_cx = window_width  // 2    # x-координата центра холста
_cy = window_height // 2    # y-координата центра холста


# ─── Преобразование координат ──────────────────────────────────────────

def scale_x(x):
    """Физическая x → экранная x."""
    return int(x) + _cx


def scale_y(y):
    """Физическая y → экранная y (ось Y направлена вверх)."""
    return -int(y) + _cy


# ─── Орбиты ────────────────────────────────────────────────────────────

def draw_all_orbits(space, stars):
    """
    Рисует окружности орбит для каждой звезды.
    Все орбиты имеют тег "orbit" — можно скрывать/показывать через toggle_orbits().
    """
    space.delete("orbit")
    for star in stars:
        cx = scale_x(star.x)
        cy = scale_y(star.y)
        for r in star.orbit_radii:
            space.create_oval(
                cx - r, cy - r, cx + r, cy + r,
                outline="#3a3a6a",
                width=1,
                dash=(3, 6),
                tags="orbit"
            )


def toggle_orbits(space, show: bool):
    """Переключает видимость орбит (теговое управление)."""
    state = "normal" if show else "hidden"
    space.itemconfigure("orbit", state=state)


# ─── Создание графических объектов ─────────────────────────────────────

def create_star_image(space, star):
    """Рисует звезду — яркий круг с оранжевой обводкой."""
    x, y, r = scale_x(star.x), scale_y(star.y), star.R
    star.image = space.create_oval(
        x - r, y - r, x + r, y + r,
        fill=star.color, outline="orange", width=2
    )


def create_star_label(space, star):
    """Подписывает звезду её именем над кружком."""
    x = scale_x(star.x)
    y = scale_y(star.y) - star.R - 10
    space.create_text(x, y, text=star.label, fill="white",
                      font=("Arial", 9, "bold"))


def create_planet_image(space, planet):
    """Рисует планету — закрашенный круг без обводки."""
    x, y, r = scale_x(planet.x), scale_y(planet.y), planet.R
    planet.image = space.create_oval(
        x - r, y - r, x + r, y + r,
        fill=planet.color, outline=""
    )


def create_satellite_image(space, sat):
    """Рисует спутник — маленький белый кружок."""
    x, y, r = scale_x(sat.x), scale_y(sat.y), sat.R
    sat.image = space.create_oval(
        x - r, y - r, x + r, y + r,
        fill=sat.color, outline=""
    )


# ─── Обновление позиций на экране ──────────────────────────────────────

def update_object_position(space, body):
    """Перемещает уже существующий овал на холсте к новым координатам тела."""
    x, y, r = scale_x(body.x), scale_y(body.y), body.R
    space.coords(body.image, x - r, y - r, x + r, y + r)


# ─── Легенда ───────────────────────────────────────────────────────────

def create_legend(space, star_configs):
    """
    Рисует в левом верхнем углу легенду:
    цветная точка + название звезды + количество планет.
    """
    x0, y0 = 12, 12
    for label, pcolor, n_pl in star_configs:
        space.create_oval(x0, y0, x0 + 10, y0 + 10,
                          fill=pcolor, outline="")
        space.create_text(x0 + 15, y0 + 5,
                          text=f"{label}: {n_pl} планет",
                          fill="#cccccc", anchor="w",
                          font=("Arial", 9))
        y0 += 18


if __name__ == "__main__":
    print("This module is not for direct call!")