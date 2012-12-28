import pyglet, math, threading
from widgets import *
from place import Place
from graphics import load_rltile

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()
orb = pyglet.resource.image('orb.png')
elgolem = load_rltile('rltiles/dc-mon0/0golem/electric_golem.bmp')
efreetimg = load_rltile('rltiles/dc-mon1/e/efreet.bmp')


orb.radius = 8

myroom = Place("My Room")
livingroom = Place("Living Room")
diningarea = Place("Dining Area")
kitchen = Place("Kitchen")
longhall = Place("Long Hall")
guestroom = Place("Guest Room")
mybathroom = Place("My Bathroom")
momsbathroom = Place("Mom's Bathroom")
momsroom = Place("Mom's Room")

myroom.connect_to(livingroom)
myroom.connect_to(mybathroom)
myroom.connect_to(guestroom)
livingroom.connect_to(myroom)
livingroom.connect_to(diningarea)
livingroom.connect_to(longhall)
mybathroom.connect_to(myroom)
mybathroom.connect_to(guestroom)
mybathroom.connect_to(livingroom)
guestroom.connect_to(livingroom)
guestroom.connect_to(myroom)
guestroom.connect_to(mybathroom)
diningarea.connect_to(kitchen)
diningarea.connect_to(livingroom)
longhall.connect_to(livingroom)
longhall.connect_to(momsroom)
longhall.connect_to(momsbathroom)
momsroom.connect_to(momsbathroom)
momsroom.connect_to(longhall)
momsbathroom.connect_to(longhall)
momsbathroom.connect_to(momsroom)


spotgraph = SpotGraph()
spotgraph.add_place(momsroom,50,50)
spotgraph.add_place(momsbathroom,50, 100)
spotgraph.add_place(longhall, 100, 100)
spotgraph.add_place(livingroom, 150, 50)
spotgraph.add_place(diningarea, 150, 200)
spotgraph.add_place(kitchen, 100, 200)
spotgraph.add_place(myroom,200,50)
spotgraph.add_place(mybathroom,250,100)
spotgraph.add_place(guestroom,200,200)

golem = Pawn(momsroom, spotgraph, elgolem)


efreet = Pawn(myroom, spotgraph, efreetimg)


pawns = [golem, efreet]

golem.waypoint(longhall, 0.01)
golem.waypoint(livingroom, 0.02)
golem.waypoint(diningarea, 0.03)
golem.waypoint(kitchen, 0.1)

for place in [mybathroom, myroom, livingroom, longhall, momsbathroom]:
    efreet.waypoint(place, 0.02)

def noop():
    print "NOPE"

menu = Menu(window, 0, 33, 100, 200, solarized_dark_scheme, "DejaVu Sans", 16)

for word in ["Hi", "there", "you", "cool", "guy"]:
    menu.add_item(word, noop, 1)

bar = MenuBar(window, 32, solarized_dark_scheme, "DejaVu Sans", 16)
bar.add_menu("File")

def add_edges_to_batch(edges, batch, group):
    # Each vertex of each edge should have a corresponding color vertex.
    # Each edge should be paired with the color vertices of both its own vertices.
    for item in edges:
        edge = item[0]
        color = item[1]
        batch.add(2, pyglet.gl.GL_LINES, group, ('v2i', edge), ('c4B', color))

def add_sprites_to_batch(spritelist, batch, group):
    # Each item in spritelist should be a tuple of the form
    # (img, x, y)
    return [pyglet.sprite.Sprite(img, x=x, y=y, batch=batch, group=group) for (img, x, y) in spritelist]

class MenuOrderedGroup(pyglet.graphics.OrderedGroup):
    def set_state(self):
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glEnable(pyglet.gl.GL_TEXTURE_2D)
    def unset_state(self):
        pyglet.gl.glDisable(pyglet.gl.GL_BLEND)
        pyglet.gl.glDisable(pyglet.gl.GL_TEXTURE_2D)

@window.event
def on_draw():
    window.clear()


    edgegroup = pyglet.graphics.OrderedGroup(0)
    orbgroup = pyglet.graphics.OrderedGroup(1)
    pawngroup = pyglet.graphics.OrderedGroup(2)
    menugroup = MenuOrderedGroup(3)
    labelgroup = pyglet.graphics.OrderedGroup(4)

    add_edges_to_batch(spotgraph.edges_to_draw, batch, edgegroup)

    spotsprites = add_sprites_to_batch([(orb, spot.getleft(), spot.getbot()) for spot in spotgraph.spots], batch, orbgroup)

    pawnsprites = add_sprites_to_batch([tuple(pawn) for pawn in pawns], batch, pawngroup)

    bardrawn = bar.addtobatch(batch, menugroup, labelgroup)
    menudrawn = menu.addtobatch(batch, menugroup, labelgroup)

    batch.draw()
    pyglet.graphics.glFlush()
    del spotsprites
    del pawnsprites
    del bardrawn
    del menudrawn

mouse_listeners = [menu]

for listener in mouse_listeners:
    listener.register(window)

pt = PawnTimer(pawns)
pyglet.clock.schedule_interval(pt.movepawns, 1/60., 1/60.)

pyglet.app.run()
