# This file is for the controllers for the things that show up on the
# screen when you play.
import pyglet
from uuid import uuid1 as uuid


class Color:
    """Color(red=0, green=0, blue=0, alpha=255) => color

    This is just a container class for the (red, green, blue, alpha)
    tuples that Pyglet uses to identify colors. I like being able to
    get a particular element by name rather than number.

    """
    tabname = "color"
    keydecldict = {'name': 'text'}
    valdecldict = {'red': 'integer not null '
                   'check(red between 0 and 255)',
                   'green': 'integer not null '
                   'check(green between 0 and 255)',
                   'blue': 'integer not null '
                   'check(blue between 0 and 255)',
                   'alpha': 'integer default 255 '
                   'check(alpha between 0 and 255)'}

    def __init__(self, db, rowdict):
        self.name = rowdict["name"]
        self.red = rowdict["red"]
        self.green = rowdict["green"]
        self.blue = rowdict["blue"]
        self.alpha = rowdict["alpha"]
        self.tup = (self.red, self.green, self.blue, self.alpha)
        self.pattern = pyglet.image.SolidColorImagePattern(self.tup)

    def __iter__(self):
        return iter(self.tup)

    def __str__(self):
        return "(" + ", ".join(self.tup) + ")"


class MenuItem:
    tabname = "menuitem"
    keydecldict = {'menu': 'text',
                   'idx': 'integer'}
    valdecldict = {'text': 'text',
                   'onclick': 'text',
                   'onclick_arg': 'text',
                   'closer': 'boolean',
                   'visible': 'boolean',
                   'interactive': 'boolean'}
    fkeydict = {"menu": ("menu", "name")}

    def __init__(self, db, board, rowdict):
        self.menu = db.boardmenudict[board][rowdict["menu"]]
        self.idx = rowdict["idx"]
        self.text = rowdict["text"]
        self.onclick_core = db.func[rowdict["onclick"]]
        self.onclick_arg = rowdict["onclick_arg"]
        self.closer = rowdict["closer"]
        self.visible = rowdict["visible"]
        self.interactive = rowdict["interactive"]

    def __iter__(self):
        return (self.menu.name, self.idx,
                self.text, self.onclick_core.__name__,
                self.onclick_arg, self.closer,
                self.visible, self.interactive)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.text == other
        else:
            return self.text == other.text

    def __gt__(self, other):
        if isinstance(other, str):
            return self.text > other
        return self.text > other.text

    def __ge__(self, other):
        if isinstance(other, str):
            return self.text >= other
        return self.text >= other.text

    def __lt__(self, other):
        if isinstance(other, str):
            return self.text < other
        return self.text < other.text

    def __le__(self, other):
        if isinstance(other, str):
            return self.text <= other
        return self.text <= other.text

    def __repr__(self):
        return self.text

    def __hash__(self):
        return hash(self.menu.board.dimension + self.menu.name + str(self.idx))

    def getcenter(self):
        width = self.getwidth()
        height = self.getheight()
        rx = width / 2
        ry = height / 2
        x = self.getleft()
        y = self.getbot()
        return (x + rx, y + ry)

    def getleft(self):
        if not hasattr(self, 'left'):
            self.left = self.menu.getleft() + self.menu.style.spacing
        return self.left

    def getright(self):
        if not hasattr(self, 'right'):
            self.right = self.menu.getright() - self.menu.style.spacing
        return self.right

    def gettop(self):
        if not hasattr(self, 'top'):
            self.top = (self.menu.gettop() - self.menu.style.spacing -
                        (self.idx * self.getheight()))
        return self.top

    def getbot(self):
        if not hasattr(self, 'bot'):
            self.bot = self.gettop() - self.menu.style.fontsize
        return self.bot

    def getwidth(self):
        if not hasattr(self, 'width'):
            self.width = self.getright() - self.getleft()
        return self.width

    def getheight(self):
        if not hasattr(self, 'height'):
            self.height = self.menu.style.fontsize + self.menu.style.spacing
        return self.height

    def onclick(self, button, modifiers):
        return self.onclick_core(self.onclick_arg)

    def toggle_visibility(self):
        self.visible = not self.visible
        for item in self.items:
            item.toggle_visibility()


