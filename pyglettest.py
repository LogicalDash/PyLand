import pyglet

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()
orb = pyglet.resource.image('orb.png')

orbcoords = [(50, 100),(150, 200),(200,150),(300,300),(150,150)]
orbconnex = [(0,1),(3,4),(2,0),(2,3)]
orbradius = 8


@window.event
def on_draw():
    window.clear()
    window.sprites = []
    for connect in orbconnex:
        orb0 = orbcoords[connect[0]]
        orb1= orbcoords[connect[1]]
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2i', (orb0[0], orb0[1], orb1[0], orb1[1])))

    for coord in orbcoords:
        window.sprites.append(pyglet.sprite.Sprite(orb, x = (coord[0] - orbradius), y = (coord[1] - orbradius), batch=batch))
    batch.draw()


pyglet.app.run()
