from threading import Thread, Event
from queue import Queue, Empty
from json import dumps
from websockets.sync.server import serve
import pygame
import threading
import time
import math
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import webbrowser

# WebSocket Server Setup
connected = set()
data = Queue()
stop = Event()
b = False

all_data = []

def handler(websocket):
    connected.add(websocket)
    init_message = {
        'type': 'init',
        'name': 'AtwoodMachine',
        'default_settings': {'xAxisValue': 'Time', 'yAxisValue': 'Pos'}
    }
    websocket.send(dumps(init_message))
    global b
    global all_data
    if b == True:
        for entry in all_data:
            update_message = {
                'type': 'update',
                'values': entry
            }
            websocket.send(dumps(update_message))
    else:
        b = True
        
    try:
        for msg in websocket:
            pass
    finally:
        connected.remove(websocket)

def start_server():
    server = serve(handler, '', 8032)
    Thread(target=server.serve_forever).start()
    return server

server = start_server()

def broadcaster():
    while not stop.is_set():
        for websocket in connected.copy():
            try:
                global all_data
                global b
                got = data.get_nowait()
                if b == True:
                    all_data.append(got)
                    update_message = {
                        'type': 'update',
                        'values': got
                    }
                    websocket.send(dumps(update_message))
                else:
                    b = True
            except Empty:
                pass
        time.sleep(.1)

Thread(target=broadcaster).start()

# Constants
g = 9.81
m1 = 1.0
m2 = 1.0
initial_pos1 = (150, 340)
initial_pos2 = (210, 340)

w1, l1 = 40, 40
w2, l2 = 40, 40

# Data lists for plotting
time_data = []
velocity_data1 = []
velocity_data2 = []
acceleration_data1 = []
acceleration_data2 = []
position_data1 = []
position_data2 = []

# Pygame initialization
pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

# Simulation variables
pos1 = list(initial_pos1)
pos2 = list(initial_pos2)
vel1 = 0.0
vel2 = 0.0
accel1 = 0.0
accel2 = 0.0
time_elapsed = 0.0
dt = 0.1

# Input boxes
font = pygame.font.Font(None, 25)

