# This file is for the controllers for the things that show up on the screen when you play.
import pyglet, sys, os
sys.path.append(os.curdir)
import graphics
from place import Place
from math import floor, sqrt
from uuid import uuid4

class LabelException(Exception):
    def __init__(self, it):
        Exception.__init__(self, 'Something went wrong with the label reading "' + it.text + '"')

class MouseStruct:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.dx = 0
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
        return self.mouse.y - self.getbot()
    def is_button_pressed(self, button):
        if button is pyglet.window.mouse.LEFT:
            return self.mouse.left
        elif button is pyglet.window.mouse.MIDDLE:
            return self.mouse.middle
        elif button is pyglet.window.mouse.RIGHT:
            return self.mouse.right
        else:
            return False
    def is_mouse_in(self):
        return self.mouse.x >= self.getleft() and \
          self.mouse.x <= self.getright() and \
          self.mouse.y >= self.getbot() and \
          self.mouse.y <= self.gettop
    def is_being_clicked(self, button=pyglet.window.mouse.LEFT):
        return self.is_button_pressed(button) and \
          self.is_mouse_in()
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
        for handler in [self.on_mouse_motion, self.on_mouse_press, self.on_mouse_release, self.on_mouse_drag]:
            window.push_handlers(handler)


class Color:
    """Color(red=0, green=0, blue=0, alpha=255) => color

    This is just a container class for the (red, green, blue, alpha)
    tuples that Pyglet uses to identify colors. I like being able to
    get a particular element by name rather than number."""
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

def from_hex(h):
    if type(h) == str:
        hs = h
    else:
        hs = hex(h).replace('0x','').zfill(6)
    rh = hs[0:2]
    gh = hs[2:4]
    bh = hs[4:6]
    r = int(rh,16)
    g = int(gh,16)
    b = int(bh,16)
    return Color(r, g, b)

white = Color(255,255,255)
black = Color(0,0,0)

class ColorSet:
    pass

class SolarizedSet(ColorSet):
    base03 = from_hex(0x002b36)
    base02 = from_hex(0x073642)
    base01 = from_hex(0x586e75)
    base00 = from_hex(0x657b83)
    base0 = from_hex(0x839496)
    base1 = from_hex(0x93a1a1)
    base2 = from_hex(0xeee8d5)
    base3 = from_hex(0xfdf6e3)
    yellow = from_hex(0xb58900)
    orange = from_hex(0xcb4b16)
    red = from_hex(0xdc322f)
    magenta = from_hex(0xd33682)
    violet = from_hex(0x6c71c4)
    blue = from_hex(0x268bd2)
    cyan = from_hex(0x2aa198)
    green = from_hex(0x859900)
    bg = ColorSet()
    fg = ColorSet()
    bg.dark = base02
    bg.xdark = base03
    bg.light = base2
    bg.xlight = base3
    fg.dark = base00
    fg.xdark = base01
    fg.light = base0
    fg.xlight = base1

class SolarizedDarkSet(SolarizedSet):
    fg = ColorSet()
    bg = ColorSet()
    fg.inactive = SolarizedSet.fg.dark
    bg.inactive = SolarizedSet.bg.dark
    fg.active = SolarizedSet.fg.xdark
    bg.active = SolarizedSet.bg.xdark

class SolarizedLightSet(SolarizedSet):
    fg = ColorSet()
    bg = ColorSet()
    fg.inactive = SolarizedSet.fg.light
    bg.inactive = SolarizedSet.bg.light
    fg.active = SolarizedSet.fg.xlight
    bg.active = SolarizedSet.bg.xlight

class ColorScheme:
    def __init__(self, buttons, menus, fields, content):
        # all the args should be ColorSet class objects
        self.buttons = buttons
        self.menus = menus
        self.fields = fields
        self.content = content

solarized_dark_scheme = ColorScheme(SolarizedDarkSet, SolarizedDarkSet, SolarizedDarkSet, SolarizedDarkSet)

