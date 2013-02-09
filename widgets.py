# This file is for the controllers for the things that show up on the
# screen when you play.
import pyglet
from place import Place
from math import floor, sqrt

def point_is_in(x, y, listener):
    return x >= listener.getleft() and x <= listener.getright() \
        and y >= listener.getbot() and y <= listener.gettop()

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
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = Color.maybe_to_color(color)
        self.image = pyglet.image.create(width, height,
                                         pyglet.image.SolidColorImagePattern(color.tup))
    def gettop(self):
        return self.y + self.height
    def getbot(self):
        return self.y
    def getleft(self):
        return self.x
    def getright(self):
        return self.x + self.width
    def addtobatch(self, batch, group=None):
        self.sprite = pyglet.sprite.Sprite(self.image, self.x, self.y,
                                           batch=batch, group=group)

class MenuItem:
    def __init__(self, text, onclick, style, closer=True):
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
        return pyglet.text.Label(self.text, fontface, fontsize, color=color,
                                 x=x, y=y, batch=batch, group=group,
                                 anchor_x='left', anchor_y='bottom')
    def addtobatch(self, batch, group=None):
        if self.visible:
            if self.hovered:
                color = self.style.fg_active
            else:
                color = self.style.fg_inactive
            return pyglet.text.Label(self.text, self.style.fontface, self.style.fontsize,
                                     color=color, x=self.x, y=self.y, batch=batch,
                                     group=group)

class Menu:
    def __init__(self, name, xprop, yprop, wprop, hprop, style):
        self.name = name
        self.style = style
        if xprop < 0.0: # place lower-left corner (100*|xprop|)% from
                        # the right of the window
            self.x = self.wf.window.width + (self.wf.window.width * xprop)
        else: # place lower-left corner (100*|xprop|)% from the left of the window
            self.x = self.wf.window.width * xprop
        if yprop < 0.0:  # place lower-left corner (100*|yprop|)% from
                         # the top of the window
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
        self.rect = Rect(self.x, self.y, self.width, self.height,
                         self.style.bgcolor)
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
            return []
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
        return drawn


class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    def __init__(self, place, x, y, r, imgname, spotgraph):
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


class Pawn:
    """A token to represent something that moves about between Places.

    Pawn(wf, thing, place, x, y) => pawn

    wf is the WidgetFactory that made the Pawn. It will be displayed on the Board that wf manages.

    thing is the game-logic item that the Pawn represents. It should be of class Thing.

    place is the name of a Place that is already represented by a Spot
    in the same Board. pawn will appear here to begin with. Note that
    the Spot need not be visible. You can supply the Place name for an
    invisible spot to make it appear that a Pawn is floating in that
    nebulous dimension between Places.

    """
    # Coordinates should really be relative to the Board and not the
    # uh, canvas? is that what they are called in pyglet?
    def __init__(self, thing, img, place):
        self.thing = thing
        self.img = img
        self.place = place
        self.x = place.x
        self.y = place.y
        self.curspot = self.wf.db.getspot(place.name)
        self.visible = False
    def addtobatch(self, batch, group=None):
        return pyglet.sprite.Sprite(pawn.img, pawn.x, pawn.y, batch=self.batch, group=self.pawngroup)
            
class Board:
    def __init__(self, width, height, texture):
        self.width = width
        self.height = height
        self.tex = texture
        self.pawns = []
    def getwidth(self):
        return self.width
    def getheight(self):
        return self.height

class Style:
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

