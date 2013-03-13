# This file is for the controllers for the things that show up on the
# screen when you play.
import pyglet


class Color:
    """Color(red=0, green=0, blue=0, alpha=255) => color

    This is just a container class for the (red, green, blue, alpha)
    tuples that Pyglet uses to identify colors. I like being able to
    get a particular element by name rather than number.

    """
    table_schema = ("CREATE TABLE color "
                    "(name text primary key, "
                    "red integer not null "
                    "check(red between 0 and 255), "
                    "green integer not null "
                    "check(green between 0 and 255), "
                    "blue integer not null "
                    "check(blue between 0 and 255), "
                    "alpha integer default 255 "
                    "check(alpha between 0 and 255));")

    def __init__(self, name, r=0, g=0, b=0, a=255):
        self.name = name
        self.red = r
        self.green = g
        self.blue = b
        self.alpha = a
        self.tup = (r, g, b, a)
        self.pattern = pyglet.image.SolidColorImagePattern(self.tup)


class MenuItem:
    table_schema = ("CREATE TABLE menuitem (menu text, idx integer, "
                    "text text, onclick text, onclick_arg text, "
                    "closer boolean, visible boolean, interactive boolean, "
                    "foreign key(menu) references menu(name), "
                    "primary key(menu, idx));")

    def __init__(self, board, menu, idx, text, onclick, onclick_arg,
                 closer=True, visible=False, interactive=True):
        self.board = board
        self.menu = menu
        self.idx = idx
        self.text = text
        self.onclick_core = onclick
        self.onclick_arg = onclick_arg
        self.closer = closer
        self.visible = visible
        self.interactive = interactive
        self.height = menu.style.fontsize + menu.style.spacing
        self.hovered = False

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

    def __str__(self):
        return self.text

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
                        (self.idx * self.height))
        return self.top

    def getbot(self):
        if not hasattr(self, 'bot'):
            self.bot = self.gettop() - self.menu.style.fontsize
        return self.bot

    def onclick(self, button, modifiers):
        self.onclick_core(self.onclick_arg)

    def toggle_visibility(self):
        self.visible = not self.visible
        for item in self.items:
            item.toggle_visibility()


class Menu:
    table_schema = ("CREATE TABLE menu "
                    "(name text primary key, "
                    "x float not null, "
                    "y float not null, "
                    "width float not null, "
                    "height float not null, "
                    "style text default 'Default', "
                    "visible boolean default 0, "
                    "interactive boolean default 1, "
                    "foreign key(style) references style(name));")

    def __init__(self, board, name,
                 left, bottom, top, right, style, visible):
        self.board = board
        self.name = name
        self.left = left
        self.bottom = bottom
        self.top = top
        self.right = right
        self.style = style
        self.items = []
        self._scrolled_to = 0
        self.visible = visible
        self.interactive = True
        self.hovered = False
        # In order to actually draw these things you need to give them
        # an attribute called window, and it should be a window of the
        # pyglet kind. It isn't in the constructor because that would
        # make loading inconvenient.

    def __getitem__(self, i):
        return self.items.__getitem__(i)

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
    table_schema = ("CREATE TABLE spot "
                    "(dimension, place, img, x, y, "
                    "visible boolean, interactive boolean, "
                    "foreign key(dimension, place) "
                    "references place(dimension, name), "
                    "foreign key(img) references img(name), "
                    "primary key(dimension, place));")

    def __init__(self, dimension, place, img, x, y, visible, interactive):
        self.place = place
        self.x = x
        self.y = y
        self.img = img
        self.visible = visible
        self.interactive = interactive

    def __str__(self):
        coords = "(%i,%i)" % (self.x, self.y)
        return "Spot at " + coords + " representing " + str(self.place)

    def __repr__(self):
        return "spot(%i,%i)->%s" % (self.x, self.y, str(self.place))

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

    def is_visible(self):
        return self.visible

    def is_interactive(self):
        return self.interactive

    def onclick(self, button, modifiers):
        pass


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
    table_schema = ("CREATE TABLE pawn "
                    "(dimension, thing, img, visible, interactive, "
                    "foreign key(img) references img(name), "
                    "foreign key(dimension, thing) "
                    "references thing(dimension, name), "
                    "primary key(dimension, thing));")

    def __init__(self, board, thing, img, visible, interactive):
        self.board = board
        self.thing = thing
        self.img = img
        self.visible = visible
        self.interactive = interactive
        self.hovered = False

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
    table_schema = ("CREATE TABLE board "
                    "(dimension primary key, "
                    "width integer, "
                    "height integer, "
                    "wallpaper, "
                    "foreign key(dimension) references dimension(name), "
                    "foreign key(wallpaper) references image(name));")

    def __init__(self, dimension, width, height, image,
                 spots=[], pawns=[], menus=[]):
        self.dimension = dimension
        self.width = width
        self.height = height
        self.img = image
        self.spots = spots
        self.pawns = pawns
        self.menus = menus

    def getwidth(self):
        return self.width

    def getheight(self):
        return self.height

    def getmap(self):
        return self.mapobj

    def __str__(self):
        return "A board, %d pixels wide by %d tall, representing the "\
            "dimension %s, containing %d spots, %d pawns, and %d menus."\
            % (self.width, self.height, self.dimension, len(self.spots),
               len(self.pawns), len(self.menus))


class Style:
    table_schema = ("CREATE TABLE style "
                    "(name text primary key, "
                    "fontface text not null, "
                    "fontsize integer not null, "
                    "spacing integer default 6, "
                    "bg_inactive text not null, "
                    "bg_active text not null, "
                    "fg_inactive text not null, "
                    "fg_active text not null, "
                    "foreign key(bg_inactive) references color(name), "
                    "foreign key(bg_active) references color(name), "
                    "foreign key(fg_inactive) references color(name), "
                    "foreign key(fg_active) references color(name));")

    def __init__(self, name, fontface, fontsize, spacing,
                 bg_inactive, bg_active, fg_inactive, fg_active):
        self.name = name
        self.fontface = fontface
        self.fontsize = fontsize
        self.spacing = spacing
        self.bg_inactive = bg_inactive
        self.bg_active = bg_active
        self.fg_inactive = fg_inactive
        self.fg_active = fg_active


classes = [Color, MenuItem, Menu, Spot, Pawn, Board, Style]
table_schemata = [clas.table_schema for clas in classes]
