import pyglet
import unittest

spriteInventory = {}

def init():
    loadSprites()

def getSprite(spriten):
    return spriteInventory[spriten]

def loadSprites():
    imgconf = file("images.conf",'r')
    line = imgconf.readline()
    tokens = []

    while(line != ""):
        tokens = line.split(" ")
        if(len(tokens) != 2):
            print "Wrong number of tokens: " + line
            break
        try:
            image = pyglet.resource.image(tokens[1])
        except:
            print "Not an image: " + tokens[1]
            break
        spriteInventory[tokens[0]] = image
        line = imgconf.readline()

        imgconf.close()

class GraphicTestCase(unittest.TestCase):
    def testImageClass(self):
        for img in spriteInventory.values():
            self.assertIsInstance(img, pyglet.image.TextureRegion)


class sprite:
    x = 0
    y = 0

    def __init__(self, name):
        self.image = getSprite(name)

    def __init__(self, name, x, y):
        self.image = getSprite(name)
        self.x = x
        self.y = y

    def blit(self):
        self.image.blit(x, y)
