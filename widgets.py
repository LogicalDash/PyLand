# This file is for the controllers for the things that show up on the screen when you play.
import pyglet
from place import Place
from math import floor, sqrt

def point_is_in(x, y, listener):
    return x >= listener.getleft() and x <= listener.getright() and y >= listener.getbot() and y <= listener.gettop()

def point_is_between(x, y, x1, y1, x2, y2):
    return x >= x1 and x <= x2 and y >= y1 and y <= y2




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
        self.tup = (r, g, b, a)
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
    def __init__(self, wf, x, y, width, height, color):
        self.wf = wf
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = Color.maybe_to_color(color)
        self.image = pyglet.image.create(width, height, pyglet.image.SolidColorImagePattern(color.tup))
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
    def draw(self, group=None):
        self.sprite = pyglet.sprite.Sprite(self.image, self.x - self.wf.board.x,
                                           self.y - self.wf.board.y, batch=self.wf.batch, group=group)

class MenuItem:
    def __init__(self, wf, text, onclick, style, closer=True):
        self.wf = wf
        self.text = text
        self.onclick = onclick
        self.closer = closer
        self.style = style
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
    def show(self):
        if None in [self.y, self.fontsize]:
            raise Exception("I can't show the label %s without knowing where it is, first." % self.text)
        else:
            self.wf.addclickable(self)
            self.visible = True
    def hide(self):
        self.visible = False
        self.wf.rmclickable(self)
    def set_pressed(self, b, m):
        if b == pyglet.window.mouse.LEFT:
            self.pressed = True
    def unset_pressed(self, b, m):
        if self.pressed:
            if b == pyglet.window.mouse.LEFT:
                self.onclick()
    def getbot(self):
        return self.y
    def gettop(self):
        if None in [self.y, self.fontsize]:
            return None
        else:
            return self.y + self.fontsize
        return pyglet.text.Label(self.text, fontface, fontsize, color=color, x=x, y=y, batch=batch, group=group, anchor_x='left', anchor_y='bottom')
    def draw(self, group=None):
        if self.visible:
            if self.hovered:
                color = self.style.fg_active
            else:
                color = self.style.fg_inactive
            return pyglet.text.Label(self.text, self.style.fontface, self.style.fontsize,
                                     color=color, x=self.x, y=self.y, batch=self.wf.batch,
                                     group=group)

class Menu:
    def __init__(self, wf, xprop, yprop, wprop, hprop, style):
        self.wf = wf
        self.style = style
        if xprop < 0.0: # place lower-left corner (100*|xprop|)% from the right of the window
            self.x = self.wf.window.width + (self.wf.window.width * xprop)
        else: # place lower-left corner (100*|xprop|)% from the left of the window
            self.x = self.wf.window.width * xprop
        if yprop < 0.0:  # place lower-left corner (100*|yprop|)% from the top of the window
            self.y = self.wf.window.height + (self.wf.window.height * yprop)
        else: # place lower-left corner (100*|yprop|)% from the bottom of the window
            self.y = self.wf.window.height * yprop
        self.width = self.wf.window.width * abs(wprop)
        self.height = self.wf.window.height * abs(hprop)
        if wprop < 0.0: # width extends to the left
            self.y -= self.width
        if hprop < 0.0: # height extends downward
            self.x -= self.height
        self.bgcolor = Color.maybe_to_color(style.bg_inactive)
        self.inactive_color = Color.maybe_to_color(style.fg_inactive)
        self.active_color = Color.maybe_to_color(style.fg_active)
        self.fontface = style.fontface
        self.fontsize = style.fontsize
        self.spacing = style.spacing
        self.items = []
        self.rect = Rect(self.wf, self.x, self.y, self.width, self.height, self.style.bgcolor)
        self._scrolled_to = 0
        self.visible = False
    def __getitem__(self, i):
        return self.items.__getitem__(i)
    def __delitem__(self, i):
        return self.items.__delitem__(i)
    def show(self):
        self.visible = True
        self.wf.clickables.append(self)
        self.wf.hoverables.append(self)
    def hide(self):
        self.visible = False
        self.wf.clickables.remove(self)
        self.wf.hoverables.remove(self)
    def getstyle(self):
        return self.style
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
    def insert_item(self, i, text, onclick, closer=True):
        if i > len(self.items):
            i = len(self.items)
        newitem = MenuItem(self.wf, text, onclick, self.style, closer)
        self.items.insert(i, newitem)
        return newitem
    def remove_item(self, it):
        self.items.remove_item(it)
    def addtobatch(self, batch, menugroup, labelgroup, start=0):
        if not self.visible:
            return False
        self.rect.addtobatch(batch, menugroup)
        items_height = 0
        draw_until = start
        while items_height < self.getheight() and len(self.items) > draw_until:
            items_height += self.style.fontsize + self.style.spacing
            draw_until += 1
        prev_height = self.gettop()
        for item in self.items:
            item.top = prev_height - self.style.spacing
            item.bot = prev_height - self.style.spacing - self.style.fontsize 
            item.x = self.getleft()
            item.y = item.bot
            prev_height -= self.fontsize + self.spacing
        i = start
        drawn = []
        while i < draw_until:
            drawing = self.items[i]
            drawing.show()
            drawn.append(drawing.draw(labelgroup))
            i += 1
        return True

    def draw(self):
        return self.addtobatch(self.wf.batch, self.wf.menugroup,
                               self.wf.labelgroup, self._scrolled_to)


