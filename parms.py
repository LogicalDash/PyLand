class DefaultParameters:
    def __init__(self):
#        stubs = ['start_new_map', 'open_map', 'save_map', 'quit_map_editor', 'select_all', 'copy', 'paste', 'delete', 'new_custom_place', 'new_workplace', 'new_lair', 'new_commons', 'new_custom_thing', 'new_decoration', 'new_clothing', 'new_tool']
#        for stub in stubs:
#            exec('def %s():\n\tpass' % stub)

        game_menu_items = { 'New' : 'start_new_map',
                    'Open' : 'open_map',
                    'Save' : 'save_map',
                    'Quit' : 'quit_map_editor' }
        editor_menu_items = { 'Select All' : 'select_all',
                      'Copy' : 'copy',
                      'Paste' : 'paste',
                      'Delete' : 'delete' }
        place_menu_items = { 'Custom Place' : 'new_custom_place',
                     'Workplace' : 'new_workplace',
                     'Commons' : 'new_commons',
                     'Lair' : 'new_lair' }
        thing_menu_items = { 'Custom Thing' : 'new_custom_thing',
                     'Decoration' : 'new_decoration',
                     'Clothing' : 'new_clothing',
                     'Tool' : 'new_tool' }
        menu_names = { 'Game' : 'game_menu_items',
                       'Editor' : 'editor_menu_items',
                       'Place' : 'place_menu_items',
                       'Thing' : 'thing_menu_items' }

        self.menuitems = []
        for menu in menu_names.iteritems():
            i = 0
            exec('menu_contents = ' + menu[1] + ".iteritems()")
            for content in menu_contents:
                self.menuitems.append(((menu[0],), (i, content[0], content[1])))
                i += 1

        little_basic_menus = [ ('Game', 0), ('Editor', 200), ('Place', 400), ('Thing', 600) ]
        self.menus = [ ((m[0],), (m[1], 200, 200, 400, 'Default')) for m in little_basic_menus ]

        solarized_colors = { 'base03' : (0x00, 0x2b, 0x36),
                             'base02' : (0x07, 0x36, 0x42),
                             'base01' : (0x58, 0x6e, 0x75),
                             'base00' : (0x65, 0x7b, 0x83),
                             'base0' : (0x83, 0x94, 0x96),
                             'base1' : (0x93, 0xa1, 0xa1),
                             'base2' : (0xee, 0xe8, 0xd5),
                             'base3' : (0xfd, 0xf6, 0xe3),
                             'yellow' : (0xb5, 0x89, 0x00),
                             'orange' : (0xcb, 0x4b, 0x16),
                             'red' : (0xdc, 0x32, 0x2f),
                             'magenta' : (0xd3, 0x36, 0x82),
                             'violet' : (0x6c, 0x71, 0xc4),
                             'blue' : (0x26, 0x8b, 0xd2),
                             'cyan' : (0x2a, 0xa1, 0x98),
                             'green' : (0x85, 0x99, 0x00) }

        self.colors = [ (('solarized-' + color[0],), (color[1][0], color[1][1], color[1][2]) ) for color in solarized_colors.iteritems() ]
        self.styles = [ (('Default',), ('DejaVu Sans', 16, 6, 'solarized-base03', 'solarized-base2', 'solarized-base1', 'solarized-base01')) ]
        ps = [ 'myroom', 'guestroom', 'mybathroom', 'diningoffice', 'kitchen', 'livingroom', 'longhall', 'mombathroom', 'momroom', 'outside' ]
        self.places = [ ((p,), ()) for p in ps]
        pos = [
            ('myroom', 'guestroom'),
            ('myroom', 'mybathroom'),
            ('myroom', 'outside', False),
            ('myroom', 'diningoffice'),
            ('myroom', 'livingroom'),
            ('guestroom', 'diningoffice'),
            ('guestroom', 'livingroom'),
            ('guestroom', 'mybathroom'),
            ('guestroom', 'outside', False),
            ('livingroom', 'diningoffice'),
            ('diningoffice', 'outside'),
            ('diningoffice', 'kitchen'),
            ('livingroom', 'longhall'),
            ('longhall', 'momsbathroom'),
            ('longhall', 'momsroom'),
            ('momsroom', 'outside', False)
            ]
        self.portals = [ (("portal[%s->%s]" % po[:2],), po) for po in pos ]
        ths = [
            ('me', 'myroom'),
            ('diningtable', 'diningoffice'),
            ('mydesk', 'myroom'),
            ('mybed', 'myroom'),
            ('bustedchair', 'myroom'),
            ('sofas', 'livingroom'),
            ('fridge', 'kitchen'),
            ('momsbed', 'momsroom')
            ]
        self.things = [ ((th[0],), th[1:]) for th in ths ]
        atts = [
            ('life', 'bool'),
            ('bulk', 'int', [], 0),
            ('grams', 'float', [], 0.0),
            ('stickiness', 'int', [], -10, 10),
            ('grade level', 'int', ['Preschool', 'Kindergarten', 'Post-secondary'], 1, 12)
            ]
        self.attributes = [ ((att[0],),att[1:]) for att in atts ]
        tribs = [
            ('me', 'life', True),
            ('me', 'bulk', 7),
            ('me', 'grams', 63502.9),
            ('me', 'stickiness', 1),
            ('me', 'grade level', 'Post-secondary')
            ]
        self.attributions = [ ((trib[1], trib[0]), (trib[2],)) for trib in tribs ]