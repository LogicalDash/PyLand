import pyglet, math, threading
from widgets import *
from place import Place
from graphics import GameGraphics

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()

g = GameGraphics('images.conf')