class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    def __init__(self, wf, place, x, y, r, imgname, spotgraph):
        self.wf = wf
        self.place = place
        self.x = x
        self.y = y
        self.r = r
        self.spotgraph = spotgraph
        self.img = self.wf.db.getimg(imgname)
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
    def __init__(self, wf, places=[], portals=[]):
        self.wf = wf
        self.w = wf.board.getwidth()
        self.h = wf.board.getheight()
        self.place2spot = {}
        self.port2edge = {}
        for place in places:
            if self.wf.db.havespot(place):
                self.place2spot[place] = self.wf.db.getspot(place.name)
            else:
                # just drop it somewhere.
                # TODO change this out for something nicer
                self.add_place_sensibly(place)
                db.savespot(self.place2spot[place])
        for port in portals:
            if port.orig not in self.place2spot.keys():
                if self.wf.db.havespot(port.orig):
                    self.place2spot[port.orig] = self.wf.db.getspot(place.name)
                    
            self.port2edge[port] = (self.place2spot[port.orig], self.place2spot[port.dest])
    def add_spot(self, spot):
        self.place2spot[spot.place] = spot
    def add_place(self, place, x, y, r=8):
        newspot = Spot(place, x, y, r, self)
        self.add_spot(newspot)
        self.connect_portals(newspot)
    def add_place_sensibly(self, place):
        # TODO actually select a sensible spot
        x = rand(0, self.w)
        y = rand(0, self.h)
        self.add_place(place, x, y, 8)
    def spots_connected(self, spot1, spot2):
        return ((spot1, spot2) in self.edges) or ((spot2, spot1) in self.edges)
    def neighbors(self, spot1):
        r = []
        for edge in self.edges:
            if edge[0] is spot1:
                r.append(edge[1])
            if edge[1] is spot1:
                r.append(edge[0])
        return r
    def add_portal(self, port):
        if not self.place2spot.has_key(port.orig):
            self.add_place_sensibly(port.orig)
        if not self.place2spot.has_key(port.dest):
            self.add_place_sensibly(port.dest)
        spot1 = self.place2spot[port.orig]
        spot2 = self.place2spot[port.dest]
        edge = (spot1, spot2)
        self.port2edge[port] = edge
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
    # Coordinates should really be relative to the Board and not the
    # uh, canvas? is that what they are called in pyglet?
    def __init__(self, wf, start, img, x=None, y=None):
        self.wf = wf
        if x is not None and y is not None:
            self.x = x
            self.y = y
        else:
            self.x = start.x
            self.y = start.y
        self.curspot = start
        self.tup = (img, self.x, self.y)
        self.route = []
        self.step = 0
        self.trip_completion = 0.0
        self.visible = False
    def show(self):
        self.visible = True
        self.wf.clickables.append(self)
        self.wf.draggables.append(self)
    def hide(self):
        self.visible = False
        self.wf.clickables.remove(self)
        self.wf.draggables.remove(self)
    def toggle(self):
        if self.visible:
            self.hide()
        else:
            self.show()
    def curstep(self):
        if self.step >= len(self.route):
            return None
        elif len(self.route) > 0:
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
    def sety(self, newy):
        self.y = newy
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
        if len(self.route) == 0:
            self.route = [(dest, speed)]
        else:
            self.route.append((dest, speed))
    def cancel_route(self):
        """Canceling the route will let the Pawn reach the next node
        before stopping to await a new waypoint. If you want it
        stranded between two nodes, call delroute instead."""
        self.route = [self.curstep()]
    def delroute(self):
        self.route = []

