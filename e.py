from threading import Thread, Event 
from queue import Queue, Empty 
import threading
import math 

connected = set()
data = Queue 
stop = Event()
y = 0
def quadratic(num):
    x = 0
    while x<num:
        y = x**2
        x+= 1
    return y
quadratic(5)