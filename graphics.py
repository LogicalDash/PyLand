import pyglet
import unittest

def load_rltile(path):
    badimg = pyglet.resource.image(path)
    badimgd = badimg.get_image_data()
    bad_rgba = badimgd.get_data('RGBA', badimgd.pitch)
    badimgd.set_data('RGBA', badimgd.pitch, bad_rgba.replace('\xffGll','\x00Gll').replace('\xff.', '\x00.'))
    return badimgd.get_texture()

class GameGraphics:
    def __init__(self, imgfile):
        self.sprite_inventory = {}
        self.imgfile = imgfile

    def get_sprite(self, spriten):
        if self.sprite_inventory.has_key(spriten):
            return self.sprite_inventory[spriten]
        else:
            self.sprite_inventory[spriten] = pyglet.resource.image(spriten)

    def load_sprites(self):
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
            sprite_inventory[tokens[0]] = image
            line = imgconf.readline()

            imgconf.close()

def image(imgn):
    return g.getSprite(imgn)

class GraphicTestCase(unittest.TestCase):
    def testImageClass(self):
        for img in sprite_inventory.values():
            self.assertIsInstance(img, pyglet.image.TextureRegion)