class PawnTimer:
    def __init__(self, pawns):
        self.pawns = pawns
        self.delay = 0.0

class Board:
    def __init__(self, width, height, texture, spotgraphs, pawns):
        self.width = width
        self.height = height
        self.tex = texture
        self.spotgraphs = spotgraphs
        self.pawns = pawns
    def getwidth(self):
        return self.width
    def getheight(self):
        return self.height

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
    # One window, batch, and WidgetFactory per board.
    def __init__(self, db, gamestate, boardname, window, batch):
        self.db = db
        self.board = self.db.getboard(boardname)
        self.gamestate = gamestate
        self.window = window
        self.batch = batch
        self.made = []
        self.hoverables = []
        self.clickables = []
        self.draggables = []
        self.keyboard_listeners = []
        self.delay = 0
        self.pressed = None
        self.hovered = None
        self.grabbed = None
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
    def on_draw(self):
        for widget in self.made:
            widget.addtobatch(self.batch)
    def on_key_press(self, sym, mods):
        for listener in self.keyboard_listeners:
            if sym in listener.listen_to_keys:
                if mods & listener.listen_to_mods > 0:
                    listener.keypress(sym, mods)
        # self.mouse.left = button == pyglet.window.mouse.LEFT
        # self.mouse.middle = button == pyglet.window.mouse.MIDDLE
        # self.mouse.right = button == pyglet.window.mouse.RIGHT
        # self.key.shift = modifiers & pyglet.window.key.MOD_SHIFT
        # self.key.ctrl = modifiers & pyglet.window.key.MOD_CTRL
        # self.key.meta = (modifiers & pyglet.window.key.MOD_ALT or
        #                  modifiers & pyglet.window.key.MOD_OPTION)
    def on_mouse_motion(self, x, y, dx, dy):
        for listener in self.hoverables:
            if point_is_in(x, y, listener):
                listener.set_hover()
                self.hover = listener
                return
        if self.hover is not None:
            self.hover.unset_hover()
            self.hover = None
    def on_mouse_press(self, x, y, button, modifiers):
        for listener in self.clickables:
            if button in listener.listen_to_buttons:
                if point_is_in(x, y, listener):
                    listener.set_pressed(button, mods)
                    self.pressed = listener
                    return
        for listener in self.draggables:
            if button in listener.listen_to_buttons:
                if point_is_in(x, y, listener):
                    listener.set_grabbed(button, mods)
                    self.grabbed = listener
                    return
    def on_mouse_release(self, x, y, button, modifiers):
        if self.pressed is not None:
            self.pressed.unset_pressed(button, modifiers)
            self.pressed = None
    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.grabbed is not None:
            self.grabbed.unset_grabbed(buttons, modifiers)
            self.grabbed = None
    def mkmenu(self, menuname):
        menu = self.db.getmenu(menuname)
        if menu not in self.made:
            self.made.append(menu)
        if menu.visible:
            self.hoverables.append(menu)
            self.clickables.append(menu)
    def mkpawn(self, pawnname, show=True):
        pawn = Pawn(*self.db.getpawn(pawnname))
        if pawn not in self.made:
            self.made.append(pawn)
        # I haven't really decided how I want the player to interact
        # with pawns yet.  I'm guessing they should be clickable and
        # draggable. I'm debating whether they should be hoverable as
        # well.
        if show:
            pawn.show()