# coding: utf-8
# license: GPLv3

"""
Симуляция «Солнечной системы» — точка входа (pygame).

Состав системы по умолчанию (build_default_system в solar_model):
  Звезда 1: 10 планет        Звезда 2: 15 планет (+спутники)
  Звезда 3: 20 планет        Звезда 4: 25 планет (+спутники)

Управление:
  • кнопки внизу (мышью) и горячие клавиши:
  • SPACE — старт/пауза   O — орбиты   T — след   I — взаимодействие
  • ←/→ — скорость        ↑/↓ — шаг dt   ESC — выход
"""

import os
import sys

import pygame

from solar_vis import Viewport, draw_legend, get_font
from solar_model import build_default_system
from solar_input import load_system, save_system

SOLAR_FILE = "solar_system.txt"


def resource_path(name):
    
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)

# Поля от размеров экрана (на рамку окна, заголовок, панель задач).
SCREEN_MARGIN_X = 40
SCREEN_MARGIN_Y = 140

BAR_H = 56                      # высота нижней панели управления
BG_COLOR = (5, 5, 15)          # фон космоса (#05050f)
PANEL_COLOR = (13, 13, 31)     # фон панели (#0d0d1f)
BTN_COLOR = (30, 58, 95)       # кнопка (#1e3a5f)
BTN_HOVER = (45, 82, 132)      # кнопка под курсором
INFO_COLOR = (136, 170, 204)   # текст счётчиков
HINT_COLOR = (90, 100, 130)    # подсказка по клавишам
TRACK_COLOR = (60, 70, 100)    # дорожка ползунка
HANDLE_COLOR = (140, 180, 230) # бегунок ползунка
LABEL_COLOR = (170, 170, 170)  # подписи на панели


