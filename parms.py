# TODO: give a board to every pawn and spot TODO: redo
# pawn.waypoint(...) so it looks in the database for a spot to go to
# TODO: remove references to spotgraph from spot and rewrite
# appropriately
# TODO: some way of distinguishing between routes on
# different game boards that doesn't rely on the Board class, since
# that is a widget and not a game logic thing
from widgets import table_schemata as widget_schemata
from graph import table_schemata as graph_schemata
from thing import table_schemata as thing_schemata
from character import table_schemata as char_schemata

tables = (thing_schemata +
          graph_schemata +
          widget_schemata +
          char_schemata +
          ["CREATE TABLE item "
           "(dimension, name text, "
           "foreign key(dimension) references dimension(name));",
           "CREATE TABLE location "
           "(dimension, thing, place, "
           "foreign key(dimension, thing) references thing(dimension, name), "
           "foreign key(dimension, place) references place(dimension, name), "
           "primary key(dimension, thing));",
           "CREATE TABLE containment "
           "(dimension, contained, container, "
           "foreign key(dimension, contained) "
           "references thing(dimension, name), "
           "foreign key(dimension, container) "
           "references thing(dimension, name), "
           "primary key(dimension, contained));",
           "CREATE TABLE img "
           "(name text primary key, path, rltile);",
           "CREATE TABLE boardmenu "
           "(board text, menu text, "
           "foreign key(board) references board(dimension), "
           "foreign key(menu) references menu(name));"])


def start_new_map(nope):
    pass


def open_map(nope):
    pass


def save_map(nope):
    pass


def quit_map_editor(nope):
    pass


def editor_select(nope):
    pass


def editor_copy(nope):
    pass


def editor_paste(nope):
    pass


def editor_delete(nope):
    pass


def new_place(place_type):
    pass


def new_thing(thing_type):
    pass


funcs = [start_new_map, open_map, save_map, quit_map_editor, editor_select,
         editor_copy, editor_paste, editor_delete, new_place, new_thing]


game_menu_items = {'New': ('start_new_map', None),
                   'Open': ('open_map', None),
                   'Save': ('save_map', None),
                   'Quit': ('quit_map_editor', None)}
editor_menu_items = {'Select': ('editor_select', None),
                     'Copy': ('editor_copy', None),
                     'Paste': ('editor_paste', None),
                     'Delete': ('editor_delete', None)}
place_menu_items = {'Custom Place': ('new_place', 'custom'),
                    'Workplace': ('new_place', 'workplace'),
                    'Commons': ('new_place', 'commons'),
                    'Lair': ('new_place', 'lair')}
thing_menu_items = {'Custom Thing': ('new_thing', 'custom'),
                    'Decoration': ('new_thing', 'decoration'),
                    'Clothing': ('new_thing', 'clothing'),
                    'Tool': ('new_thing', 'tool')}
main_menu_items = {'Game': ('toggle_menu_visibility_by_name', 'Game'),
                   'Editor': ('toggle_menu_visibility_by_name', 'Editor'),
                   'Place': ('toggle_menu_visibility_by_name', 'Place'),
                   'Thing': ('toggle_menu_visibility_by_name', 'Thing')}


solarized_colors = {'base03': (0x00, 0x2b, 0x36),
                    'base02': (0x07, 0x36, 0x42),
                    'base01': (0x58, 0x6e, 0x75),
                    'base00': (0x65, 0x7b, 0x83),
                    'base0': (0x83, 0x94, 0x96),
                    'base1': (0x93, 0xa1, 0xa1),
                    'base2': (0xee, 0xe8, 0xd5),
                    'base3': (0xfd, 0xf6, 0xe3),
                    'yellow': (0xb5, 0x89, 0x00),
                    'orange': (0xcb, 0x4b, 0x16),
                    'red': (0xdc, 0x32, 0x2f),
                    'magenta': (0xd3, 0x36, 0x82),
                    'violet': (0x6c, 0x71, 0xc4),
                    'blue': (0x26, 0x8b, 0xd2),
                    'cyan': (0x2a, 0xa1, 0x98),
                    'green': (0x85, 0x99, 0x00)}


placenames = ['myroom',
              'guestroom',
              'mybathroom',
              'diningoffice',
              'kitchen',
              'livingroom',
              'longhall',
              'momsbathroom',
              'momsroom',
              'outside']


atts = [('life', 'bool'),
        ('bulk', 'int', [], 0),
        ('grams', 'float', [], 0.0),
        ('stickiness', 'int', [], -10, 10),
        ('grade level', 'int',
         ['Preschool', 'Kindergarten', 'Post-secondary'],
         1, 12)]


def reciprocate(porttup):
    return (porttup[1], porttup[0])


def reciprocate_all(porttups):
    return [reciprocate(port) for port in porttups]


def reciprocal_pairs(pairs):
    return pairs + [reciprocate(pair) for pair in pairs]