class WidgetFactory:
    # One window, batch, and WidgetFactory per board.
    def __init__(self, db, gamestate, boardname, window, batch):
        self.db = db
        self.board = self.db.getboard(boardname)
        self.gamestate = gamestate
        self.window = window
        self.batch = batch
        self.menugroup = pyglet.graphics.Group()
        self.labelgroup = pyglet.graphics.Group()
        self.pawngroup = pyglet.graphics.Group()
        self.spotgroup = pyglet.graphics.Group()
        self.menusmade = []
        self.labelsmade = []
        self.pawnsmade = []
        self.spotsmade = []
        self.hoverables = []
        self.clickables = []
        self.draggables = []
        self.keyboard_listeners = []
        self.delay = 0
        self.pressed = None
        self.hovered = None
        self.grabbed = None
    def rmlistener(self, listener):
        self.hoverables.remove(listener)
        self.clickables.remove(listener)
        self.draggables.remove(listener)
        self.keyboard_listeners.remove(listener)
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
        drawn = []
        for pawn in self.pawnsmade:
            drawn.append(pawn.addtobatch(self.batch, self.pawngroup))
        
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
    def extract_name(it, clas):
        if type(it) is str:
            return it
        elif isinstance(it, clas):
            return it.name
        else:
            raise TypeError("I need a %s or the name of one" % str(clas))
    def open_spot(self, place_or_name):
        if type(place_or_name) is str:
            s = self.db.getspot(place)
        elif isinstance(place_or_name, Place):
            s = self.db.getspot(place.name)
        else:
            raise TypeError("I need a place or the name of one.")
        self.spotsmade.append(s)
        return s
    def close_spot(self, name_or_spot):
        if type(name_or_spot) is str:
            spot = self.db.getspot(name_or_spot)
            name = name_or_spot
        elif isinstance(name_or_spot, Spot):
            spot = name_or_spot
            name = name_or_spot.place.name
        elif isinstance(name_or_spot, Place):
            spot = self.db.getspot(name_or_spot.name)
            name = name_or_spot.name
        else:
            raise TypeError("I need a name of a place, a place, or the spot that represents it")
        self.db.savespot(spot)
        del self.db.spotmap[name]
        self.rmlistener(spot)
        self.spotsmade.remove(spot)
    def open_menu(self, name):
        menu = self.db.getmenu(name)
        self.menusmade.append(menu)
        return menu
    def close_menu(self, name_or_menu):
        if type(name_or_menu) is str:
            menu = self.db.getmenu(name_or_menu)
            name = name_or_menu
        elif isinstance(name_or_menu, Menu):
            menu = name_or_menu
            name = name_or_menu.name
        else:
            raise TypeError("I need a menu's name or a menu proper")
        # saving the opened-ness of windows when 
        self.db.savemenu(menu)
        del self.db.menumap[name]
        self.rmlistener(menu)
        self.menusmade.remove(menu)
    def open_pawn(self, thing_or_name):
        if type(thing) is str:
            thingn = thing
        elif isinstance(thing, Thing):
            thingn = thing.name
        else:
            raise TypeError("I need a thing or the name of one")
        pawn = self.db.getpawn(thingn, self.board)
        self.pawnsmade.append(pawn)
        return pawn
    def close_pawn(self, thing_or_pawn_or_name):
        topor = thing_or_pawn_or_name
        if type(topor) is str:
            pawn = self.db.getpawn(topor, self.board)
            name = topor
        elif isinstance(topor, Thing):
            pawn = self.db.getpawn(topor.name, self.board)
            name = topor.name
        elif isinstance(topor, Pawn):
            pawn = topor
            name = topor.name
        else:
            raise TypeError("I need a thing, a pawn, or a name")
        self.db.savepawn(pawn)
        del self.db.pawnmap[name]
        self.rmlistener(pawn)
        self.pawnsmade.remove(pawn)
    def show_pawn(self, pawn):
        pawn.visible = True
        self.clickables.append(pawn)
        self.draggables.append(pawn)
    def hide_pawn(self, pawn):
        pawn.visible = False
        self.clickables.remove(pawn)
        self.draggables.remove(pawn)
    def toggle_pawn(self, pawn):
        if pawn.visible:
            self.hide_pawn(pawn)
        else:
            self.show_pawn(pawn)
    def show_menu_item(self, mi):
        if None in [mi.y, mi.fontsize]:
            raise Exception("I can't show the label %s without knowing"
                            " where it is, first." % mi.text)
        else:
            self.clickables.append(mi)
            mi.visible = True
    def hide_menu_item(self, mi):
        mi.visible = False
        self.clickables.remove(mi)
    def toggle_menu_item(self, mi):
        if mi.visible:
            self.hide_menu_item(mi)
        else:
            self.show_menu_item(mi)