import pyglet
from database import Database
from state import GameState


def point_is_in(x, y, listener):
    return x >= listener.getleft() and x <= listener.getright() \
        and y >= listener.getbot() and y <= listener.gettop()


def point_is_between(x, y, x1, y1, x2, y2):
    return x >= x1 and x <= x2 and y >= y1 and y <= y2


class GameWindow:
    # One window, batch, and WidgetFactory per board.
    def __init__(self, db, gamestate, boardname, batch=None):
        self.db = db
        self.db.xfunc(self.toggle_menu_visibility_by_name)
        self.gamestate = gamestate
        self.board = self.db.load_board(boardname)
        if self.board is None:
            raise Exception("No board by the name %s" % (boardname,))

        self.boardgroup = pyglet.graphics.OrderedGroup(0)
        self.edgegroup = pyglet.graphics.OrderedGroup(1)
        self.spotgroup = pyglet.graphics.OrderedGroup(2)
        self.pawngroup = pyglet.graphics.OrderedGroup(3)
        self.menugroup = pyglet.graphics.OrderedGroup(4)
        self.labelgroup = pyglet.graphics.OrderedGroup(5)

        self.pressed = None
        self.hovered = None
        self.grabbed = None
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_dx = 0
        self.mouse_dy = 0
        self.mouse_buttons = 0
        self.mouse_mods = 0
        self.view_left = 0
        self.view_bot = 0
        self.drawn = []
        self.to_mouse = []

        window = pyglet.window.Window()
        if batch is None:
            batch = pyglet.graphics.Batch()

        @window.event
        def on_draw():
            self.add_stuff_to_batch()

        @window.event
        def on_key_press(sym, mods):
            self.on_key_press(sym, mods)

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

        self.window = window
        self.batch = batch

        for menu in self.board.menus:
            menu.window = self.window

    def add_stuff_to_batch(self):
        self.window.clear()
        self.to_mouse = []
        for h in self.drawn:
            h.delete()
        self.drawn = []
        for menu in self.board.menus:
            if menu.visible:
                self.drawn.append(self.add_menu_to_batch(menu))
                for item in menu.items:
                    if item.visible:
                        self.drawn.append(self.add_menu_item_to_batch(item))
                        if item.interactive:
                            self.to_mouse.append(item)
        for pawn in self.board.pawns:
            if pawn.visible:
                self.drawn.append(self.add_pawn_to_batch(pawn))
                if pawn.interactive:
                    self.to_mouse.append(pawn)
        for spot in self.board.spots:
            if spot.visible:
                self.drawn.append(self.add_spot_to_batch(spot))
                if spot.interactive:
                    self.to_mouse.append(spot)
        self.drawn.append(self.add_board_to_batch())
        self.batch.draw()

    def toggle_menu_visibility_by_name(self, name):
        self.db.toggle_menu_visibility(self.board.dimension + '.' + name)

    def on_key_press(self, key, mods):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        if self.hovered is None:
            for moused in self.to_mouse:
                if moused is not None\
                   and moused.interactive\
                   and point_is_in(x, y, moused):
                    self.hovered = moused
                    break
        else:
            if not point_is_in(x, y, self.hovered):
                self.hovered = None

    def on_mouse_press(self, x, y, button, modifiers):
        self.hovered = None
        for moused in self.to_mouse:
            if point_is_in(x, y, moused):
                self.pressed = moused
                break

    def on_mouse_release(self, x, y, button, modifiers):
        if self.pressed is not None:
            if point_is_in(x, y, self.pressed)\
               and hasattr(self.pressed, 'onclick'):
                self.pressed.onclick(button, modifiers)
        self.pressed = None
        # I don't think it makes sense to consider it hovering if you
        # drag and drop something somewhere and then loiter. Hovering
        # is deliberate, this probably isn't

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.pressed is not None:
            if hasattr(self.pressed, 'move_with_mouse'):
                self.pressed.move_with_mouse(x, y, dx, dy, buttons, modifiers)
            elif not point_is_in(x, y, self.pressed):
                self.pressed = None

    def add_board_to_batch(self):
        x = -1 * self.view_left
        y = -1 * self.view_bot
        s = pyglet.sprite.Sprite(self.board.img, x, y,
                                 self.batch, self.boardgroup)
        return s

    def add_menu_to_batch(self, menu):
        color = menu.style.bg_inactive
        w = menu.getwidth()
        h = menu.getheight()
        pattern = pyglet.image.SolidColorImagePattern(color.tup)
        image = pattern.create_image(w, h)
        return pyglet.sprite.Sprite(image, menu.getleft(), menu.getbot(),
                                    batch=self.batch, group=self.menugroup)

    def add_menu_item_to_batch(self, mi):
        sty = mi.menu.style
        if self.hovered is mi:
            color = sty.fg_active
        else:
            color = sty.fg_inactive
        left = mi.getleft()
        bot = mi.getbot()
        return pyglet.text.Label(mi.text, sty.fontface, sty.fontsize,
                                 color=color.tup, x=left, y=bot,
                                 batch=self.batch, group=self.labelgroup)

    def add_spot_to_batch(self, spot):
        # This also adds edges representing all the portals from the
        # spot. Those edges are added to the batch directly. They
        # won't be returned.
        portals = spot.place.portals
        edge_positions = []
        for portal in portals:
            origspot = portal.orig.spot
            orig_x = origspot.x
            orig_y = origspot.y
            destspot = portal.dest.spot
            dest_x = destspot.x
            dest_y = destspot.y
            edge_positions.extend([orig_x, orig_y, dest_x, dest_y])
        mode = pyglet.graphics.GL_LINES
        self.batch.add(len(portals) * 2, mode, self.edgegroup,
                       ('v2i', edge_positions))
        return pyglet.sprite.Sprite(spot.img, spot.x - spot.r, spot.y - spot.r,
                                    batch=self.batch, group=self.spotgroup)

    def add_pawn_to_batch(self, pawn):
        # Getting the window coordinates whereupon to put the pawn
        # will not be simple.  I'll first need the two places the
        # thing stands between now; or, if it is not on a journey,
        # then just its location. That's an easy case: draw the pawn
        # on top of the spot for the location. But otherwise, I must
        # find the spots to represent the beginning and the end of the
        # portal in which the thing stands, and find the point the
        # correct proportion of the distance between them.
        if hasattr(pawn, 'journey'):
            port = pawn.thing.journey.getstep(0)
            prog = pawn.thing.progress
            whence = self.db.spotdict[port.orig.name]
            thence = self.db.spotdict[port.dest.name]
            # a line between them
            rise = thence.y - whence.y
            run = thence.x - whence.x
            # a point on the line, at prog * its length
            x = whence.x + prog * run
            y = whence.y + prog * rise
            # this may put it off the bounds of the screen
            s = pyglet.sprite.Sprite(pawn.img, x - pawn.r, y,
                                     batch=self.batch, group=self.pawngroup)
        else:
            dim = pawn.board.dimension
            locn = pawn.thing.location.name
            spot = self.db.spotdict[dim][locn]
            # Pawns are centered horizontally, but not vertically, on
            # the spot they stand.  This prevents them from covering
            # the spot overmuch while still making them look like
            # they're "on top" of the spot.
            x = spot.x
            y = spot.y
            s = pyglet.sprite.Sprite(pawn.img, x - pawn.r, y,
                                     batch=self.batch, group=self.pawngroup)
        return s


db = Database(":memory:")
db.mkschema()
db.insert_defaults()
gamestate = GameState(db)
gw = GameWindow(db, gamestate, 'Physical')


gamespeed = 1/60.0

# pyglet.clock.schedule_interval(gamestate.update, gamespeed, gamespeed)

pyglet.app.run()