class DefaultParameters:
    def addstub(self, stub):
        exec('def %s():\n\tpass\n\nself.stubs["%s"]=%s' % (stub, stub, stub))

    def __init__(self):
        self.dimensions = [{"name": "Physical"}]
        self.tables = tables
        self.funcs = funcs
        # I'm going to have the menu bar on the left of the
        # screen. For convenience.
        gamemenu = {'name': 'Game',
                    'left': 0.1,
                    'bottom': 0.3,
                    'top': 1.0,
                    'right': 0.2,
                    'style': 'Small',
                    'visible': False}
        editormenu = {'name': 'Editor',
                      'left': 0.1,
                      'bottom': 0.3,
                      'top': 1.0,
                      'right': 0.2,
                      'style': 'Small',
                      'visible': False}
        placemenu = {'name': 'Place',
                     'left': 0.1,
                     'bottom': 0.3,
                     'top': 1.0,
                     'right': 0.2,
                     'style': 'Small',
                     'visible': False}
        thingmenu = {'name': 'Thing',
                     'left': 0.1,
                     'bottom': 0.3,
                     'top': 1.0,
                     'right': 0.2,
                     'style': 'Small',
                     'visible': False}
        mainmenu = {'name': 'Main',
                    'left': 0.0,
                    'bottom': 0.0,
                    'top': 1.0,
                    'right': 0.12,
                    'style': 'Big',
                    'visible': True}
        self.menus = [gamemenu, editormenu, placemenu, thingmenu, mainmenu]
        menunames = [menud["name"] for menud in self.menus]

        def mkmenuitemd(menu, idx, text, onclick, onclick_arg,
                        closer, visible, interactive):
            return {'menu': menu,
                    'idx': idx,
                    'text': text,
                    'onclick': onclick,
                    'onclick_arg': onclick_arg,
                    'closer': closer,
                    'visible': visible,
                    'interactive': interactive}
        self.menuitems = []
        i = 0
        for item in game_menu_items.iteritems():
            self.menuitems.append(
                mkmenuitemd('Game', i,
                            item[0], item[1][0], item[1][1],
                            True, True, True))
            i += 1
        i = 0
        for item in editor_menu_items.iteritems():
            self.menuitems.append(
                mkmenuitemd('Editor', i, item[0],
                            item[1][0], item[1][1],
                            True, True, True))
            i += 1
        i = 0
        for item in place_menu_items.iteritems():
            self.menuitems.append(
                mkmenuitemd('Place', i,
                            item[0], item[1][0], item[1][1],
                            True, True, True))
            i += 1
        i = 0
        for item in thing_menu_items.iteritems():
            self.menuitems.append(
                mkmenuitemd('Thing', i,
                            item[0], item[1][0], item[1][1],
                            True, True, True))
            i += 1
        i = 0
        for item in main_menu_items.iteritems():
            self.menuitems.append(
                mkmenuitemd('Main', i,
                            item[0], item[1][0], item[1][1],
                            False, True, True))
            i += 1

        def mkcolord(name, red, green, blue, alpha):
            return {'name': name,
                    'red': red,
                    'green': green,
                    'blue': blue,
                    'alpha': alpha}

        def mkstyled(name, fontface, fontsize, spacing,
                     bg_inactive, bg_active,
                     fg_inactive, fg_active):
            return {'name': name,
                    'fontface': fontface,
                    'fontsize': fontsize,
                    'spacing': spacing,
                    'bg_inactive': bg_inactive,
                    'bg_active': bg_active,
                    'fg_inactive': fg_inactive,
                    'fg_active': fg_active}

        self.colors = [
            mkcolord(
                'solarized-' + color[0],
                color[1][0], color[1][1],
                color[1][2], 255)
            for color in solarized_colors.iteritems()]
        self.styles = [
            mkstyled(
                'Big',
                'DejaVu Sans', 16, 6,
                'solarized-base03',
                'solarized-base2',
                'solarized-base1',
                'solarized-base01'),
            mkstyled(
                'Small',
                'DejaVu Sans', 12, 3,
                'solarized-base03',
                'solarized-base2',
                'solarized-base1',
                'solarized-base01')]

        def mkitemd(dimension, name):
            return {'dimension': dimension,
                    'name': name}

        self.places = [mkitemd('Physical', p) for p in placenames]
        rpos = [('myroom', 'guestroom'),
                ('myroom', 'mybathroom'),
                ('myroom', 'outside'),
                ('myroom', 'diningoffice'),
                ('myroom', 'livingroom'),
                ('guestroom', 'diningoffice'),
                ('guestroom', 'livingroom'),
                ('guestroom', 'mybathroom'),
                ('livingroom', 'diningoffice'),
                ('diningoffice', 'kitchen'),
                ('livingroom', 'longhall'),
                ('longhall', 'momsbathroom'),
                ('longhall', 'momsroom')]
        nrpos = [('guestroom', 'outside'),
                 ('diningoffice', 'outside'),
                 ('momsroom', 'outside')]
        pos = reciprocal_pairs(rpos) + nrpos

        def mkportald(dimension, orig, dest):
            return {'dimension': dimension,
                    'name': "portal[%s->%s]" % (orig, dest),
                    'from_place': orig,
                    'to_place': dest}

        self.portals = [mkportald('Physical', po[0], po[1]) for po in pos]
        ths = [('me', 'myroom'),
               ('diningtable', 'diningoffice'),
               ('mydesk', 'myroom'),
               ('mybed', 'myroom'),
               ('bustedchair', 'myroom'),
               ('sofas', 'livingroom'),
               ('fridge', 'kitchen'),
               ('momsbed', 'momsroom'),
               ('mom', 'momsroom')]
        self.things = [mkitemd('Physical', th[0]) for th in ths]

        def mklocd(dimension, thing, place):
            return {'dimension': dimension,
                    'thing': thing,
                    'place': place}

        self.locations = [mklocd('Physical', th[0], th[1]) for th in ths]
        mjos = ["portal[momsroom->longhall]",
                "portal[longhall->livingroom]",
                "portal[livingroom->diningoffice]",
                "portal[diningoffice->outside]"]
        steps_to_kitchen = [('Physical', 'me',  0, 'kitchen',
                             'portal[myroom->diningoffice]',  0.0),
                            ('Physical', 'me', 1, 'kitchen',
                             'portal[diningoffice->kitchen]', 0.0)]
        steps_outside = []
        i = 0
        while i < len(mjos):
            steps_outside.append(('Physical', 'mom', i, 'outside',
                                  mjos[i], 0.0))
            i += 1

        def mkstepd(dimension, thing, idx, destination, portal, progress):
            return {"dimension": dimension,
                    "thing": thing,
                    "idx": idx,
                    "destination": destination,
                    "portal": portal,
                    "progress": progress}

        self.steps = [mkstepd(*step)
                      for step in steps_to_kitchen + steps_outside]

        def mkcontd(dimension, contained, container):
            return {"dimension": dimension,
                    "contained": contained,
                    "container": container}

        self.containments = [mkcontd('Physical', th[0], th[1]) for th in ths]

        def mkboardd(dimension, width, height, wallpaper):
            return {"dimension": dimension,
                    "width": width,
                    "height": height,
                    "wallpaper": wallpaper}

        self.boards = [mkboardd('Physical', 800, 600, 'wall')]

        def mkboardmenud(board, menu):
            return {"board": board,
                    "menu": menu}

        self.boardmenu = [mkboardmenud('Physical', menuname)
                          for menuname in menunames]

        def mkimgd(name, path, rltile):
            return {"name": name,
                    "path": path,
                    "rltile": rltile}

        imgtups = [("troll_m", "rltiles/player/base/troll_m.bmp", True),
                   ("zruty", "rltiles/nh-mon0/z/zruty.bmp", True),
                   ("orb", "orb.png", False),
                   ("wall", "wallpape.jpg", False)]
        self.imgs = [mkimgd(*tup) for tup in imgtups]

        def mkspotd(dimension, place, img, x, y, visible, interactive):
            return {"dimension": dimension,
                    "place": place,
                    "img": img,
                    "x": x,
                    "y": y,
                    "visible": visible,
                    "interactive": interactive}

        self.spots = [
            mkspotd('Physical', 'myroom', "orb", 400, 100, True, True),
            mkspotd('Physical', 'mybathroom', 'orb', 450, 150, True, True),
            mkspotd('Physical', 'guestroom', 'orb', 400, 200, True, True),
            mkspotd('Physical', 'livingroom', 'orb', 300, 150, True, True),
            mkspotd('Physical', 'diningoffice', 'orb', 350, 200, True, True),
            mkspotd('Physical', 'kitchen', 'orb', 350, 150, True, True),
            mkspotd('Physical', 'longhall', 'orb', 250, 150, True, True),
            mkspotd('Physical', 'momsroom', 'orb', 250, 100, True, True),
            mkspotd('Physical', 'momsbathroom', 'orb', 250, 200, True, True),
            mkspotd('Physical', 'outside', 'orb', 300, 100, True, True)]

        def mkpawnd(dimension, thing, img, visible, interactive):
            return {"dimension": dimension,
                    "thing": thing,
                    "img": img,
                    "visible": visible,
                    "interactive": interactive}

        pawntups = [('Physical', 'me', "troll_m", True, True),
                    ('Physical', 'mom', 'zruty', True, True)]
        self.pawns = [mkpawnd(*tup) for tup in pawntups]

        self.table_contents = {
            "dimension": self.dimensions,
            "menu": self.menus,
            "menuitem": self.menuitems,
            "color": self.colors,
            "style": self.styles,
            "item": self.places + self.portals + self.things,
            "place": self.places,
            "portal": self.portals,
            "thing": self.things,
            "location": self.locations,
            "containment": self.containments,
            "journey_step": self.steps,
            "board": self.boards,
            "boardmenu": self.boardmenu,
            "img": self.imgs,
            "spot": self.spots,
            "pawn": self.pawns}

default = DefaultParameters()
