# This file is for the controllers for the things that show up on the screen when you play.
import pyglet
from place import Place

class Color:
    def __init__(self, r=0, g=0, b=0, a=255):
        self.red = r
        self.green = g
        self.blue = b
        self.alpha = a
        self.tuple = (r, g, b, a)
    def maybe_to_color(arg):
        if isinstance(arg, Color):
            return arg
        elif type(arg) is tuple:
            if len(arg) == 3:
                return Color(arg[0], arg[1], arg[2], 255)
            if len(arg) == 4:
                return Color(*arg)
        else:
            return None

class Rect:
    indices = [2, 0, 1, 2, 3, 1]
    def __init__(self, left, bottom, right, top, color):
        self.vertices = ('v2i', (left, bottom, left, top, right, bottom, right, top))
        self.color_verts = ('c4B', color.tuple*4)
    def addtobatch(self, batch, group):
        batch.add_indexed(4, pyglet.gl.GL_TRIANGLES, group, self.indices, self.vertices, self.color_verts)

class MenuItem:
    """Controller for the clickable labels that fill up menus. Mouse
    events should be passed here, rather than to the label itself."""
    def __init__(self, text, ct, onclick, img):
        self.text = text
        self.onclick = onclick
        self.loadimg(img)
        self.ct = ct
    def __eq__(self, other):
        return self.text == other.text
    def __gt__(self, other):
        return self.text > other.text
    def __ge__(self, other):
        return self.text >= other.text
    def __lt__(self, other):
        return self.text < other.text
    def __le__(self, other):
        return self.text <= other.text
    def loadimg(self, img):
        if isinstance(img, pyglet.image.TextureRegion):
            self.img = img
        elif type(img) == type(""):
            self.img = pyglet.resource.image(img)
        else:
            self.img = None
    def getlabel(self, x, y, fontface, fontsize, batch, group):
        return pyglet.text.Label(self.text, fontface, fontsize, x=x, y=y, batch=batch, group=group,
                                 anchor_x='left', anchor_y='top')


class MenuList:
    def __init__(self):
        self.items = []
        self.sorted = True
    def __getitem__(self, i):
        return self.items[i]
    def __len__(self):
        return len(self.items)
    def add_item(self, name, ct, onclick, img):
        if name in [item.text for item in self.items]:
            return
        else:
            self.items.append(MenuItem(name, ct, onclick, img))
            self.sorted = False
    def remove_item(self, name):
        self.items.remove(name) # not sure if this will work given a name of string type.
    def remove(self, name):
        self.items.remove(name)
    def sort(self):
        # This just sorts by item name. I may want to make it sort by quantity eventually.
        self.items.sort()

class Menu:
    def __init__(self, x, y, width, height, bgcolor, fgcolor, fontface, fontsize):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bgcolor = Color.maybe_to_color(bgcolor)
        self.fgcolor = Color.maybe_to_color(fgcolor)
        self.fontface = fontface
        self.fontsize = fontsize
        self.items = MenuList()
        self.rect = Rect(x, y, x+width, y+height, bgcolor)
    def getleft(self):
        return self.x
    def getbot(self):
        return self.y
    def getheight(self):
        return self.height
    def gettop(self):
        return self.y + self.height
    def getwidth(self):
        return self.width
    def getright(self):
        return self.x + self.width
    def get_edge_verts(self):
        return ('v2i', (self.x, self.y, self.x+self.width, self.y, self.x+self.width,
                        self.y+self.height, self.x, self.y+self.height))
    def get_color_verts(self):
        return ('c4B', self.bgcolor.tuple*4)
    def add_item(self, name, number, onclick, icon=None):
        self.items.add_item(name, number, onclick, icon)
    def remove_item(self, name):
        self.items.remove_item(name)
    def item_height(self, i):
        if i > len(self.items):
            return self.fontsize
        elif self.items[i].img is None:
            return self.fontsize
        elif self.items[i].img.height > self.fontsize:
            return self.items[i].img.height
        else:
            return self.fontsize
    def addtobatch(self, batch, menugroup, labelgroup, start=0, spacing=6):
        # Alpha layer doesn't work; no transparent menus
        self.rect.addtobatch(batch, menugroup)
        if not self.items.sorted:
            self.items.sort()
        items_height = 0
        draw_until = start
        while items_height < self.getheight() and len(self.items) > draw_until:
            items_height += self.item_height(draw_until) + spacing
            draw_until += 1
        draw_at = self.gettop()
        i = start
        drawn = []
        while i < draw_until:
            drawn.append(self.items[i].getlabel(self.getleft(), draw_at, self.fontface, self.fontsize,
                                                batch, labelgroup))
            draw_at -= self.item_height(i) + spacing
            i += 1


    