class Menu:
    tabname = "menu"
    keydecldict = {'name': 'text'}
    valdecldict = {'left': 'float not null',
                   'bottom': 'float not null',
                   'top': 'float not null',
                   'right': 'float not null',
                   'style': "text default 'Default'",
                   "visible": "boolean default 0"}
    interactive = True

    def __init__(self, db, rowdict):
        self.name = rowdict["name"]
        self.left = rowdict["left"]
        self.bottom = rowdict["bottom"]
        self.top = rowdict["top"]
        self.right = rowdict["right"]
        self.style = db.styledict[rowdict["style"]]
        self.visible = rowdict["visible"]
        self.items = []
        self._scrolled_to = 0

        # In order to actually draw these things you need to give them
        # an attribute called window, and it should be a window of the
        # pyglet kind. It isn't in the constructor because that would
        # make loading inconvenient.

    def __iter__(self):
        return (self.name, self.left, self.bottom, self.top,
                self.right, self.style.name, self.visible)

    def __getitem__(self, i):
        return self.items[i]

    def __setitem__(self, i, to):
        self.items[i] = to

    def __delitem__(self, i):
        return self.items.__delitem__(i)

    def getstyle(self):
        return self.style

    def getleft(self):
        return int(self.left * self.window.width)

    def getbot(self):
        return int(self.bottom * self.window.height)

    def gettop(self):
        return int(self.top * self.window.height)

    def getright(self):
        return int(self.right * self.window.width)

    def getwidth(self):
        return int((self.right - self.left) * self.window.width)

    def getheight(self):
        return int((self.top - self.bottom) * self.window.height)

    def is_visible(self):
        return self.visible

    def is_interactive(self):
        return self.interactive

    def toggle_visibility(self):
        self.visible = not self.visible


class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    tabname = "spot"
    keydecldict = {"dimension": "text",
                   "place": "text"}
    valdecldict = {"img": "text",
                   "x": "integer",
                   "y": "integer",
                   "visible": "boolean",
                   "interactive": "boolean"}
    fkeydict = {"dimension, place": ("place", "dimension, name"),
                "img": ("img", "name")}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.place = db.placedict[self.dimension][rowdict["place"]]
        self.x = rowdict["x"]
        self.y = rowdict["y"]
        self.img = db.imgdict[rowdict["img"]]
        self.visible = rowdict["visible"]
        self.interactive = rowdict["interactive"]
        self.r = self.img.width / 2
        self.grabpoint = None
        self.uuid = uuid()

    def __repr__(self):
        return "spot(%i,%i)->%s" % (self.x, self.y, str(self.place))

    def __hash__(self):
        return int(self.uuid)

    def getleft(self):
        return self.x - self.r

    def getbot(self):
        return self.y - self.r

    def gettop(self):
        return self.y + self.r

    def getright(self):
        return self.x + self.r

    def getcenter(self):
        return (self.x, self.y)

    def gettup(self):
        return (self.img, self.getleft(), self.getbot())

    def is_visible(self):
        return self.visible

    def is_interactive(self):
        return self.interactive

    def onclick(self, button, modifiers):
        pass

    def dropped(self, x, y, button, modifiers):
        self.grabpoint = None

    def move_with_mouse(self, x, y, dx, dy, buttons, modifiers):
        if self.grabpoint is None:
            self.grabpoint = (x - self.x, y - self.y)
        (grabx, graby) = self.grabpoint
        self.x = x - grabx + dx
        self.y = y - graby + dy