class Rect:
    """Rect(x, y, width, height, color, batch=None, group=None) => rect

    A rectangle with its lower-left corner at the given x and y. It
    supports only batch rendering. If you supply a batch in the
    constructor, I'll add myself to it immediately."""
    def __init__(self, x, y, width, height, color, batch=None, group=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = Color.maybe_to_color(color)
        self.image = pyglet.image.create(width, height, pyglet.image.SolidColorImagePattern(color.tuple))
        if batch is not None:
            self.addtobatch(batch, group)
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
        return self.sprite

class Button(MouseListener):
    # I'll just use simple rectangular buttons with text on, for now.
    def __init__(self, window, onclick, x, y, width, height, text, SolarizedDarkSet, fontface="Sans", fontsize=20):
        self.onclick = onclick
        self.register(window)
        self.text = text
        self.colors = colors
        self.fontface = fontface
        self.fontsize = fontsize
    def addtobatch(self, batch, buttongroup, labelgroup):
        pass
    def xcenter(self):
        return self.rect.x + (self.rect.width / 2)
    def ycenter(self):
        return self.rect.y + (self.rect.height / 2)
    def fgcolor(self):
        if self.is_being_clicked:
            return self.colors.fg.active
        else:
            return self.colors.fg.inactive
    def bgcolor(self):
        if self.is_being_clicked:
            return self.colors.bg.active
        else:
            return self.colors.bg.inactive
    def getlabel(self, batch, group):
        return pyglet.text.Label(self.text, self.fontface, self.fontsize, color=self.fgcolor(), x=self.xcenter(), y=self.ycenter(), batch=batch, group=group, anchor_x='center', anchor_y='center')
    def getrect(self, batch=None, group=None):
        return Rect(self.x, self.y, self.width, self.height, self.color, batch, group)

class MenuItem:
    def __init__(self, text, onclick=None, ct=None):
        self.active = False
        self.text = text
        self.onclick = onclick
        self.ct = ct
    def __eq__(self, other):
        if isinstance(other, MenuItem):
            return self.text == other.text
        else:
            return False
    def __gt__(self, other):
        if isinstance(other, MenuItem):
            return self.text > other.text
        else:
            return False
    def __ge__(self, other):
        if isinstance(other, MenuItem):
            return self.text >= other.text
        else:
            return False
    def __lt__(self, other):
        if isinstance(other, MenuItem):
            return self.text < other.text
        else:
            return False
    def __le__(self, other):
        if isinstance(other, MenuItem):
            return self.text <= other.text
        else:
            return False
    def __repr__(self):
        return self.text
    def __str__(self):
        return self.text
    def __hash__(self):
        return hash(self.text)
    def getlabel(self, x, y, fontface, fontsize, color=None, batch=None, group=None, width=None, height=None): # TODO: find out if the Nones here break things
        if isinstance(color, Color):
            color = color.tuple
        return pyglet.text.Label(text=self.text, font_name=fontface, font_size=fontsize, color=color, x=x, y=y, batch=batch, group=group, width=width, height=height, anchor_x='left', anchor_y='top')


class MenuList:
    # eventually this should turn into an interface class for my backend db
    def __init__(self):
        self.items = []
        self.sorted = True
        self.nmap = {}
    def __len__(self):
        return len(self.items)
    def __getitem__(self, i):
        if type(i) is int:
            return self.items[i]
        elif type(i) is str:
            return self.nmap[i]
        elif isinstance(i, MenuItem):
            # seems a mite redundant
            return i
        else:
            raise IndexError("Index %s %s is incompatible with MenuItem." % (i, type(i)) )
    def index(self, item):
        if isinstance(item, MenuItem):
            return self.items.index(item)
        elif type(item) is str:
            i = 0
            for it in self.items:
                if it.text == item:
                    return i
                i += 1
            raise ValueError(it + " is not in MenuList")
        else:
            raise TypeError("Can't look up a %s in a MenuList" % type(item))
    def append(self, mi):
        if not isinstance(mi, MenuItem):
            raise TypeError("Tried to add non-MenuItem to MenuList")
        else:
            self.items.append(mi)
    def count(self, value):
        return self.items.count(value)
    def extend(self, it):
        for item in it:
            self.append(item)
    def index(self, value):
        if not isinstance(value, MenuItem):
            if type(value) is str:
                it = self.nmap[it]
            else:
                raise TypeError("Can't lookup %s in MenuList" % type(value))
        else:
            it = value
        return self.items.index(it)
    def insert(self, i, value):
        if not isinstance(value, MenuItem):
            raise TypeError("MenuList should not contain " + value)
        else:
            self.nmap[value.text] = value
            self.items.insert(i, value)
    def pop(self, i):
        if type(i) is str:
            r = self.nmap.pop(i)
        elif type(i) is int:
            r = self.items.pop(i)
            self.nmap.pop(r.text)
        else:
            raise TypeError("This is not a valid index into a MenuList: " + i)
        return r
    def remove(self, value):
        if value not in self.items:
            return
        else:
            self.nmap.pop(value.text)
            self.items.remove(value)
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

    def add_item(self, name, onclick, ct=None):
        if name in [item.text for item in self.items]:
            return None
        else:
            to_add = MenuItem(name, onclick, ct)
            self.nmap[name] = to_add
            self.items.append(to_add)
            self.sorted = False
            return to_add
    def remove_item(self, i):
        if type(i) is int:
            del self.items[i]
        elif type(i) is str:
            del self.nmap[i]
        else:
            raise IndexError("Index type %s is incompatible with MenuItem." % type(i))


class Menu(MouseListener):
    def __init__(self, window, x, y, width, height, colorscheme, fontface, fontsize, spacing=6):
        self.active_item = None
        self.chosen_item = None
        self.visible = False
        self.nmap = {}
        self.drawn = []

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.bgcolor = Color.maybe_to_color(colorscheme.menus.bg.inactive)
        self.inactive_color = Color.maybe_to_color(colorscheme.menus.fg.inactive)
        self.active_color = Color.maybe_to_color(colorscheme.menus.fg.active)
        self.fontface = fontface
        self.fontsize = fontsize
        self.spacing = spacing

        self.items = MenuList()

        self.register(window)

    def __getitem__(self, i):
        if type(i) is int:
            return self.items[i]
        elif type(i) is str:
            return self.nmap[i]
        else:
            raise TypeError("I can't look up %s in a MenuList" % i)
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
    def getitemtop(self, item):
        assert(type(item) in [ int, str ] or isinstance(item, MenuItem))
        if type(item) is int:
            i = item
        else:
            i = self.index(item)
        return self.gettop() - i * self.fontsize - i * self.spacing
    def getitembot(self, item):
        if type(item) is int:
            i = item + 1
        else:
            i = self.index(item) + 1
        return self.gettop() - i * self.fontsize
    def getrect(self):
        return Rect(self.x, self.y, self.width, self.height, self.bgcolor)
    def index(self, item):
        return self.items.index(item)
    def on_mouse_press(self, x, y, button, modifiers):
        MouseListener.on_mouse_press(self, x, y, button, modifiers)
        if self.is_mouse_over_item(self.active_item):
            self.chosen_item = self.active_item
    def on_mouse_release(self, x, y, button, modifiers):
        MouseListener.on_mouse_release(self, x, y, button, modifiers)
        if self.active_item is not None and self.chosen_item is not None:
            if self.active_item == self.chosen_item:
                self.active_item.onclick()
    def add_item(self, name, onclick, number=None):
        added = self.items.add_item(name, onclick, number)
        self.nmap[name] = added
    def remove_item(self, name):
        self.items.remove_item(name)
    def is_mouse_over_item(self, item):
        if item is None:
            return False
        elif not self.is_mouse_in():
            return False
        elif self.mouse.y > self.getitemtop(item):
            return False
        elif self.mouse.y < self.getitembot(item):
            return False
        else:
            return True
    def addtobatch(self, batch, menugroup, labelgroup):
        if self.visible:
            self.drawn.append(self.getrect().addtobatch(batch, menugroup))
            for item in self.items:
                if self.is_mouse_over_item(item):
                    self.active_item = item
                    color = self.active_color
                else:
                    color = self.inactive_color
                drawable = item.getlabel(self.getleft(), self.getitembot(item), self.fontface, self.fontsize, color, batch, labelgroup)
                self.drawn.append(drawable)
            return self.drawn
        else:
            for graphic in self.drawn:
                    graphic.delete()
            self.drawn = []

class MenuBar(Menu):
    # Appears at the top of the window. Offers stuff you can mouseover
    # to get the various menus; icons you can click to get to other
    # screens.
    #
    # Wouldn't it be better to use wxwindows for this? Eh, one more
    # library I gotta learn...
    def __init__(self, window, height, colorscheme, fontface, fontsize, spacing=6, gutter=6):
        self.active_item = None
        self.chosen_item = None
        self.lastmenu = None
        self.visible = True
        self.menu_open = False
        self.nmap = {}

        self.window = window
        self.height = height
        self.colorscheme = colorscheme
        self.bgcolor = colorscheme.menus.bg.inactive
        self.inactive_color = colorscheme.menus.fg.inactive
        self.active_color = colorscheme.menus.fg.active
        self.fontface = fontface
        self.fontsize = fontsize
        self.spacing = spacing
        self.gutter = gutter
        self.items = []
        self.x = 0
        self.y = self.window.height - self.height
        self.lastright = 0
        self.register(window)
        # Not setting self.width because that'll vary with the window size.
    def __getitem__(self, i):
        if type(i) is int:
            return self.items[i]
        elif type(i) is str:
            return self.nmap[i]
        else:
            raise TypeError("MenuBar can't lookup key " + i + " of " + type(i))
    def getleft(self):
        return self.x
    def getright(self):
        return self.window.width
    def getbot(self):
        return self.y
    def gettop(self):
        return self.window.height
    def getwidth(self):
        return self.window.width
    def getheight(self):
        return self.height
    def getrect(self, batch=None, group=None):
        return Rect(self.x, self.y, self.window.width, self.height, self.bgcolor, batch, group)
    def add_item(self, text, menu):
        # Menu bars hold menus. When the user clicks the text, a menu
        # will appear thence.
        # I'll need a function bywhichto call the menu.
        def tog():
            if not self.menu_open:
                menu.visible = True
                self.lastmenu = menu
                self.menu_open = True
            else:
                self.lastmenu.visible = False
                self.menu_open = False
        menu.left = self.lastright + self.spacing
        menu.right = menu.left + self.fontsize * len(text)
        menu.text = text
        self.items.append(menu)
        self.lastright = menu.right
        self.nmap[text] = menu
    def add_menu(self, text):
        # Add an empty menu with the given name.
        #
        # The new menu should be left justified with its name on the menu bar.
        # If I can't verify that there's enough room on the menu bar...no dice.
        # Let's say menus are 300px tall and 100px wide.
        numenu = Menu(self.window, self.lastright, self.y - 300, 100, 300, self.colorscheme, self.fontface, self.fontsize, self.spacing)
        self.add_item(text, numenu)
    def add_menu_item(self, menu, text, onclick):
        if not isinstance(menu, Menu):
            menu = self[menu] # may raise TypeError
        mi = MenuItem(text, onclick)
        menu.add_item(mi)
    def remove_item(self, name):
        if type(name) in [ int, str ]:
            it = self[name]
        elif not isinstance(name, Menu):
            raise TypeError("Bad index for MenuBar: " + repr(name) + " | " + type(name))
        else:
            it = name
        width = it.right - it.left
        j = i + 1
        while j < len(self.items):
            item = self.items[j]
            item.left -= width
            item.right -= width
            j += 1
        self.items.remove_item(it)
    def is_mouse_over_item(self, item):
        if type(item) is type(1):
            item = self.items[item]
        elif None in [item.left, item.right]:
            return False
        elif self.mouse.y < self.y:
            return False
        else:
            return item.left <= self.mouse.x <= item.right
    def addtobatch(self, batch, menugroup, labelgroup):
        if not self.visible:
            return
        drawn = []
        drawn.append(self.getrect(batch, menugroup))
        for item in self.items:
            if self.is_mouse_in():
                if self.is_mouse_over_item(item):
                    self.active_item = item
                    color = self.active_color
                else:
                    color = self.inactive_color
            else:
                self.active_item = None
                color = self.inactive_color
            if self.menu_open:
                if self.chosen_item is item:
                    item.addtobatch(batch, menugroup, labelgroup)
            drawn.append(pyglet.text.Label(text=item.text, x=item.left, y=self.y + self.gutter, font_name=self.fontface, font_size=self.fontsize, color=color.tuple, batch=batch, group=labelgroup))
        return drawn
    def on_mouse_press(self, x, y, button, modifiers):
        MouseListener.on_mouse_press(self, x, y, button, modifiers)
        self.chosen_item = self.active_item
    def on_mouse_release(self, x, y, button, modifiers):
        MouseListener.on_mouse_release(self, x, y, button, modifiers)
        if self.is_mouse_in():
            if self.chosen_item is not None:
                if self.active_item is not None:
                    if self.chosen_item == self.active_item:
                        self.chosen_item.visible = not self.chosen_item.visible
                        self.chosen_item = None
                        self.active_item = None
        else:
            if self.menu_open:
                self.lastmenu.visible = False
                self.menu_open = False

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
        self.img = graphics.image('orb.png')
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
    def __init__(self, name=None, places={}, spots=[], edges=[]):
        if name is None:
            self.name = str(uuid4())
        else:
            self.name = name
        self.places = places
        self.spots = spots
        self.edges = edges
        self.edges_to_draw = []
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
    def __init__(self, start, spotgraph, img):
        self.spotgraph = spotgraph
        if isinstance(start, Spot):
            self.curspot = start
            self.x = start.x
            self.y = start.y
        elif isinstance(start, Place):
            self.curspot = self.spotgraph.places[start]
            self.x = self.curspot.x
            self.y = self.curspot.y
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


class WidgetFactory:
    # I only want my widgets to load the necessary graphics once.
    # To that effect, I will load all of them through the widget factory.
    # The widget factory will load images once, and thereafter supply them to
    # every widget it creates.
    pass
