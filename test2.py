from threading import Thread, Event
from queue import Queue, Empty
from json import dumps
from websockets.sync.server import serve
import pygame
import math
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

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
dt = 0.01  # simulation timestep
font = pygame.font.Font(None,25)
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
            vel1 = 0      # stop block 1 on collision with bottom boundary
            pos2[1] = pos2[1]
            vel2 = 0
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

        time_elapsed += dt
        time.sleep(dt)


## server stuff
connected=set()
def handler(websocket):
    connected.add(websocket)
    # send manifest here
    try:
        for msg in websocket:
            # you'll accept messages indicating user input changes here
            pass
    finally:
        connected.remove(websocket)

server=serve(handler,'',8032)
Thread(target=server.serve_forever).start()

data=Queue()
stop=Event()

def broadcaster():
    while not stop.is_set():
        for websocket in connected.copy():
            try:
                got=data.get_nowait()
                websocket.send(dumps(got))
            except Empty:
                pass

Thread(target=broadcaster).start()

# pygame loop here
# to send data, use data.put_nowait([[name,value,mathName],...])

#implementing stuff from sim


running = True
try:
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            input_box_m1.handle_event(event)
            input_box_m2.handle_event(event)

        screen.fill((255, 255, 255))  # clear screen

        # Draw input boxes
        input_box_m1.draw(screen)
        input_box_m2.draw(screen)

        # Adjust block sizes
        if m1 > m2:
            w1 = 45
            w2 = 40
        elif m2 > m1:
            w2 = 45
            w1 = 40
        else:
            w1 = 40
            w2 = 40
        # Update physics with user input values
        m1 = input_box_m1.text if isinstance(input_box_m1.text, float) else m1
        m2 = input_box_m2.text if isinstance(input_box_m2.text, float) else m2

        # Draw blocks and connecting lines
        pygame.draw.line(screen, (0, 0, 0), (200, 0), (200, 75))
        pygame.draw.circle(screen, (200, 0, 0), (200, 75), 30)
        pygame.draw.line(screen, (0, 0, 0), (170, pos1[1] + 40), (170, 75))
        pygame.draw.line(screen, (0, 0, 0), (230, pos2[1] + 40), (230, 75))
        pygame.draw.rect(screen, (200, 0, 0), (pos1[0], pos1[1], w2, w2))
        pygame.draw.rect(screen, (0, 0, 200), (pos2[0], pos2[1], w1, w1))

        # Display information
        info_font = pygame.font.Font(None, 36)
        instruction_text = info_font.render("Enter masses", True, (0, 0, 255))

        screen.blit(instruction_text, (590, 15))

        pygame.display.flip()
        clock.tick(60)  # limit to 60 fps

        time.sleep(1)
        
        
        data.put_nowait([["pos",time_elapsed,"x_{1}"],
                         ["other", acceleration_data1, "y_{1}"]])
except KeyboardInterrupt:
    for websocket in connected.copy():
        websocket.close()
    server.shutdown()
    stop.set()


   