class Button:

    def __init__(self, rect, label_fn, action):
        self.rect = pygame.Rect(rect)
        self.label_fn = label_fn      
        self.action = action          

    def draw(self, surface, font, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, BTN_HOVER if hovered else BTN_COLOR,
                         self.rect, border_radius=4)
        text = font.render(self.label_fn(), True, (255, 255, 255))
        surface.blit(text, (self.rect.centerx - text.get_width() // 2,
                            self.rect.centery - text.get_height() // 2))


class Slider:

    def __init__(self, rect, vmin, vmax, get_value, set_value):
        self.rect = pygame.Rect(rect)
        self.vmin = vmin
        self.vmax = vmax
        self.get_value = get_value      
        self.set_value = set_value      
        self.dragging = False

    def _value_to_x(self, value):
        frac = (value - self.vmin) / (self.vmax - self.vmin)
        return self.rect.x + int(frac * self.rect.w)

    def _x_to_value(self, x):
        frac = (x - self.rect.x) / self.rect.w
        frac = max(0.0, min(1.0, frac))
        return round(self.vmin + frac * (self.vmax - self.vmin))

    def handle_event(self, event):
        
        grab = self.rect.inflate(16, 18)        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if grab.collidepoint(event.pos):
                self.dragging = True
                self.set_value(self._x_to_value(event.pos[0]))
                return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value(self._x_to_value(event.pos[0]))
            return True
        return False

    def draw(self, surface):
        cy = self.rect.centery
        pygame.draw.line(surface, TRACK_COLOR,
                         (self.rect.x, cy), (self.rect.right, cy), 3)
        hx = self._value_to_x(self.get_value())
        pygame.draw.circle(surface, HANDLE_COLOR, (hx, cy), 7)


class SolarApp:
    

    def __init__(self, sim):
        self.sim = sim
        self.running_sim = False       
        self.show_trails = True
        self.show_orbits = True
        self.dt = 1.0                  
        self.speed = 50                

        pygame.init()
        info = pygame.display.Info()
        self.canvas_w = max(640, min(1500, info.current_w - SCREEN_MARGIN_X))
        self.canvas_h = max(480, min(950, info.current_h - SCREEN_MARGIN_Y))
        self.view = Viewport(self.canvas_w, self.canvas_h)   

        self.screen = pygame.display.set_mode((self.canvas_w, self.canvas_h + BAR_H))
        pygame.display.set_caption("Солнечная система — 4 звезды (pygame)")
        self.clock = pygame.time.Clock()
        self.font = get_font(14)
        self.small = get_font(12)

        self.sim.fit_to_screen(self.canvas_w // 2, self.canvas_h // 2)

        self._build_controls()
        self._legend = self._legend_entries()

    def _legend_entries(self):
        """Для каждой звезды — подпись, цвет её планет, число планет."""
        entries = []
        for star in self.sim.stars:
            own = [p for p in self.sim.planets if p.star is star]
            color = own[0].color if own else star.color
            entries.append((star.label, color, len(own)))
        return entries

    def _build_controls(self):
        y = self.canvas_h + (BAR_H - 32) // 2
        h = 32
        self.buttons = [
            Button((10, y, 110, h),
                   lambda: "Пауза" if self.running_sim else "Старт",
                   self.toggle_run),
            Button((128, y, 140, h),
                   lambda: "Скрыть орбиты" if self.show_orbits else "Орбиты",
                   self.toggle_orbits),
            Button((276, y, 130, h),
                   lambda: "Скрыть след" if self.show_trails else "След",
                   self.toggle_trails),
            Button((414, y, 210, h),
                   lambda: f"Взаимодействие: {'вкл' if self.sim.interactions else 'выкл'}",
                   self.toggle_interactions),
        ]

      
        self._speed_label_x = 644
        self._speed_value_x = 644 + 70 + 180 + 10
        slider_rect = (644 + 70, self.canvas_h + BAR_H // 2 - 3, 180, 6)
        self.slider = Slider(
            slider_rect, 0, 100,
            get_value=lambda: self.speed,
            set_value=lambda v: setattr(self, "speed", v),
        )

    #  Действия кнопок/клавиш
    def toggle_run(self):
        self.running_sim = not self.running_sim

    def toggle_orbits(self):
        self.show_orbits = not self.show_orbits

    def toggle_trails(self):
        self.show_trails = not self.show_trails

    def toggle_interactions(self):
        self.sim.interactions = not self.sim.interactions

    def _steps_this_frame(self):
        
        return max(1, round(self.speed / 8))     

    def _advance(self):
        for _ in range(self._steps_this_frame()):
            self.sim.step(self.dt)                 
            for planet in self.sim.planets:        
                planet.record_trail(self.view)     

    def _render(self):
        s = self.screen
        s.fill(BG_COLOR)

        if self.show_orbits:
            for star in self.sim.stars:
                star.render_orbits(s, self.view)
        if self.show_trails:
            for planet in self.sim.planets:
                planet.render_trail(s)
        for star in self.sim.stars:
            star.render(s, self.view)
        for planet in self.sim.planets:
            planet.render(s, self.view)
        for sat in self.sim.satellites:
            sat.render(s, self.view)

        draw_legend(s, self._legend)
        self._render_hint()
        self._render_bar()
        pygame.display.flip()

    def _render_hint(self):
        hint = ("SPACE пуск/пауза   O орбиты   T след   I взаимод.   "
                "←/→ скорость   ↑/↓ dt   ESC выход")
        text = self.small.render(hint, True, HINT_COLOR)
        self.screen.blit(text, (self.canvas_w // 2 - text.get_width() // 2,
                                self.canvas_h - 20))

    def _render_bar(self):
        s = self.screen
        pygame.draw.rect(s, PANEL_COLOR, (0, self.canvas_h, self.canvas_w, BAR_H))
        mouse = pygame.mouse.get_pos()
        for btn in self.buttons:
            btn.draw(s, self.small, mouse)

        # Ползунок скорости + подписи.
        cy = self.canvas_h + BAR_H // 2
        label = self.small.render("Скорость", True, LABEL_COLOR)
        s.blit(label, (self._speed_label_x, cy - label.get_height() // 2))
        self.slider.draw(s)
        value = self.small.render(str(self.speed), True, LABEL_COLOR)
        s.blit(value, (self._speed_value_x, cy - value.get_height() // 2))

        info = (f"dt={self.dt:.1f}   время={self.sim.time:.1f}   "
                f"планет={len(self.sim.planets)}   "
                f"спутников={len(self.sim.satellites)}")
        text = self.font.render(info, True, INFO_COLOR)
        s.blit(text, (self.canvas_w - text.get_width() - 12,
                      self.canvas_h + (BAR_H - text.get_height()) // 2))

    #  Главный цикл 
    def _handle_event(self, event):
        """Возвращает False, если пора выходить."""
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            elif event.key == pygame.K_SPACE:
                self.toggle_run()
            elif event.key == pygame.K_o:
                self.toggle_orbits()
            elif event.key == pygame.K_t:
                self.toggle_trails()
            elif event.key == pygame.K_i:
                self.toggle_interactions()
            elif event.key == pygame.K_RIGHT:
                self.speed = min(100, self.speed + 5)
            elif event.key == pygame.K_LEFT:
                self.speed = max(0, self.speed - 5)
            elif event.key == pygame.K_UP:
                self.dt = round(min(10.0, self.dt + 0.1), 1)
            elif event.key == pygame.K_DOWN:
                self.dt = round(max(0.1, self.dt - 0.1), 1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.slider.handle_event(event):     # сначала ползунок
                for btn in self.buttons:
                    if btn.rect.collidepoint(event.pos):
                        btn.action()
                        break
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            self.slider.handle_event(event)             
        return True

    def run(self):
        alive = True
        while alive:
            for event in pygame.event.get():
                if not self._handle_event(event):
                    alive = False
                    break
            if alive and self.running_sim:
                self._advance()
            self._render()
            self.clock.tick(60)
        pygame.quit()


def main():
    if os.path.exists(SOLAR_FILE):
        
        print(f"[main] Загружаю конфигурацию из '{SOLAR_FILE}'")
        sim = load_system(SOLAR_FILE)
    else:
        seed = resource_path(SOLAR_FILE)
        if os.path.exists(seed):
            
            print(f"[main] Беру встроенную конфигурацию '{seed}'")
            sim = load_system(seed)
        else:
            
            print("[main] Конфигурация не найдена — генерирую систему по умолчанию")
            sim = build_default_system()
      
        save_system(SOLAR_FILE, sim)
        print(f"[main] Рабочая копия сохранена в '{SOLAR_FILE}'")

    SolarApp(sim).run()


if __name__ == "__main__":
    main()
