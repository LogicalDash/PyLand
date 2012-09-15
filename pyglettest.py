import pyglet, math

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()
orb = pyglet.resource.image('orb.png')
golem = pyglet.resource.image('elgolem.png')



orbcoords = [(50, 100),(150, 200),(200,150),(300,300),(150,150)]
orbconnex = [(0,1),(3,4),(2,0),(2,3)]

golem.step = 0



golem.walk = [(0,2),(2,3),(3,4)]
golem.speed = 1


orbradius = 8

window.sprites = []

golem.x = 50
golem.y = 100
@window.event
def on_draw():
    window.clear()
    window.sprites = []
    for coord in orbcoords:
        window.sprites.append(pyglet.sprite.Sprite(orb, x = (coord[0] - orbradius), y = (coord[1] - orbradius), batch=batch))
    for connect in orbconnex:
        orb0 = orbcoords[connect[0]]
        orb1= orbcoords[connect[1]]
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2i', (orb0[0], orb0[1], orb1[0], orb1[1])))

    # move the golem
    # find out where it wants to go
    if golem.step < len(golem.walk):

        golem.later = golem.walk[golem.step+1]
        #get the slope of a line from golemnow to golemlater
        golem.rise = math.ceil(golem.later[1] - golem.y)
        golem.run = math.ceil(golem.later[0] - golem.x)
        # now change the golem's location appropriately
        updatestr = "golem moving from (" + golem.x + "," + golem.y + ")"
        golem.y += golem.rise * golem.speed
        golem.x += golem.run * golem.speed
        window.sprites.append(pyglet.sprite.Sprite(golem, x = golem.x, y = golem.y, batch=batch))        


    batch.draw()


pyglet.app.run()