class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    def __init__(self, place, x, y, spotgraph):
        self.place = place
        self.x = x
        self.y = y
        self.spotgraph = spotgraph
    def __repr__(self):
        coords = "(%i,%i)" % (self.x, self.y)
        return "Spot at " + coords + " representing " + str(self.place)
    def __str__(self):
        return "(%i,%i)->%s" % (self.x, self.y, str(self.place))
                

class SpotGraph:
    places = {}
    spots = []
    edges = []
    edges_to_draw = []
    def add_spot(self, spot):
        self.spots.append(spot)
        self.places[spot.place] = spot
    def add_place(self, place, x, y):
        newspot = Spot(place, x, y, self)
        self.add_spot(newspot)
        self.connect_portals(newspot)
    def are_connected(self, spot1, spot2):
        return ((spot1, spot2) in self.edges) or ((spot2, spot1) in self.edges)
    def neighbors(self, spot1):
        r = []
        for edge in self.edges:
            if edge[0] is spot1:
                r.append(edge[1])
            if edge[1] is spot1:
                r.append(edge[0])
        return r
    def add_edge(self, spot1, spot2):
        self.edges.append((spot1, spot2))
        self.edges_to_draw.append((spot1.x, spot1.y, spot2.x, spot2.y))
    def connect_portals(self, spot):
        for portal in spot.place.portals:
            ps = self.places.keys()
            if portal.orig in ps and portal.dest in ps:
                self.add_edge(self.places[portal.orig], self.places[portal.dest])
                


class Pawn:
    """Data structure to represent things that move about between
    Spots on the screen.  Mostly these will represent characters or vehicles.

    The constructor takes three arguments: start, graph, and speed.

    start is a Spot. The Pawn will appear there at first.

    graph is a list of Spots. It should contain
    every Place that the Pawn ought to know about. That doesn't
    necessarily mean every Place in the game world, or even every
    Place that the character *represented by* the Pawn should know
    about. Pawns are not concerned with pathfinding, only with moving
    along a prescribed route at a prescribed speed.

    To give such a route to a Pawn, call waypoint. It takes two
    arguments: place and speed. place is the Place to go to next. The
    Pawn actually has no idea whether or not Places are connected to
    one another, so check first to make sure they are, otherwise the
    Pawn will happily wander where there is no Passage. speed is a
    floating point representing the portion of the distance between
    this Place and the previous one on the route that the Pawn should
    cover in a single frame. This should be calculated as the seconds
    of real time that the travel should take, divided by the game's
    screen-updates-per-second."""
    trip_completion = 0.0
    step = 0
    route = None
    def __init__(self, start, spotgraph):
        self.spotgraph = spotgraph
        if isinstance(start, Spot):
            self.curspot = start
            self.x = start.x
            self.y = start.y
        elif isinstance(start, Place):
            self.curspot = self.spotgraph.places[start]
            self.x = self.curspot.x
            self.y = self.curspot.y
    def curstep(self):
        if self.step >= len(self.route):
            return None
        if self.route is not None:
            return self.route[self.step]
    def curspeed(self):
        return self.curstep()[1]
    def nextspot(self):
        return self.curstep()[0]
    def prevspot(self):
        if self.step == 0:
            return self.curspot
        self.step -= 1
        r = self.curstep()[0]
        self.step += 1
        return r
    def move(self):
        if self.route is None:
            return
        orig = self.prevspot()
        dest = self.nextspot()
        speed = self.curspeed()
        x_total = float(dest.x - orig.x)
        y_total = float(dest.y - orig.y)
        self.trip_completion += speed
        if self.trip_completion >= 1.0:
            # Once I have my own event-handling infrastructure set up,
            # this should fire a "trip completed" event.
            self.trip_completion = 0.0
            self.curspot = dest
            self.x = dest.x
            self.y = dest.y
            self.step += 1
            if self.step >= len(self.route):
                self.step = 0
                self.route = None
            return
        x_traveled = x_total * self.trip_completion
        y_traveled = y_total * self.trip_completion
        self.x = orig.x + x_traveled
        self.y = orig.y + y_traveled
    def waypoint(self, dest, speed):
        if self.route is None:
            if isinstance(dest, Spot):
                self.route = [(dest, speed)]
            elif dest in self.spotgraph.places.keys():
                self.route = [(self.spotgraph.places[dest],speed)]
            else:
                return
        else:
            if isinstance(dest, Spot):
                self.route.append((dest, speed))
            elif dest in self.spotgraph.places.keys():
                self.route.append((self.spotgraph.places[dest], speed))
            else:
                return
    def cancel_route(self):
        """Canceling the route will let the Pawn reach the next node
        before stopping to await a new waypoint. If you want it
        stranded between two nodes, call delroute instead."""
        self.route = [self.curstep()]
    def delroute(self):
        self.route = None
    def extend_graph(self, spot):
        """Add a new Spot to the graph, where the Place is displayed
        on-screen at the given coordinates. Appropriate for when the
        character learns of a new place they can go to."""
        self.graph.append(spot)
        self.places[spot.place] = spot

