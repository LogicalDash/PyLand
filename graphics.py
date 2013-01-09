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
        self.spriteInventory = {}
        self.imgfile = imgfile

<<<<<<< HEAD
    def getSprite(spriten):
        return spriteInventory[spriten]

    def loadSprites():
=======
    def get_sprite(self, spriten):
        if self.sprite_inventory.has_key(spriten):
            return self.sprite_inventory[spriten]
        else:
            self.sprite_inventory[spriten] = pyglet.resource.image(spriten)

    def load_sprites(self):
>>>>>>> bf4e7d430ded49df77106f136e98448decf831de
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

<<<<<<< HEAD
=======
def image(imgn):
    return g.getSprite(imgn)

>>>>>>> bf4e7d430ded49df77106f136e98448decf831de
class GraphicTestCase(unittest.TestCase):
    def testImageClass(self):
        for img in spriteInventory.values():
            self.assertIsInstance(img, pyglet.image.TextureRegion)
