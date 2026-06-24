# coding: utf-8
# license: GPLv3

"""
Симуляция «Солнечной системы» — точка входа.

Состав системы по умолчанию (build_default_system в solar_model):
  Звезда 1: 10 планет        Звезда 2: 15 планет (+спутники)
  Звезда 3: 20 планет        Звезда 4: 25 планет (+спутники)

Орбиты разных звёзд пересекаются → планеты сталкиваются и сливаются,
могут падать на звёзды (звезда при этом растёт). Всё это — честная
физика в solar_model / solar_objects.

Всё состояние приложения (тела, кнопки, флаги) живёт в классе SolarApp —
никаких глобальных переменных.
"""

import os
import tkinter

from solar_vis import set_window_size, create_legend, draw_orbits

# Поля, оставляемые от размеров экрана: по бокам — на рамку окна,
# снизу — на заголовок, панель задач и панель управления.
SCREEN_MARGIN_X = 20
SCREEN_MARGIN_Y = 120
from solar_model import build_default_system
from solar_input import load_system, save_system

SOLAR_FILE = "solar_system.txt"


class SolarApp:
    """GUI-приложение: окно, кнопки и цикл анимации над одной Simulation."""

    def __init__(self, sim):
        self.sim = sim
        self.running = False
        self.show_trails = True
        self.show_orbits = True

        self._build_window()
        self.sim.fit_to_screen(self._half_w, self._half_h)
        self._draw_all_bodies()

    # ── Создание окна и панели управления ──────────────────────────
    def _build_window(self):
        self.root = tkinter.Tk()
        self.root.title("Солнечная система — 4 звезды")
        self.root.resizable(False, False)

        # Подстраиваем холст под размер экрана (с полями под рамку и панели).
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        canvas_w = max(400, screen_w - SCREEN_MARGIN_X)
        canvas_h = max(300, screen_h - SCREEN_MARGIN_Y)
        set_window_size(canvas_w, canvas_h)
        self._half_w = canvas_w // 2     # для масштабирования системы под холст
        self._half_h = canvas_h // 2

        self.canvas = tkinter.Canvas(self.root, width=canvas_w,
                                     height=canvas_h, bg="#05050f")
        self.canvas.pack(side=tkinter.TOP)

        ctrl = tkinter.Frame(self.root, bg="#0d0d1f", pady=5)
        ctrl.pack(side=tkinter.BOTTOM, fill=tkinter.X)

        self.start_button = tkinter.Button(
            ctrl, text="Старт", command=self.toggle_run,
            width=8, bg="#1e3a5f", fg="white", relief=tkinter.FLAT)
        self.start_button.pack(side=tkinter.LEFT, padx=8)

        tkinter.Label(ctrl, text="dt:", bg="#0d0d1f", fg="#aaaaaa").pack(side=tkinter.LEFT)
        self.time_step = tkinter.DoubleVar(value=1.0)
        tkinter.Entry(ctrl, textvariable=self.time_step, width=5, bg="#1a1a2e",
                      fg="white", insertbackground="white").pack(side=tkinter.LEFT, padx=4)

        tkinter.Label(ctrl, text="  Скорость:", bg="#0d0d1f",
                      fg="#aaaaaa").pack(side=tkinter.LEFT)
        self.time_speed = tkinter.DoubleVar(value=50)
        tkinter.Scale(ctrl, variable=self.time_speed, from_=0, to=100,
                      orient=tkinter.HORIZONTAL, length=130, showvalue=False,
                      bg="#0d0d1f", fg="white", troughcolor="#1e3a5f",
                      highlightthickness=0).pack(side=tkinter.LEFT)

        self.orbit_button = tkinter.Button(
            ctrl, text="Скрыть орбиты", command=self.toggle_orbits,
            width=15, bg="#1e3a5f", fg="white", relief=tkinter.FLAT)
        self.orbit_button.pack(side=tkinter.LEFT, padx=10)

        self.trail_button = tkinter.Button(
            ctrl, text="Скрыть след", command=self.toggle_trails,
            width=15, bg="#1e3a5f", fg="white", relief=tkinter.FLAT)
        self.trail_button.pack(side=tkinter.LEFT, padx=10)

        self.interaction_button = tkinter.Button(
            ctrl, text=self._interaction_text(), command=self.toggle_interactions,
            width=22, bg="#1e3a5f", fg="white", relief=tkinter.FLAT)
        self.interaction_button.pack(side=tkinter.LEFT, padx=10)

        self.displayed_time = tkinter.StringVar(value="0.0 сек.")
        tkinter.Label(ctrl, textvariable=self.displayed_time, width=16,
                      bg="#0d0d1f", fg="#88aacc").pack(side=tkinter.RIGHT, padx=8)

    # ── Первичная отрисовка ────────────────────────────────────────
    def _draw_all_bodies(self):
        # Орбиты рисуем первыми, чтобы они были под телами.
        draw_orbits(self.canvas, self.sim.stars)
        for star in self.sim.stars:
            star.draw(self.canvas)
        for planet in self.sim.planets:
            planet.draw(self.canvas)
        for sat in self.sim.satellites:
            sat.draw(self.canvas)

        # Легенда: для каждой звезды берём цвет и число её планет.
        entries = []
        for star in self.sim.stars:
            own = [p for p in self.sim.planets if p.star is star]
            color = own[0].color if own else star.color
            entries.append((star.label, color, len(own)))
        create_legend(self.canvas, entries)

    # ── Кнопки ──────────────────────────────────────────────────────
    def toggle_run(self):
        """Старт / Пауза."""
        self.running = not self.running
        if self.running:
            self.start_button.config(text="Пауза")
            self.animate()
        else:
            self.start_button.config(text="Старт")

    def toggle_orbits(self):
        """Показать / скрыть окружности орбит."""
        self.show_orbits = not self.show_orbits
        self.canvas.itemconfigure("orbit", state="normal" if self.show_orbits else "hidden")
        self.orbit_button.config(text="Скрыть орбиты" if self.show_orbits else "Показать орбиты")

    def toggle_trails(self):
        """Показать / скрыть следы планет."""
        self.show_trails = not self.show_trails
        self.canvas.itemconfigure("trail", state="normal" if self.show_trails else "hidden")
        self.trail_button.config(text="Скрыть след" if self.show_trails else "Показать след")

    def _interaction_text(self):
        state = "вкл" if self.sim.interactions else "выкл"
        return f"Взаимодействие: {state}"

    def toggle_interactions(self):
        """Включает / выключает гравитационное взаимодействие планет между собой."""
        self.sim.interactions = not self.sim.interactions
        self.interaction_button.config(text=self._interaction_text())

    # ── Один кадр анимации ─────────────────────────────────────────
    def animate(self):
        dt = self.time_step.get()
        removed_planets, removed_sats = self.sim.step(dt)

        # Стираем исчезнувшие тела (слияние планет + падение на звёзды).
        for victim in removed_planets:
            if victim.image is not None:
                self.canvas.delete(victim.image)
            victim.clear_trail(self.canvas)
        for sat in removed_sats:
            if sat.image is not None:
                self.canvas.delete(sat.image)

        # Двигаем тела к новым позициям.
        for star in self.sim.stars:        # звезда могла подрасти, поглотив планету
            star.redraw(self.canvas)
        for planet in self.sim.planets:
            planet.extend_trail(self.canvas)
            planet.redraw(self.canvas)
        for sat in self.sim.satellites:
            sat.redraw(self.canvas)

        self.displayed_time.set("%.1f сек." % self.sim.time)

        if self.running:
            delay = 101 - int(self.time_speed.get())   # 1 мс (быстро) … 101 мс (медленно)
            self.canvas.after(delay, self.animate)

    def run(self):
        self.root.mainloop()


def main():
    if os.path.exists(SOLAR_FILE):
        print(f"[main] Загружаю конфигурацию из '{SOLAR_FILE}'")
        sim = load_system(SOLAR_FILE)
    else:
        print(f"[main] Файл '{SOLAR_FILE}' не найден — генерирую систему по умолчанию")
        sim = build_default_system()
        save_system(SOLAR_FILE, sim)
        print(f"[main] Конфигурация сохранена в '{SOLAR_FILE}'")

    SolarApp(sim).run()


if __name__ == "__main__":
    main()
