import sys
import os
import pyglet
import window
import state
import frame
import graphics

class Game:
    levelfile = "level.txt"
    imagesfile = "images.conf"
    version = 0
    def __init__(self):
        if(len(sys.argv)>1):
            self.levelfile = sys.argv[1]
        self.state = state.GameState(self.levelfile)
        self.graphics = graphics.GameGraphics(self.imagesfile)
        self.frame = frame.GameFrame(self.graphics, self.state)
        self.win = window.GameWindow(self.frame)


Game()