class Pawn:
    """A token to represent something that moves about between Places.

    Pawn(thing, place, x, y) => pawn

    thing is the game-logic item that the Pawn represents.
    It should be of class Thing.

    place is the name of a Place that is already represented by a Spot
    in the same Board. pawn will appear here to begin with. Note that
    the Spot need not be visible. You can supply the Place name for an
    invisible spot to make it appear that a Pawn is floating in that
    nebulous dimension between Places.

    """
    tabname = "pawn"
    keydecldict = {"dimension": "text",
                   "thing": "text"}
    valdecldict = {"img": "text",
                   "visible": "boolean",
                   "interactive": "boolean"}
    fkeydict = {"img": ("img", "name"),
                "dimension, thing": ("thing", "dimension, name")}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.thing = db.thingdict[self.dimension][rowdict["thing"]]
        self.img = db.imgdict[rowdict["img"]]
        self.visible = rowdict["visible"]
        self.interactive = rowdict["interactive"]
        self.r = self.img.width / 2

    def __iter__(self):
        return [
            ("dimension", self.dimension),
            ("name", self.thing.name),
            ("img", self.img.name),
            ("visible", self.visible),
            ("interactive", self.interactive)]

    def getcoords(self):
        # Assume I've been provided a spotdict. Use it to get the
        # spot's x and y, as well as that of the spot for the next
        # step on my thing's journey. If my thing doesn't have a
        # journey, return the coords of the spot. If it does, return a
        # point between the start and end spots in proportion to the
        # journey's progress. If there is no end spot, behave as if
        # there's no journey.
        #
        # I can't assume that img is an actual image because the
        # loader instantiates things before assigning them data that's
        # not strings or numbers. Calculate self.rx to save some
        # division.
        if not hasattr(self, 'rx'):
            self.rx = self.img.width / 2
        if not hasattr(self, 'ry'):
            self.ry = self.img.height / 2
        if hasattr(self.thing, 'journey') and\
           self.thing.journey.stepsleft() > 0:
            j = self.thing.journey
            port = j.getstep(0)
            start = port.orig.spot
            end = port.dest.spot
            hdist = end.x - start.x
            vdist = end.y - start.y
            p = j.progress
            x = start.x + hdist * p
            y = start.y + vdist * p
            return (x, y)
        else:
            ls = self.thing.location.spot
            return (ls.x, ls.y)

    def getcenter(self):
        (x, y) = self.getcoords()
        return (x, y + self.ry)

    def getleft(self):
        return self.getcoords()[0] - self.rx

    def getright(self):
        return self.getcoords()[0] + self.rx

    def gettop(self):
        return self.getcoords()[1] + self.img.height

    def getbot(self):
        return self.getcoords()[1]

    def is_visible(self):
        return self.visible

    def is_interactive(self):
        return self.interactive

    def onclick(self, button, modifiers):
        pass


class Board:
    tabname = "board"
    keydecldict = {"dimension": "text"}
    valdecldict = {"width": "integer",
                   "height": "integer",
                   "wallpaper": "text"}
    fkeydict = {"dimension": ("dimension", "name"),
                "wallpaper": ("image", "name")}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.width = rowdict["width"]
        self.height = rowdict["height"]
        self.img = db.imgdict[rowdict["wallpaper"]]
        self.spots = db.spotdict[self.dimension].viewvalues()
        self.pawns = db.pawndict[self.dimension].viewvalues()
        self.menus = db.boardmenudict[self.dimension].viewvalues()

    def getwidth(self):
        return self.width

    def getheight(self):
        return self.height

    def __repr__(self):
        return "A board, %d pixels wide by %d tall, representing the "\
            "dimension %s, containing %d spots, %d pawns, and %d menus."\
            % (self.width, self.height, self.dimension, len(self.spots),
               len(self.pawns), len(self.menus))


class Style:
    tabname = "style"
    keydecldict = {"name": "text"}
    valdecldict = {"fontface": "text not null",
                   "fontsize": "integer not null",
                   "spacing": "integer default 6",
                   "bg_inactive": "text not null",
                   "bg_active": "text not null",
                   "fg_inactive": "text not null",
                   "fg_active": "text not null"}
    fkeydict = {"bg_inactive": ("color", "name"),
                "bg_active": ("color", "name"),
                "fg_inactive": ("color", "name"),
                "fg_active": ("color", "name")}

    def __init__(self, db, rowdict):
        self.name = rowdict["name"]
        self.fontface = rowdict["fontface"]
        self.fontsize = rowdict["fontsize"]
        self.spacing = rowdict["spacing"]
        self.bg_inactive = db.colordict[rowdict["bg_inactive"]]
        self.bg_active = db.colordict[rowdict["bg_active"]]
        self.fg_inactive = db.colordict[rowdict["fg_inactive"]]
        self.fg_active = db.colordict[rowdict["fg_active"]]
        self.tup = (self.name, self.fontface, self.fontsize, self.spacing,
                    self.bg_inactive.name, self.bg_active.name,
                    self.fg_inactive.name, self.fg_active.name)
