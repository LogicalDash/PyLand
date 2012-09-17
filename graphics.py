import pyglet
import unittest


class GameGraphics:
    def __init__(self, imgfile):
        self.spriteInventory = {}
        self.imgfile = imgfile

    def getSprite(spriten):
        return spriteInventory[spriten]

    def loadSprites():
        imgconf = open(self.imgfile, 'r')
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
