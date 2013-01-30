# This file is for the controllers for the things that show up on the screen when you play.
import pyglet
from place import Place
from math import floor, sqrt

def point_is_in(x, y, listener):
    return x >= listener.getleft() and x <= listener.getright() and y >= listener.getbot() and y <= listener.gettop()

def point_is_between(x, y, x1, y1, x2, y2):
    return x >= x1 and x <= x2 and y >= y1 and y <= y2

class MouseStruct:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.dy = 0
        self.dy = 0
        self.left = False
        self.middle = False
        self.right = False

class ModKeyStruct:
    def __init__(self):
        self.shift = False
        self.ctrl = False
        self.meta = False


class MouseListener:
    """MouseListener is a mix-in class. It provides basic
    functionality for handling four mouse events: on_mouse_motion,
    on_mouse_press, on_mouse_release, and on_mouse_drag.

    You may use the register(window) method defined here to register
    all four event listeners with the given window."""
    def get_mouse_rel_x(self):
        return self.mouse.x - self.getleft()
    def get_mouse_rel_y(self):
        return self.mouse.y - self.gettop()
    def get_mouse_offset_x(self):
        return self.mouse.x - self.x
    def get_mouse_offset_y(self):
        return self.mouse.y - self.y
    def is_mouse_in(self):
        return point_is_in(self.mouse.x, self.mouse.y, self)
    def distance_from_mouse(self):
        return sqrt(self.mouse_offset_x()**2 + self.mouse_offset_y()**2)
    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse.x = x
        self.mouse.y = y
        self.mouse.dx = dx
        self.mouse.dy = dy
    def on_mouse_press(self, x, y, button, modifiers):
        self.mouse.x = x
        self.mouse.y = y
        self.mouse.left = button == pyglet.window.mouse.LEFT
        self.mouse.middle = button == pyglet.window.mouse.MIDDLE
        self.mouse.right = button == pyglet.window.mouse.RIGHT
        self.key.shift = modifiers & pyglet.window.key.MOD_SHIFT
        self.key.ctrl = modifiers & pyglet.window.key.MOD_CTRL
        self.key.meta = (modifiers & pyglet.window.key.MOD_ALT or
                         modifiers & pyglet.window.key.MOD_OPTION)
        self.mouse.pressed = True
    def on_mouse_release(self, x, y, button, modifiers):
        self.mouse.x = x
        self.mouse.y = y
        self.mouse.left = button == pyglet.window.mouse.LEFT
        self.mouse.middle = button == pyglet.window.mouse.MIDDLE
        self.mouse.right = button == pyglet.window.mouse.RIGHT
        self.key.shift = modifiers & pyglet.window.key.MOD_SHIFT
        self.key.ctrl = modifiers & pyglet.window.key.MOD_CTRL
        self.key.meta = (modifiers & pyglet.window.key.MOD_ALT or
                         modifiers & pyglet.window.key.MOD_OPTION)
        self.mouse.pressed = False
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.mouse.x = x
        self.mouse.y = y
        self.mouse.dx = dx
        self.mouse.dy = dy
        self.mouse.left = buttons & pyglet.window.mouse.LEFT
        self.mouse.middle = buttons & pyglet.window.mouse.MIDDLE
        self.mouse.right = buttons & pyglet.window.mouse.RIGHT
        self.key.shift = modifiers & pyglet.window.key.MOD_SHIFT
        self.key.ctrl = modifiers & pyglet.window.key.MOD_CTRL
        self.key.meta = (modifiers & pyglet.window.key.MOD_ALT or
                         modifiers & pyglet.window.key.MOD_OPTION)
    def register(self, window):
        self.mouse = MouseStruct()
        self.key = ModKeyStruct()
        @window.event
        def on_mouse_motion(x, y, dx, dy):
            self.on_mouse_motion(x, y, dx, dy)
        @window.event
        def on_mouse_press(x, y, button, modifiers):
            self.on_mouse_press(x, y, button, modifiers)
        @window.event
        def on_mouse_release(x, y, button, modifiers):
            self.on_mouse_release(x, y, button, modifiers)
        @window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.on_mouse_drag(x, y, dx, dy, buttons, modifiers)


class Color:
    """Color(red=0, green=0, blue=0, alpha=255) => color

    This is just a container class for the (red, green, blue, alpha)
    tuples that Pyglet uses to identify colors. I like being able to
    get a particular element by name rather than number."""
    def __init__(self, name, r=0, g=0, b=0, a=255):
        self.name = name
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
    """Rect(x, y, width, height, color) => rect

    A rectangle with its lower-left corner at the given x and y. It
    supports only batch rendering.

    rect.addtobatch(batch, group=None) => None
    Call this function to draw the rect."""
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = Color.maybe_to_color(color)
        self.image = pyglet.image.create(width, height, pyglet.image.SolidColorImagePattern(color.tuple))
    def gettop(self):
        return self.y + self.height
    def getbot(self):
        return self.y
    def getleft(self):
        return self.x
    def getright(self):
        return self.x + self.width
    def addtobatch(self, batch, group=None):
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y, batch=batch, group=group)

