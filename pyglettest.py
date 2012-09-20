import pyglet, math, threading
from widgets import *
from place import Place

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()
orb = pyglet.resource.image('orb.png')
elgolem = pyglet.resource.image('rltiles/dc-mon0/0golem/electric_golem.bmp')

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

for edge in spotgraph.edges:
    print "(" + str(edge[0].place) + "->" + str(edge[1].place) + ")"
pawns = []


@window.event
def on_draw():
    window.clear()
    window.sprites = []
    gl_lines_to_draw = []

    for edge_to_draw in spotgraph.edges_to_draw:
        gl_lines_to_draw.append(('v2i', edge_to_draw))

    for spot in spotgraph.spots:
        window.sprites.append(pyglet.sprite.Sprite(orb, x = (spot.x - orb.radius), y = (spot.y - orb.radius), batch = batch))

    for pawn in pawns:
        window.sprites.append(pyglet.sprite.Sprite(pawn.img, x = pawn.x, y=pawn.y, batch=batch))

    for line in gl_lines_to_draw:
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, line)
        
    batch.draw()
    pyglet.graphics.glFlush()

for pawn in pawns:
    pyglet.clock.schedule_interval(pawn.move, 1/60.)
pyglet.app.run()
