# TODO: give a board to every pawn and spot TODO: redo
# pawn.waypoint(...) so it looks in the database for a spot to go to
# TODO: remove references to spotgraph from spot and rewrite
# appropriately
# TODO: some way of distinguishing between routes on
# different game boards that doesn't rely on the Board class, since
# that is a widget and not a game logic thing

tabs = ["CREATE TABLE dimension "
        "(name text primary key);",
        "CREATE TABLE item "
        "(dimension, name text, "
        "foreign key(dimension) references dimension(name));",
        "CREATE TABLE place "
        "(dimension, name text, "
        "foreign key(dimension, name) references item(dimension, name));",
        "CREATE TABLE thing "
        "(dimension, name text, "
        "foreign key(dimension, name) references item(dimension, name));",
        "CREATE TABLE portal "
        "(dimension, name text,"
        "from_place text, to_place text, "
        "foreign key(dimension, name) references item(dimension, name), "
        "foreign key(dimension, from_place) references place(dimenison, name),"
        " foreign key(dimension, to_place) references place(dimension, name), "
        "primary key(dimension, name), "
        "check(from_place<>to_place));",
        "CREATE TABLE location "
        "(dimension, thing, place "
        "foreign key(dimension, thing) references thing(dimension, name), "
        "foreign key(dimension, place) references place(dimension, name), "
        "primary key(dimension, thing));",
        "CREATE TABLE containment "
        "(dimension, contained, container, "
        "foreign key(dimension, contained) references thing(dimension, name), "
        "foreign key(dimension, container) references thing(dimension, name), "
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
        "CREATE TABLE board "
        "(dimension primary key, width integer, height integer, wallpaper, "
        "foreign key(dimension) references dimension(name), "
        "foreign key(wallpaper) references image(name));",
        "CREATE TABLE spot "
        "(dimension, place, img, x, y"
        "foreign key(dimension, place) references place(dimension, name), "
        "foreign key(img) references img(name), "
        "primary key(dimension, place);",
        "CREATE TABLE pawn "
        "(dimension, thing, img, "
        "foreign key(img) references img(name), "
        "foreign key(dimension, thing) references thing(dimension, name), "
        "primary key(dimension, thing));",
        "CREATE TABLE color "
        "(name text primary key, "
        "red integer not null check(red between 0 and 255), "
        "green integer not null check(green between 0 and 255), "
        "blue integer not null check(blue between 0 and 255), "
        "alpha integer default 255 check(alpha between 0 and 255));",
        "CREATE TABLE style "
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
        "foreign key(fg_active) references color(name));",
        "CREATE TABLE menu "
        "(name text primary key, "
        "x float not null, "
        "y float not null, "
        "width float not null, "
        "height float not null, "
        "style text default 'Default', "
        "visible boolean default 0, "
        "foreign key(style) references style(name));",
        "CREATE TABLE menuitem "
        "(menu text, idx integer, text text, onclick text, closer boolean, "
        "foreign key(menu) references menu(name), primary key(menu, idx));",
        "CREATE TABLE boardmenu "
        "(board text, menu text, "
        "foreign key(board) references board(dimension), "
        "foreign key(menu) references menu(name));",
        "CREATE TABLE step "
        "(dimension, "
        "thing, "
        "destination, "
        "portal, "
        "idx integer, "
        "progress float, "
        "foreign key(dimension, thing) references thing(dimension, name), "
        "foreign key(dimension, portal) references portal(dimension, name), "
        "foreign key(dimension, destination) "
        "references place(dimension, name), "
        "check(progress>=0.0), "
        "check(progress<1.0), "
        "primary key(dimension, thing, destination, idx));"]


stubs = ['start_new_map',
         'open_map',
         'save_map',
         'quit_map_editor',
         'select_all',
         'copy',
         'paste',
         'delete',
         'new_custom_place',
         'new_workplace',
         'new_lair',
         'new_commons',
         'new_custom_thing',
         'new_decoration',
         'new_clothing',
         'new_tool',
         'show_game_menu',
         'show_editor_menu',
         'show_place_menu',
         'show_thing_menu']


game_menu_items = {'New': 'start_new_map',
                   'Open': 'open_map',
                   'Save': 'save_map',
                   'Quit': 'quit_map_editor'}
editor_menu_items = {'Select All': 'select_all',
                     'Copy': 'copy',
                     'Paste': 'paste',
                     'Delete': 'delete'}
place_menu_items = {'Custom Place': 'new_custom_place',
                    'Workplace': 'new_workplace',
                    'Commons': 'new_commons',
                    'Lair': 'new_lair'}
thing_menu_items = {'Custom Thing': 'new_custom_thing',
                    'Decoration': 'new_decoration',
                    'Clothing': 'new_clothing',
                    'Tool': 'new_tool'}
main_menu_items = {'Game': 'show_game_menu',
                   'Editor': 'show_editor_menu',
                   'Place': 'show_place_menu',
                   'Thing': 'show_thing_menu'}


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
              'mombathroom',
              'momroom',
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
        self.stubs = {}
        for stub in stubs:
            self.addstub(stub)
        # I'm going to have the menu bar on the left of the
        # screen. For convenience.
        self.menus = [('Game', 0.1, -0.02, 0.8, -0.2, 'Default', False),
                      ('Editor', 0.1, -0.24, 0.8, -0.2, 'Default', False),
                      ('Place', 0.1, -0.46, 0.8, -0.2, 'Default', False),
                      ('Thing', 0.1, -0.68, 0.8, -0.2, 'Default', False),
                      ('Main', 0.0, 0.0, 0.1, 1.0, 'Default', False)]
        menunames = [tup[0] for tup in self.menus]
        self.menuitems = []
        i = 0
        for item in game_menu_items.iteritems():
            self.menuitems.append(('Game', i, item[0], item[1], True))
            i += 1
        i = 0
        for item in editor_menu_items.iteritems():
            self.menuitems.append(('Editor', i, item[0], item[1], True))
            i += 1
        i = 0
        for item in place_menu_items.iteritems():
            self.menuitems.append(('Place', i, item[0], item[1], True))
            i += 1
        i = 0
        for item in thing_menu_items.iteritems():
            self.menuitems.append(('Thing', i, item[0], item[1], True))
            i += 1
        i = 0
        for item in main_menu_items.iteritems():
            self.menuitems.append(('Main', i, item[0], item[1], False))
            i += 1

        self.colors = [('solarized-' + color[0],
                        color[1][0], color[1][1], color[1][2])
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
               ('momsbed', 'momsroom')]
        self.things = [('Physical', th[0]) for th in ths]
        self.locations = [('Physical',) + th for th in ths]
        mjos = ["portal[momsroom->longhall]",
                "portal[longhall->livingroom]",
                "portal[livingroom->diningoffice]",
                "portal[diningoffice->outside]"]
        steps_to_kitchen = [('Physical', 'me', 'kitchen',
                             'portal[myroom->diningoffice]', 0,  0.0),
                            ('Physical', 'me', 'kitchen',
                             'portal[diningoffice->kitchen', 0, 0.0)]
        steps_outside = []
        i = 0
        while i < len(mjos):
            steps_outside.append(('Physical', 'mom', 'outside',
                                  mjos[i], i, 0.0))
            i += 1
        journeys = [steps_to_kitchen, steps_outside]
        self.steps = []
        for journey in journeys:
            self.steps += journey
        self.containment = [('Physical', th[0], th[1]) for th in ths]
        self.boards = [('Physical', 'Default')]
        self.boardmenu = [('Default', menuname) for menuname in menunames]

default = DefaultParameters()
