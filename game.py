import sys
import os
import pyglet
import windowframe
import gamestate
import gameframe
import graphics

class Game:
    levelfile = file(sys.argv[1], "r")
    version = 0
    def __init__(self):
        graphics.loadSprites()
        gamestate.init()
        gamestate.loadLevel(self.levelfile)
        gameframe.init()
        windowframe.init()

        pyglet.app.run()

Game()
