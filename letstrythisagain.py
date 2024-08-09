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
import webbrowser  # Import webbrowser module

# WebSocket Server Setup
connected = set()
data = Queue()
stop = Event()
b = False

all_data = []

def handler(websocket):
    connected.add(websocket)
    # Send init message
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
g = 9.81  # gravitational acceleration
m1 = 1.0  # mass of block 1
m2 = 1.0  # mass of block 2
initial_pos1 = (150, 340)  # initial position of block 1
initial_pos2 = (210, 340)  # initial position of block 2

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
dt = 0.1  # simulation timestep

# Input boxes
font = pygame.font.Font(None, 25)

class InputBox:
    def __init__(self, x, y, w, h, label='', default=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = str(default)  # Ensure default value is converted to string
        self.txt_surface = font.render(label + ' ' + self.text, True, self.color)
        self.active = False
        self.label = label

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = not self.active
                if self.active:
                    self.text = ''  # Clear text when activated
                self.color = self.color_active if self.active else self.color_inactive
                self.txt_surface = font.render(self.label + ' ' + str(self.text), True, self.color)
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                try:
                    self.text = float(self.text)  # Convert input text to float
                except ValueError:
                    pass  # Handle invalid input gracefully
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

# Function to update physics
def update_physics():
    global pos1, pos2, vel1, vel2, accel1, accel2, time_elapsed

    while True:
        # Calculate forces and accelerations
        accel1 = (m2 - m1) * g / (m1 + m2)
        accel2 = (m1 - m2) * g / (m1 + m2)
        
        vel1 += accel1 * dt
        vel2 += accel2 * dt

        # Check and correct for collision with bottom boundary
        if pos1[1] >= 550:
            pos1[1] = 550  # set block 1 at the bottom boundary
            vel1 = 0      # stop block
        elif pos2[1] >= 550:
            pos2[1] = 550  # set block 2 at the bottom boundary
            vel2 = 0      # stop block 2 on collision with bottom boundary
            pos1[1] = pos1[1]
            vel1 = 0
        else:
            pos1[1] += vel1 * dt
            pos2[1] += vel2 * dt

        # Store data for plotting
        time_data.append(time_elapsed)
        velocity_data1.append(vel1)
        velocity_data2.append(vel2)
        acceleration_data1.append(accel1)
        acceleration_data2.append(accel2)
        position_data1.append(pos1[1])
        position_data2.append(pos2[1])

        # Send data to WebSocket server
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

# Function to create the plot window for block 1
def create_plot_window1():
    root = tk.Tk()
    root.title("Blue block")

    fig, ax = plt.subplots(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    data_options = ["Time", "Velocity", "Position", "Acceleration"]

    x_var = tk.StringVar(value=data_options[0])
    y_var = tk.StringVar(value=data_options[1])

    def update_plot_wrapper1():
        x_label = x_var.get().lower()
        y_label = y_var.get().lower()
        x_data = time_data if x_label == "time" else eval(f"velocity_data1" if x_label == "velocity" else f"position_data1" if x_label == "position" else "acceleration_data1")
        y_data = time_data if y_label == "time" else eval(f"velocity_data1" if y_label == "velocity" else f"position_data1" if y_label == "position" else "acceleration_data1")
        ax.clear()
        ax.plot(x_data, y_data)
        ax.set_title(f"{y_var.get()} vs {x_var.get()}")
        ax.set_xlabel(x_var.get())
        ax.set_ylabel(y_var.get())
        ax.grid(True)
        canvas.draw()
        root.after(1000, update_plot_wrapper1)  # Update every 1 second to reduce lag

    tk.Label(root, text="X-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, x_var, *data_options).pack(side=tk.LEFT)

    tk.Label(root, text="Y-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, y_var, *data_options).pack(side=tk.LEFT)

    update_plot_wrapper1()
    root.mainloop()

# Function to create the plot window for block 2
def create_plot_window2():
    root = tk.Tk()
    root.title("Red block")

    fig, ax = plt.subplots(figsize=(8, 6))
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    data_options = ["Time", "Velocity", "Position", "Acceleration"]

    x_var = tk.StringVar(value=data_options[0])
    y_var = tk.StringVar(value=data_options[1])

    def update_plot_wrapper2():
        x_label = x_var.get().lower()
        y_label = y_var.get().lower()
        x_data = time_data if x_label == "time" else eval(f"velocity_data2" if x_label == "velocity" else f"position_data2" if x_label == "position" else "acceleration_data2")
        y_data = time_data if y_label == "time" else eval(f"velocity_data2" if y_label == "velocity" else f"position_data2" if y_label == "position" else "acceleration_data2")
        ax.clear()
        ax.plot(x_data, y_data)
        ax.set_title(f"{y_var.get()} vs {x_var.get()}")
        ax.set_xlabel(x_var.get())
        ax.set_ylabel(y_var.get())
        ax.grid(True)
        canvas.draw()
        root.after(1000, update_plot_wrapper2)  # Update every 1 second to reduce lag

    tk.Label(root, text="X-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, x_var, *data_options).pack(side=tk.LEFT)

    tk.Label(root, text="Y-Axis:").pack(side=tk.LEFT)
    tk.OptionMenu(root, y_var, *data_options).pack(side=tk.LEFT)

    update_plot_wrapper2()
    root.mainloop()

# Pygame main loop
threading.Thread(target=update_physics).start()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            stop.set()
            server.close()
        input_box_m1.handle_event(event)
        input_box_m2.handle_event(event)
        
        # Check for Desmos button click
        if event.type == pygame.MOUSEBUTTONDOWN:
            if desmos_button.collidepoint(event.pos):
                webbrowser.open('index.html')  # Open the Desmos graph in the default web browser

    screen.fill((255, 255, 255))

    pygame.draw.rect(screen, (0, 0, 255), (pos1[0] - w1//2, pos1[1] - l1//2, w1, l1))
    pygame.draw.rect(screen, (255, 0, 0), (pos2[0] - w2//2, pos2[1] - l2//2, w2, l2))

    pygame.draw.line(screen, (0, 0, 0), (180, 100), (180, 340), 5)
    pygame.draw.line(screen, (0, 0, 0), (180, 100), (400, 100), 5)
    pygame.draw.line(screen, (0, 0, 0), (400, 100), (400, 340), 5)

    input_box_m1.update()
    input_box_m2.update()

    input_box_m1.draw(screen)
    input_box_m2.draw(screen)

    plot_button1 = pygame.draw.rect(screen, (0, 255, 0), (600, 200, 140, 30))
    screen.blit(font.render('Blue Block Graph', True, (0, 0, 0)), (605, 205))

    plot_button2 = pygame.draw.rect(screen, (0, 255, 0), (600, 250, 140, 30))
    screen.blit(font.render('Red Block Graph', True, (0, 0, 0)), (605, 255))

    # Desmos button
    desmos_button = pygame.draw.rect(screen, (0, 255, 0), (600, 300, 140, 30))
    screen.blit(font.render('Open Desmos Graph', True, (0, 0, 0)), (605, 305))

    if event.type == pygame.MOUSEBUTTONDOWN:
        if plot_button1.collidepoint(event.pos):
            threading.Thread(target=create_plot_window1).start()
        elif plot_button2.collidepoint(event.pos):
            threading.Thread(target=create_plot_window2).start()

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