class MenuItem:
    def __init__(self, text, onclick, closer=True):
        self.text = text
        self.onclick = onclick
        self.closer = closer
    def __eq__(self, other):
        if type(other) is type(""):
            return self.text == other
        else:
            return self.text == other.text
    def __gt__(self, other):
        if type(other) is type(""):
            return self.text > other
        return self.text > other.text
    def __ge__(self, other):
        if type(other) is type(""):
            return self.text >= other
        return self.text >= other.text
    def __lt__(self, other):
        if type(other) is type(""):
            return self.text < other
        return self.text < other.text
    def __le__(self, other):
        if type(other) is type(""):
            return self.text <= other
        return self.text <= other.text
    def __repr__(self):
        return self.text
    def __str__(self):
        return self.text
    def __hash__(self):
        return hash(self.text)
    def getlabel(self, x, y, fontface, fontsize, color, batch, group):
        return pyglet.text.Label(self.text, fontface, fontsize, color=color, x=x, y=y, batch=batch, group=group, anchor_x='left', anchor_y='top')


class MenuList:
    def __init__(self):
        self.items = []
        self.sorted = True
        self.textmap = {}
    def __getitem__(self, i):
        if i is None:
            return None
        if type(i) is type(1):
            if not self.sorted:
                self.sort()
                self.sorted = True
            return self.items[i]
        else:
            return self.nmap[i]
    def __len__(self):
        return len(self.items)
    def index(self, thingus):
        return self.items.index(thingus)
    def insert_item(self, i, text, onclick, closer=True):
        mi = MenuItem(text, onclick, closer)
        self.textmap[text] = mi
        self.items.insert(i, mi)
        return mi
    def reverse(self):
        self.items.reverse()
        return self
        def sort(self):
        # This just sorts by item name. I may want to make it sort by quantity eventually.
            if not self.sorted:
                self.items.sort()
                self.sorted = True
                return True # I did in fact sort
            else:
                return False # no I didn't
    def remove_item(self, i):
        del self.item[i]
    def sort(self):
        # This just sorts by item name. I may want to make it sort by quantity eventually.
        if not self.sorted:
            self.items.sort()

class Menu(MouseListener):
    def __init__(self, x, y, width, height, style):
        self.style = style
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.bgcolor = Color.maybe_to_color(style.bg_inactive)
        self.inactive_color = Color.maybe_to_color(style.fg_inactive)
        self.active_color = Color.maybe_to_color(style.fg_active)
        self.fontface = style.fontface
        self.fontsize = style.fontsize
        self.spacing = style.spacing
        self.items = MenuList()
        self.rect = Rect(x, y, width, height, self.bgcolor)
    def __getitem__(self, i):
        return self.items[i]
    def getstyle(self):
        return Style(self.fontface, self.fontsize, self.spacing, self.bgcolor, self.bgcolor, self.inactive_color, self.active_color)
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
    def on_mouse_press(self, x, y, button, modifiers):
        MouseListener.on_mouse_press(self, x, y, button, modifiers)
        if self.is_mouse_in():
            for item in self.items:
                if self.moused_over_item(item):
                    self.pick = (item, button, modifiers)
                    return
    def on_mouse_release(self, x, y, button, modifiers):
        MouseListener.on_mouse_release(self, x, y, button, modifiers)
        if self.is_mouse_in() and self.pick is not None:
            if self.moused_over_item(self.pick[0]) and button == self.pick[1] and modifiers == self.pick[2]:
                self.pick[0].onclick()
        self.pick = None
    def insert_item(self, i, text, onclick, closer=True):
        if i > len(self.items):
            i = len(self.items)
        added = self.items.insert_item(i, text, onclick, closer)
        return added
    def remove_item(self, i):
        self.items.remove_item(i)
    def is_mouse_over_item(self, item):
        if type(item) is type(1):
            item = self.items[item]
        if None in [item.bot_rel, item.top_rel]:
            return False
        return item.bot_rel <= self.get_mouse_rel_y() <= item.top_rel
    def addtobatch(self, batch, menugroup, labelgroup, start=0):
        self.rect.addtobatch(batch, menugroup)
        items_height = 0
        draw_until = start
        while items_height < self.getheight() and len(self.items) > draw_until:
            items_height += self.fontsize + self.spacing
            draw_until += 1
        prev_height = self.getheight
        for item in self.items:
            item.top_rel = prev_height
            item.bot_rel = prev_height - self.fontsize
            prev_height -= self.fontsize + self.spacing
        i = start
        drawn = []
        while i < draw_until:
            color = self.inactive_color.tuple
            if self.is_mouse_in():
                if self.is_mouse_over_item(i):
                    color = self.active_color.tuple
            drawn.append(self.items[i].getlabel(self.getleft(), self.items[i].top_rel + self.gettop(), self.fontface, self.fontsize, color, batch, labelgroup))
            i += 1

