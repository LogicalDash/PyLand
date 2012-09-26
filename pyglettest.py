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

golem = Pawn(momsroom, spotgraph)
golem.img = elgolem

efreet = Pawn(myroom, spotgraph)
efreet.img = efreetimg

pawns = [golem, efreet]

golem.waypoint(longhall, 0.01)
golem.waypoint(livingroom, 0.02)
golem.waypoint(diningarea, 0.03)
golem.waypoint(kitchen, 0.1)

for place in [mybathroom, myroom, livingroom, longhall, momsbathroom]:
    efreet.waypoint(place, 0.02)

def noop():
    pass

menu = Menu(0,0,200,400,Color(44,44,44,11),Color(200,200,200),"DejaVu Sans",10)

for word in ["Hi", "there", "you", "cool", "guy"]:
    menu.add_item(word, 1, noop)


@window.event
def on_draw():
    window.clear()
    batch = pyglet.graphics.Batch()
    edgegroup = pyglet.graphics.OrderedGroup(0)
    orbgroup = pyglet.graphics.OrderedGroup(1)
    spritegroup = pyglet.graphics.OrderedGroup(2)
    menugroup = pyglet.graphics.OrderedGroup(3)
    labelgroup = pyglet.graphics.OrderedGroup(4)
    sprites = []

    menu.addtobatch(batch, menugroup, labelgroup)

    for edge_to_draw in spotgraph.edges_to_draw:
        batch.add(2, pyglet.gl.GL_LINES, edgegroup, ('v2i', edge_to_draw))

    for spot in spotgraph.spots:
        sprites.append(pyglet.sprite.Sprite(orb, x = (spot.x - orb.radius), y = (spot.y - orb.radius), batch = batch, group=orbgroup))

    for pawn in pawns:
        sprites.append(pyglet.sprite.Sprite(pawn.img, x = pawn.x, y=pawn.y, batch=batch, group=spritegroup))

        
    batch.draw()
    pyglet.graphics.glFlush()

def movepawns(ts):
    for pawn in pawns:
        pawn.move()
pyglet.clock.schedule_interval(movepawns, 1/60.)
pyglet.app.run()
