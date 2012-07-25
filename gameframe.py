import pyglet
import graphics
import gamestate
from copy import copy

graphics.loadAll()
spriteInventory = graphics.getSpriteInventory()
# A dictionary mapping strings of sprite names to images.
spritesToDraw = []
# spritesToDraw should be populated by tuples specifying the sprite's
# image and where to draw it.  It should be removed from the list when
# the entity it represents isn't on screen anymore--how to tell? I'll
# have to remember the object represented too, and I'll put that as
# the *first* item in the tuple, since that's where self goes in
# function defs.


def drawThis(self, spriteName, spriteX, spriteY):
    image = spriteInventory[spriteName]
    spritesToDraw.append(self, image, spriteX, spriteY)

def getSpritesToDraw(self):
    drawThese = copy(spritesToDraw)
    spritesToDraw = []
    return drawThese

def draw(self):
    
