import pyglet, math, threading

window = pyglet.window.Window()
batch = pyglet.graphics.Batch()
orb = pyglet.resource.image('orb.png')
elgolem = pyglet.resource.image('elgolem.png')

class Mover:
    testing = False
    xdir = 1
    ydir = 1
    trip_completion = 0.0
    def __init__(self, start, route, graph, speed):
        self.x = start[0]
        self.y = start[1]
        self.route = route
        self.speed = speed
        self.step = 0
        self.graph = graph
    def curstep(self):
        if self.step >= len(self.route):
            return None
        else:
            return self.route[self.step]
    def nextnode(self):
        if self.step >= len(self.route):
            return None
        else:
            return self.graph[self.curstep()[1]]
    def prevnode(self):
        if self.step >= len(self.route):
            return self.graph[self.route[-1][1]]
        else:
            return self.graph[self.curstep()[0]]
    def move(self, ts):
        dest = self.nextnode()
        if dest is None:
            return
        dest_x = dest[0]
        dest_y = dest[1]
        orig = self.prevnode()
        orig_x = orig[0]
        orig_y = orig[1]
        rise = dest_y - orig_y
        if rise > 0:
            self.ydir = 1
        elif rise == 0:
            self.ydir = 0
        elif rise < 0:
            self.ydir = -1
        run = dest_x - orig_x
        if run > 0:
            self.xdir = 1
        elif run == 0:
            self.xdir = 0
        elif run < 0:
            self.xdir = -1

        # Progress along roads is considered as a proportion of the
        # total length of the road. Right now I haven't got roads of
        # different lengths.
        x_total = float(dest_x - orig_x)
        y_total = float(dest_y - orig_y)
        self.trip_completion += self.speed
        if self.trip_completion >= 1.0:
            self.trip_completion = 0.0
            self.step += 1
            self.x = dest_x
            self.y = dest_y
            return
        x_traveled = x_total * self.trip_completion
        y_traveled = y_total * self.trip_completion
        self.x = orig_x + x_traveled
        self.y = orig_y + y_traveled
            
        
        

orbcoords = [(50, 100),(150, 200),(200,150),(300,300),(150,150)]
orbconnex = [(0,1),(3,4),(2,0),(2,3)]
golem = Mover(orbcoords[0], [(0,2),(2,3),(3,4)], orbcoords, 0.01)
golem.testing = True

orb.radius = 8

@window.event
def on_draw():
    window.clear()
    window.sprites = []
    for coord in orbcoords:
        window.sprites.append(pyglet.sprite.Sprite(orb, x = (coord[0] - orb.radius), y = (coord[1] - orb.radius), batch=batch))

    window.sprites.append(pyglet.sprite.Sprite(elgolem, x = golem.x, y = golem.y, batch=batch))
        
    for connect in orbconnex:
        orb0 = orbcoords[connect[0]]
        orb1= orbcoords[connect[1]]
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2i', (orb0[0], orb0[1], orb1[0], orb1[1])))
        
    batch.draw()
    pyglet.graphics.glFlush()

pyglet.clock.schedule_interval(golem.move, 1/60.)
pyglet.app.run()