class InputBox:
    def __init__(self, x, y, w, h, label='', default=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = str(default)
        self.txt_surface = font.render(label + ' ' + self.text, True, self.color)
        self.active = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                if self.active:
                    self.text = ''
                self.color = self.color_active if self.active else self.color_inactive
                self.txt_surface = font.render(self.label + ' ' + str(self.text), True, self.color)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    self.text = float(self.text)
                except ValueError:
                    pass
                self.active = False
                self.color = self.color_inactive
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
            self.txt_surface = font.render(self.label + ' ' + str(self.text), True, self.color)

    def update(self):
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

input_box_m1 = InputBox(600, 50, 140, 30, 'Blue block:', str(m1))
input_box_m2 = InputBox(600, 100, 140, 30, 'Red block:', str(m2))

def update_physics():
    global pos1, pos2, vel1, vel2, accel1, accel2, time_elapsed

    while True:
        accel1 = (m2 - m1) * g / (m1 + m2)
        accel2 = (m1 - m2) * g / (m1 + m2)
        
        vel1 += accel1 * dt
        vel2 += accel2 * dt

        if pos1[1] >= 550:
            pos1[1] = 550
            vel1 = 0
        elif pos2[1] >= 550:
            pos2[1] = 550
            vel2 = 0
            pos1[1] = pos1[1]
            vel1 = 0
        else:
            pos1[1] += vel1 * dt
            pos2[1] += vel2 * dt

        time_data.append(time_elapsed)
        velocity_data1.append(vel1)
        velocity_data2.append(vel2)
        acceleration_data1.append(accel1)
        acceleration_data2.append(accel2)
        position_data1.append(pos1[1])
        position_data2.append(pos2[1])

        data.put_nowait([
            ['time', time_elapsed, 't'],
            ['pos1', pos1[1], 'y_{1}'],
            ['pos2', pos2[1], 'y_{2}'],
            ['vel1', vel1, 'v_{1}'],
            ['vel2', vel2, 'v_{2}'],
            ['accel1', accel1, 'a_{1}'],
            ['accel2', accel2, 'a_{2}']
        ])

        time_elapsed += dt
        time.sleep(dt)

def create_plot_window(title, data1, data2):
    root = tk.Tk()
    root.title(title)

    fig, ax = plt.subplots(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    data_options = ["Time", "Velocity", "Position", "Acceleration"]

    x_var = tk.StringVar(value=data_options[0])
    y_var = tk.StringVar(value=data_options[1])

    def update_plot_wrapper():
        x_label = x_var.get().lower()
        y_label = y_var.get().lower()
        x_data = time_data if x_label == "time" else eval(f"{data1}_data" if x_label == "velocity" else f"{data1}_data" if x_label == "position" else f"{data1}_data")
        y_data = time_data if y_label == "time" else eval(f"{data2}_data" if y_label == "velocity" else f"{data2}_data" if y_label == "position" else f"{data2}_data")
        ax.clear()
        ax.plot(x_data, y_data)
        ax.set_title(f"{y_var.get()} vs {x_var.get()}")
        ax.set_xlabel(x_var.get())
        ax.set_ylabel(y_var.get())
        ax.grid(True)
        canvas.draw()
        root.after(1000, update_plot_wrapper)

    tk.Label(root, text="X-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, x_var, *data_options).pack(side=tk.LEFT)

    tk.Label(root, text="Y-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, y_var, *data_options).pack(side=tk.LEFT)

    update_plot_wrapper()
    root.mainloop()

def reset_simulation():
    global pos1, pos2, vel1, vel2, accel1, accel2, time_elapsed
    pos1 = list(initial_pos1)
    pos2 = list(initial_pos2)
    vel1 = 0.0
    vel2 = 0.0
    accel1 = 0.0
    accel2 = 0.0
    time_elapsed = 0.0
    time_data.clear()
    velocity_data1.clear()
    velocity_data2.clear()
    acceleration_data1.clear()
    acceleration_data2.clear()
    position_data1.clear()
    position_data2.clear()
    all_data.clear()

reset_button = pygame.Rect(600, 150, 140, 30)
open_web_button = pygame.Rect(600, 200, 140, 30)
open_graph_button1 = pygame.Rect(600, 250, 140, 30)
open_graph_button2 = pygame.Rect(600, 300, 140, 30)

physics_thread = threading.Thread(target=update_physics)
physics_thread.daemon = True
physics_thread.start()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        input_box_m1.handle_event(event)
        input_box_m2.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if open_web_button.collidepoint(event.pos):
                webbrowser.open('https://localhost:8032')
            elif reset_button.collidepoint(event.pos):
                reset_simulation()
                b = False
            elif open_graph_button1.collidepoint(event.pos):
                Thread(target=create_plot_window, args=("Blue block", "velocity", "position")).start()
            elif open_graph_button2.collidepoint(event.pos):
                Thread(target=create_plot_window, args=("Red block", "velocity", "position")).start()

    input_box_m1.update()
    input_box_m2.update()

    screen.fill((255, 255, 255))

    try:
        m1 = float(input_box_m1.text)
    except ValueError:
        m1 = 1.0

    try:
        m2 = float(input_box_m2.text)
    except ValueError:
        m2 = 1.0

    input_box_m1.draw(screen)
    input_box_m2.draw(screen)

    pygame.draw.rect(screen, (0, 0, 255), reset_button)
    reset_text = font.render("Reset Simulation", True, (255, 255, 255))
    screen.blit(reset_text, (reset_button.x + 5, reset_button.y + 5))

    pygame.draw.rect(screen, (0, 255, 0), open_web_button)
    open_web_text = font.render("Open Web Page", True, (255, 255, 255))
    screen.blit(open_web_text, (open_web_button.x + 5, open_web_button.y + 5))

    pygame.draw.rect(screen, (0, 255, 255), open_graph_button1)
    open_graph_text1 = font.render("Open Blue Graph", True, (255, 255, 255))
    screen.blit(open_graph_text1, (open_graph_button1.x + 5, open_graph_button1.y + 5))

    pygame.draw.rect(screen, (255, 0, 255), open_graph_button2)
    open_graph_text2 = font.render("Open Red Graph", True, (255, 255, 255))
    screen.blit(open_graph_text2, (open_graph_button2.x + 5, open_graph_button2.y + 5))

    pygame.draw.rect(screen, (0, 0, 255), (*pos1, w1, l1))
    pygame.draw.rect(screen, (255, 0, 0), (*pos2, w2, l2))
    pygame.draw.line(screen, (0, 0, 0), (200, 0), (200, 75))
    pygame.draw.circle(screen, (200, 0, 0), (200, 75), 30)
    pygame.draw.line(screen, (0, 0, 0), (170, pos1[1] + 40), (170, 75))
    pygame.draw.line(screen, (0, 0, 0), (230, pos2[1] + 40), (230, 75))
    pygame.draw.rect(screen, (200, 0, 0), (pos1[0], pos1[1], w2, w2))
    pygame.draw.rect(screen, (0, 0, 200), (pos2[0], pos2[1], w1, w1))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
stop.set()
server.shutdown()
