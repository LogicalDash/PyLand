import pyglet
import copy

class GameFrame:
    def __init__(graphics, state):
        self.graphics = graphics
        self.graphics.loadSprites()
        self.spriteInventory = graphics.getSpriteInventory()
        # A dictionary mapping strings of sprite names to images.
        self.spritesToDraw = []
        # spritesToDraw should be populated by tuples specifying the sprite's
        # image and where to draw it.  It should be removed from the list when
        # the entity it represents isn't on screen anymore--how to tell? I'll
        # have to remember the object represented too, and I'll put that as
        # the *first* item in the tuple, since that's where self goes in
        # function defs.
        self.state = state

    def putSpriteAt(self, spriteName, spriteX, spriteY):
        image = self.spriteInventory[spriteName]
        self.spritesToDraw.append((image, spriteX, spriteY))
    
    def draw(self):
        todraw = copy.deepcopy(self.spritesToDraw)
        spritesToDraw = []
        for triple in todraw:
            triple[0].blit(triple[1], triple[2])