class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    def __init__(self, place, x, y, r, spotgraph):
        self.place = place
        self.x = x
        self.y = y
        self.r = r
        self.spotgraph = spotgraph
        self.img = pyglet.resource.image('orb.png')
    def __repr__(self):
        coords = "(%i,%i)" % (self.x, self.y)
        return "Spot at " + coords + " representing " + str(self.place)
    def __str__(self):
        return "(%i,%i)->%s" % (self.x, self.y, str(self.place))
    def getleft(self):
        return self.x - self.r
    def getbot(self):
        return self.y - self.r
    def gettop(self):
        return self.y + self.r
    def getright(self):
        return self.x + self.r
    def gettup(self):
        return (self.img, self.getleft(), self.getbot())
    def __iter__(self):
        return iter([self.img, self.getleft(), self.getbot()])

class SpotGraph:
    places = {}
    spots = []
    edges = []
    edges_to_draw = []
    def add_spot(self, spot):
        self.spots.append(spot)
        self.places[spot.place] = spot
    def add_place(self, place, x, y, r=8):
        newspot = Spot(place, x, y, r, self)
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
        self.edges_to_draw.append(((spot1.x, spot1.y, spot2.x, spot2.y), (255, 255)*4))
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
    # I think I want to redo the coordinates on these so that they are
    # relative to the associated spot.
    def __init__(self, start, spotgraph, img, item=None, x=None, y=None):
        self.spotgraph = spotgraph
        if item is not None:
            self.item = item
        if x is not None and y is not None:
            self.x = x
            self.y = y
        elif isinstance(start, Spot):
            self.curspot = start
            self.x = start.x
            self.y = start.y
        elif isinstance(start, Place):
            self.curspot = self.spotgraph.places[start]
            self.x = self.curspot.x
            self.y = self.curspot.y
        else:
            raise ValueError("No way to tell where to put this pawn.")
        self.list = [img, self.x, self.y]
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
    def setx(self, newx):
        self.x = newx
        self.list[1] = newx
    def sety(self, newy):
        self.y = newy
        self.list[2] = newy
    def gettup(self):
        return tuple(self.list)
    def __iter__(self):
        return iter(self.list)
    def move(self, rep = 1):
        if self.route is None:
            return
        orig = self.prevspot()
        dest = self.nextspot()
        speed = self.curspeed() * rep
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
            if self.step >= len(self.route) - 1:
                self.step = 0
                self.route = None
            self.step += 1
            return
        x_traveled = x_total * self.trip_completion
        y_traveled = y_total * self.trip_completion
        self.setx(orig.x + x_traveled)
        self.sety(orig.y + y_traveled)
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

class PawnTimer:
    def __init__(self, pawns):
        self.pawns = pawns
        self.delay = 0.0
    def movepawns(self, ts, freq):
        self.delay += ts - freq
        # when the cumulative delay is longer than the time between frames,
        # skip a frame to make up for it
        reps = 1
        while self.delay > freq:
            reps += 1
            self.delay -= freq
        for pawn in self.pawns:
            pawn.move(reps)

class Canvas:
    def __init__(self, width, height, texture, spotgraphs=[], pawns=[]):
        self.width = width
        self.height = height
        self.tex = texture
        self.spotgraphs = spotgraphs
        self.pawns = pawns

class Style:
    def __init__(self, name, fontface, fontsize, spacing, bg_inactive, bg_active, fg_inactive, fg_active):
        self.name = name
        self.fontface = fontface
        self.fontsize = fontsize
        self.spacing = spacing
        self.bg_inactive = bg_inactive
        self.bg_active = bg_active
        self.fg_inactive = fg_inactive
        self.fg_active = fg_active

class WidgetFactory:
    def __init__(self, db, window=None, batch=None):
        self.db = db
        if window is None:
            self.window = pyglet.window.Window()
        else:
            self.window = window
        if batch is None:
            self.batch = pyglet.graphics.Batch()
        else:
            self.batch = batch

class WidgetFactoryTestCase(unittest.TestCase):
    def setUp(self):
        