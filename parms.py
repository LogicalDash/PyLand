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
        "CREATE TABLE containment "
        "(dimension, contained, container, "
        "foreign key(dimension, contained) references item(dimension, name), "
        "foreign key(dimension, container) references item(dimension, name), "
        "primary key(dimension, contained), "
        "check(contained<>container);",
        "CREATE TABLE attribute "
        "(name text primary key, type text, lower, upper);",
        "CREATE TABLE attribution "
        "(dimension, attributed_to, attribute, value, "
        "foreign key(dimension, attributed_to) "
        "references item(dimension, name), "
        "foreign key(attribute) references attribute(name));"
        "CREATE TABLE permitted "
        "(attribute, value, "
        "foreign key(attribute) references attribute(name));"
        "CREATE TABLE img "
        "(name text primary key, path, rltile);",
        "CREATE TABLE map "
        "(dimension, name text primary key, "
        "foreign key(dimension) references dimension(name));"
        "CREATE TABLE map_place "
        "(map, place, dimension, "
        "foreign key(map, dimension) references map(name, dimension), "
        "foreign key(place, dimension) references place(name, dimension), "
        "primary key(place, dimension));",
        "CREATE TABLE map_port "
        "(dimension, map, port, "
        "foreign key(map) references map(name), "
        "foreign key(dimension, port) references portal(dimension, name));",
        "CREATE TABLE board "
        "(map primary key, width integer, height integer, wallpaper, "
        "foreign key(map) references map(name), "
        "foreign key(wallpaper) references image(name));",
        "CREATE TABLE spot "
        "(dimension, place, board, x integer, y integer, r integer, "
        "foreign key(dimension, place) references place(dimension, name), "
        "foreign key(board) references board(name), "
        "primary key(dimension, place, board));",
        "CREATE TABLE pawn "
        "(dimension, thing, board, img, "
        "foreign key(img) references img(name), "
        "foreign key(dimension, thing) references thing(dimension, name), "
        "primary key(dimension, thing, board));",
        "CREATE TABLE color "
        "(name text primary key, "
        "red integer not null check(red between 0 and 255), "
        "green integer not null check(green between 0 and 255), "
        "blue integer not null check(blue between 0 and 255));",
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
        "CREATE TABLE step "
        "(dimension, "
        "map, "
        "thing, "
        "ord integer not null, "
        "destination, "
        "portal, "
        "progress float not null, "
        "foreign key(map) references map(name), "
        "foreign key(dimension, thing) references thing(dimension, name), "
        "foreign key(dimension, portal) references portal(dimension, name), "
        "foreign key(dimension, destination) "
        "references place(dimension, name), "
        "check(progress>=0.0), "
        "check(progress<1.0), "
        "primary key(dimension, map, thing, ord, destination));"]


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


places = [(p, 'Physical') for p in placenames]


atts = [('life', 'bool'),
        ('bulk', 'int', [], 0),
        ('grams', 'float', [], 0.0),
        ('stickiness', 'int', [], -10, 10),
        ('grade level', 'int',
         ['Preschool', 'Kindergarten', 'Post-secondary'],
         1, 12)]


class DefaultParameters:
    def addstub(self, stub):
        exec('def %s():\n\tpass\n\nself.stubs["%s"]=%s' % (stub, stub, stub))

    def __init__(self):
        self.tabs = tabs
        self.stubs = {}
        for stub in stubs:
            self.addstub(stub)
        # I'm going to have the menu bar on the left of the
        # screen. For convenience.
        self.menus = [(('Game',), (0.1, -0.02, 0.8, -0.2, 'Default', False)),
                      (('Editor',), (0.1, -0.24, 0.8, -0.2, 'Default', False)),
                      (('Place',), (0.1, -0.46, 0.8, -0.2, 'Default', False)),
                      (('Thing',), (0.1, -0.68, 0.8, -0.2, 'Default', False)),
                      (('Main',), (0.0, 0.0, 0.1, 1.0, 'Default', False))]
        self.menuitems = []
        i = 0
        for item in game_menu_items.iteritems():
            self.menuitems.append((('Game', i), (item[0], item[1], True)))
            i += 1
        i = 0
        for item in editor_menu_items.iteritems():
            self.menuitems.append((('Editor', i), (item[0], item[1], True)))
            i += 1
        i = 0
        for item in place_menu_items.iteritems():
            self.menuitems.append((('Place', i), (item[0], item[1], True)))
            i += 1
        i = 0
        for item in thing_menu_items.iteritems():
            self.menuitems.append((('Thing', i), (item[0], item[1], True)))
            i += 1
        i = 0
        for item in main_menu_items.iteritems():
            self.menuitems.append((('Main', i), (item[0], item[1], False)))
            i += 1

        self.colors = [(('solarized-' + color[0],),
                        (color[1][0], color[1][1], color[1][2]))
                       for color in solarized_colors.iteritems()]
        self.styles = [(('Default',),
                        ('DejaVu Sans', 16, 6,
                         'solarized-base03',
                         'solarized-base2',
                         'solarized-base1',
                         'solarized-base01'))]
        self.places = [((p,), ()) for p in places]
        pos = [
            ('myroom', 'guestroom', True),
            ('myroom', 'mybathroom', True),
            ('myroom', 'outside', False),
            ('myroom', 'diningoffice', True),
            ('myroom', 'livingroom', True),
            ('guestroom', 'diningoffice', True),
            ('guestroom', 'livingroom', True),
            ('guestroom', 'mybathroom', True),
            ('guestroom', 'outside', False),
            ('livingroom', 'diningoffice', True),
            ('diningoffice', 'outside', True),
            ('diningoffice', 'kitchen', True),
            ('livingroom', 'longhall', True),
            ('longhall', 'momsbathroom', True),
            ('longhall', 'momsroom', True),
            ('momsroom', 'outside', False)]
        self.portals = [(("portal[%s->%s]" % po[:2],), po) for po in pos]
        ths = [('me', 'myroom'),
               ('diningtable', 'diningoffice'),
               ('mydesk', 'myroom'),
               ('mybed', 'myroom'),
               ('bustedchair', 'myroom'),
               ('sofas', 'livingroom'),
               ('fridge', 'kitchen'),
               ('momsbed', 'momsroom')]
        self.things = [((th[0],), th[1:]) for th in ths]
        self.attributes = []
        for att in atts:
            if len(att) == 2:
                tta = att + ([], None, None)
            elif len(att) == 3:
                tta = att + (None, None)
            elif len(att) == 4:
                tta = att+(None,)
            else:
                tta = att
            self.attributes.append(((tta[0],), tta[1:]))
        tribs = [('me', 'life', True),
                 ('me', 'bulk', 7),
                 ('me', 'grams', 63502.9),
                 ('me', 'stickiness', 1),
                 ('me', 'grade level', 'Post-secondary')]
        self.attributions = [((trib[1], trib[0]), (trib[2],))
                             for trib in tribs]
