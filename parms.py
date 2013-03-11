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

tables = (thing_schemata +
          graph_schemata +
          widget_schemata +
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
           "CREATE TABLE attribute "
           "(name text primary key, type text, lower, upper);",
           "CREATE TABLE attribution "
           "(dimension, attributed_to, attribute, value, "
           "foreign key(dimension, attributed_to) "
           "references item(dimension, name), "
           "foreign key(attribute) references attribute(name));",
           "CREATE TABLE permitted "
           "(attribute, value, "
           "foreign key(attribute) references attribute(name));",
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
main_menu_items = {'Game': ('toggle_menu_by_name', 'Game'),
                   'Editor': ('toggle_menu_by_name', 'Editor'),
                   'Place': ('toggle_menu_by_name', 'Place'),
                   'Thing': ('toggle_menu_by_name', 'Thing')}


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
        self.dimensions = [("Physical")]
        self.tabs = tabs
        self.funcs = funcs
        # I'm going to have the menu bar on the left of the
        # screen. For convenience.
        self.menus = [('Game', 0.0, 0.3, 1.0, 0.2, 'Default', False, True),
                      ('Editor', 0.1, 0.3, 1.0, 0.2, 'Default', False, True),
                      ('Place', 0.1, 0.3, 1.0, 0.2, 'Default', False, True),
                      ('Thing', 0.1, 0.3, 1.0, 0.2, 'Default', False, True),
                      ('Main', 0.0, 0.0, 1.0, 0.12, 'Default', True, True)]
        menunames = [tup[0] for tup in self.menus]
        self.menuitems = []
        i = 0
        for item in game_menu_items.iteritems():
            self.menuitems.append(('Game', i, item[0], item[1],
                                   True, False, False))
            i += 1
        i = 0
        for item in editor_menu_items.iteritems():
            self.menuitems.append(('Editor', i, item[0], item[1],
                                   True, False, False))
            i += 1
        i = 0
        for item in place_menu_items.iteritems():
            self.menuitems.append(('Place', i, item[0], item[1],
                                   True, False, False))
            i += 1
        i = 0
        for item in thing_menu_items.iteritems():
            self.menuitems.append(('Thing', i, item[0], item[1],
                                   True, False, False))
            i += 1
        i = 0
        for item in main_menu_items.iteritems():
            self.menuitems.append(('Main', i, item[0], item[1],
                                   False, True, True))
            i += 1

        self.colors = [('solarized-' + color[0],
                        color[1][0], color[1][1], color[1][2], 255)
                       for color in solarized_colors.iteritems()]
        self.styles = [('Default',
                        'DejaVu Sans', 16, 6,
                        'solarized-base03',
                        'solarized-base2',
                        'solarized-base1',
                        'solarized-base01')]
        self.places = [('Physical', p) for p in placenames]
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
        portaldict = dict([(('Physical', "portal[%s->%s]" % po), po)
                           for po in pos])
        self.portals = [it[0] + it[1] for it in portaldict.iteritems()]
        ths = [('me', 'myroom'),
               ('diningtable', 'diningoffice'),
               ('mydesk', 'myroom'),
               ('mybed', 'myroom'),
               ('bustedchair', 'myroom'),
               ('sofas', 'livingroom'),
               ('fridge', 'kitchen'),
               ('momsbed', 'momsroom'),
               ('mom', 'momsroom')]
        self.things = [('Physical', th[0]) for th in ths]
        self.locations = [('Physical',) + th for th in ths]
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
        self.steps = steps_to_kitchen + steps_outside
        self.containments = [('Physical', th[0], th[1]) for th in ths]
        self.boards = [('Physical', 800, 600, 'wall')]
        self.boardmenu = [('Physical', menuname) for menuname in menunames]
        self.imgs = [("troll_m", "rltiles/player/base/troll_m.bmp", True),
                     ("zruty", "rltiles/nh-mon0/z/zruty.bmp", True),
                     ("orb", "orb.png", False),
                     ("wall", "wallpape.jpg", False)]
        self.spots = [('Physical', place, "orb", 0, 0, True, True) for place in placenames]
        self.pawns = [('Physical', 'me', "troll_m", True, True),
                      ('Physical', 'mom', 'zruty', True, True)]

default = DefaultParameters()
