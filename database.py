# Problems:
#
# The various database functions can't all be the same for every
# object class. It doesn't make sense to have an update method for
# Place, for instance, since the table only records that a place
# exists by a certain name.
import sqlite3
import sys
import os
from widgets import Color, MenuItem, Menu, Spot, Pawn, Board, Style
from thing import Thing
from graph import Journey, Dimension, Place, Portal
from pyglet.resource import image
from parms import tables, default

sys.path.append(os.curdir)

defaultCommit = True


def untuple(list_o_tups):
    r = []
    for tup in list_o_tups:
        for val in tup:
            r.append(val)
    return r


def questionmarks(list_o_tups):
    q = "(" + ", ".join(["?"] * len(list_o_tups[0])) + ")"
    return [q] * len(list_o_tups)


def insstr(tabname, list_o_tups):
    return "INSERT INTO " + tabname + " VALUES " +\
        ", ".join(questionmarks(list_o_tups)) + ";"


class Database:
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        self.altered = []
        self.placedict = {}
        self.portaldict = {}
        self.thingdict = {}
        self.spotdict = {}
        self.imgdict = {}
        self.boarddict = {}
        self.menudict = {}
        self.menuitemdict = {}
        self.pawndict = {}
        self.styledict = {}
        self.colordict = {}
        self.journeydict = {}
        self.contentsdict = {}
        self.containerdict = {}
        self.placecontentsdict = {}
        self.portalorigdestdict = {}
        self.portaldestorigdict = {}
        self.typ = {'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool}
        self.func = {'toggle_menu_visibility': self.toggle_menu_visibility}
        self.imgs2load = set()

    def __del__(self):
        self.c.close()
        self.conn.commit()
        self.conn.close()

    def mkschema(self):
        for tab in tables:
            self.c.execute(tab)
        self.conn.commit()

    def initialized(self):
        try:
            for tab in ["thing", "place", "attribute", "img"]:
                self.c.execute("select count(*) from %s limit 1"
                               % (tab,))
            return True
        except sqlite3.OperationalError:
            return False

    def alter(self, obj):
        "Pass an object here to have the database remember it, both in the "
        "short term and eventually on the disk."
        if isinstance(obj, Dimension):
            self.dimdict[obj.name] = obj
        elif isinstance(obj, Place):
            self.placedict[obj.name] = obj
            self.attributiondict[obj.name] = obj.att
        elif isinstance(obj, Portal):
            self.portaldict[obj.name] = obj
            podd = self.portalorigdestdict
            pdod = self.portaldestorigdict
            podd[obj.origin.name][obj.destination.name] = obj
            pdod[obj.destination.name][obj.origin.name] = obj
            self.attributiondict[obj.name] = obj.att
        elif isinstance(obj, Thing):
            self.thingdict[obj.name] = obj
            self.attributiondict[obj.name] = obj.att
        elif isinstance(obj, Spot):
            self.spotdict[obj.place.name] = obj
        elif isinstance(obj, Board):
            self.boarddict[obj.name] = obj
        elif isinstance(obj, Menu):
            self.menudict[obj.name] = obj
        elif isinstance(obj, MenuItem):
            self.menuitemdict[obj.name] = obj
        elif isinstance(obj, Pawn):
            self.pawndict[obj.thing.name][obj.board.name] = obj
        elif isinstance(obj, Style):
            self.styledict[obj.name] = obj
        elif isinstance(obj, Color):
            self.colordict[obj.name] = obj
        else:
            raise Exception("I have nowhere to put this!")
        self.altered.append(obj)

    def sync(self):
        pass
        # TODO: write all altered objects to disk

    def insert_1(self, tabname, default_list):
        qm = ["?"] * len(default_list)
        qrystr = "INSERT INTO %s VALUES (" % (tabname,) + ", ".join(qm) + ")"
        self.c.execute(qrystr, default_list)

    def insert_n(self, tabname, tups):
        qm = ", ".join(["?"] * len(tups[0]))
        qrystr = "INSERT INTO %s VALUES (%s);" % (tabname, qm)
        self.c.executemany(qrystr, tups)

    def insert(self, tabname, tups):
        self.insert_n(tabname, tups)

    def insert_defaults(self):
        # dimensions first because a lot of other stuff requires them
        self.insert_1("dimension", default.dimensions)
        # items
        self.insert("item", default.things)
        self.insert("item", default.places)
        portalkeys = [portal[:2] for portal in default.portals]
        self.insert("item", portalkeys)
        self.insert("thing", default.things)
        self.insert("place", default.places)
        self.insert("portal", default.portals)
        self.insert("location", default.locations)
        self.insert("containment", default.containments)
        self.insert("journey_step", default.steps)
        self.insert("img", default.imgs)
        self.insert("spot", default.spots)
        self.insert("pawn", default.pawns)
        self.insert("menuitem", default.menuitems)
        self.insert("color", default.colors)
        self.insert("style", default.styles)
        self.insert("menu", default.menus)
        self.insert("board", default.boards)
        self.insert("boardmenu", default.boardmenu)
        # functions
        for func in default.funcs:
            self.xfunc(func)

    def xfunc(self, func):
        self.func[func.__name__] = func

    def load_board(self, dimension):
        self.imgs2load = set()
        qrystr = "SELECT width, height, wallpaper "\
                 "FROM board WHERE dimension=?;"
        qrytup = (dimension,)
        self.c.execute(qrystr, qrytup)
        (w, h, texname) = self.c.fetchone()
        self.imgs2load.add(texname)
        self.load_places_in_dimension(dimension)
        places = self.placedict[dimension].values()
        self.load_things_in_dimension(dimension)
        things = self.thingdict[dimension].values()
        self.load_portals_in_dimension(dimension)
        self.load_containment_in_dimension(dimension)
        self.load_journeys_in_dimension(dimension)
        self.load_spots_for_board(dimension)
        self.load_pawns_for_board(dimension)
        self.load_menus_for_board(dimension)
        journeys = self.journeydict[dimension].values()
        for thing in things:
            if dimension in self.containerdict:
                if thing.name in self.containerdict[dimension]:
                    thing.container = self.containerdict[dimension][thing.name]
                else:
                    thing.container = None
                if thing.name in self.contentsdict[dimension]:
                    thing.contents = self.contentsdict[dimension][thing.name]
                else:
                    thing.contents = []
            if dimension in self.placedict and \
               thing.location in self.placedict[dimension]:
                thing.location = self.placedict[dimension][thing.location]
            else:
                thing.location = None
            if thing.name in self.journeydict[dimension]:
                thing.journey = self.journeydict[dimension][thing.name]
        podd = self.portalorigdestdict
        pcd = self.placecontentsdict
        for place in places:
            if place.name in podd[dimension]:
                place.portals = podd[dimension][place.name].values()
            else:
                place.portals = []
            if place.name in pcd[dimension]:
                place.contents = pcd[dimension][place.name]
            else:
                place.contents = []
        for journey in journeys:
            journey.thing = self.thingdict[dimension][journey.thing]
            journey.dest = self.placedict[dimension][journey.dest]
        spots = self.spotdict[dimension].values()
        places = self.placedict[dimension].values()
        portals = self.portaldict[dimension].values()
        things = self.thingdict[dimension].values()
        pawns = self.pawndict[dimension].values()
        menus = self.menudict[dimension].values()
        self.load_imgs()
        texture = self.imgdict[texname]
        board = Board(dimension, w, h, texture, spots, pawns, menus)
        for spot in spots:
            spot.img = self.imgdict[spot.img]
            spot.r = spot.img.width / 2
            spot.place = self.placedict[dimension][spot.place]
            spot.board = board
        for pawn in pawns:
            pawn.img = self.imgdict[pawn.img]
            pawn.r = pawn.img.width / 2
            pawn.thing = self.thingdict[dimension][pawn.thing]
            pawn.board = board
        for place in places:
            place.spot = self.spotdict[dimension][place.name]
        for portal in portals:
            portal.orig = self.placedict[dimension][portal.orig]
            portal.dest = self.placedict[dimension][portal.dest]
        for thing in things:
            if thing in self.pawndict[dimension]:
                thing.pawn = self.pawndict[dimension][thing.name]
            else:
                # Not all things show up like pawns on the board.
                # Some of them only show up in your inventory, or the
                # contents listing of a place.
                thing.pawn = None
        for menu in self.menudict[dimension].values():
            menu.board = board
            for menuitem in menu.items:
                if menuitem is None:
                    del menuitem
                else:
                    menuitem.board = board
        self.boarddict[dimension] = board
        return board

    def load_menus_for_board(self, board):
        qrystr = "SELECT DISTINCT menu FROM boardmenu WHERE board=?;"
        self.c.execute(qrystr, (board,))
        menunames = [row[0] for row in self.c]
        qm = ["?"] * len(menunames)
        qrystr = "SELECT name, left, bottom, top, right, style, visible "\
                 "FROM menu WHERE name IN (" + ", ".join(qm) + ");"
        self.c.execute(qrystr, menunames)
        menurows = self.c.fetchall()
        stylenames = set([row[5] for row in menurows])
        qm = ["?"] * len(stylenames)
        qrystr = "SELECT name, fontface, fontsize, spacing, "\
                 "bg_inactive, bg_active, fg_inactive, fg_active "\
                 "FROM style WHERE name IN (" + ", ".join(qm) + ");"
        qrylst = list(stylenames)
        self.c.execute(qrystr, qrylst)
        stylerows = self.c.fetchall()
        colornames = set()
        for row in stylerows:
            colornames.update(row[4:])
        qrylst = list(colornames)
        qm = ["?"] * len(qrylst)
        qrystr = "SELECT name, red, green, blue, alpha FROM color "\
                 "WHERE name IN (" + ", ".join(qm) + ");"
        self.c.execute(qrystr, qrylst)
        for row in self.c:
            color = Color(*row)
            self.colordict[row[0]] = color
        for row in stylerows:
            (name, fontface, fontsize, spacing,
             bg_i, bg_a, fg_i, fg_a) = row
            style = Style(name, fontface, fontsize, spacing,
                          self.colordict[bg_i],
                          self.colordict[bg_a],
                          self.colordict[fg_i],
                          self.colordict[fg_a])
            self.styledict[name] = style
        menunames = set()
        if board not in self.menudict:
            self.menudict[board] = {}
        for row in menurows:
            (name, x, y, w, h, sty, vis) = row
            menunames.add(name)
            style = self.styledict[sty]
            menu = Menu(board, name, x, y, w, h, style, vis)
            self.menudict[board][name] = menu
        self.load_items_in_menus(board, menunames)

    def load_items_in_menus(self, board, names):
        qrylst = list(names)
        qm = ["?"] * len(qrylst)
        qrystr = ("SELECT menu, idx, text, onclick, onclick_arg, closer, "
                  "visible, interactive FROM menuitem WHERE menu IN ("
                  + ", ".join(qm) + ");")
        self.c.execute(qrystr, qrylst)
        md = self.menudict[board]
        if board not in self.menuitemdict:
            self.menuitemdict[board] = {}
        mid = self.menuitemdict[board]
        for row in self.c:
            (menun, idx, text, fname, farg,
             closer, visible, interactive) = row
            onclick = self.func[fname]
            menu = md[menun]
            mi = MenuItem(board, menu, idx, text, onclick, farg,
                          closer, visible, interactive)
            if not mi.visible:
                continue
            while len(menu.items) <= idx:
                menu.items.append(None)
            menu.items[idx] = mi
            if menun not in mid:
                mid[menun] = {}
            mid[menun][idx] = mi

    def load_places_in_dimension(self, dimension):
        qrystr = "SELECT name FROM place WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        if dimension not in self.placedict:
            self.placedict[dimension] = {}
        pd = self.placedict[dimension]
        for row in self.c:
            name = row[0]
            place = Place(dimension, name)
            pd[name] = place

    def load_things_in_dimension(self, dimension):
        qrystr = "SELECT thing, place FROM location WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        td = self.thingdict
        pcd = self.placecontentsdict
        for d in [td, pcd]:
            if dimension not in d:
                d[dimension] = {}
        for row in self.c:
            (name, location) = row
            thing = Thing(dimension, name, location)
            td[dimension][name] = thing
            if location not in pcd[dimension]:
                pcd[dimension][location] = []
            pcd[dimension][location].append(thing)

    def load_portals_in_dimension(self, dimension):
        qrystr = "SELECT name, from_place, to_place FROM portal "\
                 "WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        for row in self.c:
            (name, orign, destn) = row
            pd = self.portaldict
            podd = self.portalorigdestdict
            pdod = self.portaldestorigdict
            dictlist = [pd, podd, pdod]
            for d in dictlist:
                if dimension not in d:
                    d[dimension] = {}
            if orign not in podd[dimension]:
                podd[dimension][orign] = {}
            if destn not in pdod[dimension]:
                pdod[dimension][destn] = {}
            portal = Portal(dimension, name, orign, destn)
            podd[dimension][orign][destn] = portal
            pdod[dimension][destn][orign] = portal
            pd[dimension][name] = portal

    def load_containment_in_dimension(self, dimension):
        qrystr = "SELECT contained, container "\
                 "FROM containment WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        container = self.containerdict
        contents = self.contentsdict
        if dimension not in container:
            container[dimension] = {}
        if dimension not in contents:
            contents[dimension] = {}
        for row in self.c:
            (inside, outside) = row
            container[dimension][inside] = outside
            if outside not in contents[dimension]:
                contents[dimension][outside] = []
            contents[dimension][outside].append(inside)

    def load_spots_for_board(self, dimension):
        qrystr = "SELECT place, img, x, y, visible, interactive "\
                 "FROM spot WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        if dimension not in self.spotdict:
            self.spotdict[dimension] = {}
        sd = self.spotdict[dimension]
        for row in self.c:
            (place, img, x, y, vis, inter) = row
            self.imgs2load.add(img)
            spot = Spot(dimension, place, img, x, y, vis, inter)
            sd[place] = spot

    def load_pawns_for_board(self, dimension):
        qrystr = "SELECT dimension, thing, img, visible, interactive "\
                 "FROM pawn WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        if dimension not in self.pawndict:
            self.pawndict[dimension] = {}
        pd = self.pawndict[dimension]
        for row in self.c:
            (dimension, thing, img, vis, inter) = row
            self.imgs2load.add(img)
            pawn = Pawn(dimension, thing, img, vis, inter)
            pd[thing] = pawn

    def load_imgs(self):
        qrylst = list(self.imgs2load)
        qm = ["?"] * len(qrylst)
        qrystr = "SELECT name, path, rltile FROM img WHERE name IN (" +\
                 ", ".join(qm) + ");"
        self.c.execute(qrystr, qrylst)
        regular = set()
        rltile = set()
        for row in self.c:
            if row[2]:
                rltile.add(row)
            else:
                regular.add(row)
        for img in regular:
            self.load_regular_img(img[0], img[1])
        for img in rltile:
            self.load_rltile(img[0], img[1])

    def load_rltile(self, name, path):
        badimg = image(path)
        badimgd = badimg.get_image_data()
        bad_rgba = badimgd.get_data('RGBA', badimgd.pitch)
        good_data = bad_rgba.replace('\xffGll', '\x00Gll')
        good_data = good_data.replace('\xff.', '\x00.')
        badimgd.set_data('RGBA', badimgd.pitch, good_data)
        rtex = badimgd.get_texture()
        rtex.name = name
        self.imgdict[name] = rtex
        return rtex

    def load_regular_img(self, name, path):
        tex = image(path).get_image_data().get_texture()
        tex.name = name
        self.imgdict[name] = tex
        return tex

    def load_journeys_in_dimension(self, dimension):
        # At most one journey per thing. I'd like to have a way of
        # keeping precomputed journeys--walks--on file as well,
        # but this is not that... a walk wouldn't have thing or
        # progress associated.
        qrystr = "SELECT thing, idx, destination, portal, progress "\
                 "FROM journey_step WHERE dimension=?;"
        self.c.execute(qrystr, (dimension,))
        if dimension not in self.journeydict:
            self.journeydict[dimension] = {}
        for row in self.c:
            (thing, idx, destination, port, progress) = row
            portal = self.portaldict[dimension][port]
            if thing in self.journeydict[dimension]:
                journey = self.journeydict[dimension][thing]
                while len(journey.steplist) <= idx:
                    journey.steplist.append(None)
                journey.steplist[idx] = portal
            else:
                journey = Journey(thing, destination, [portal])
                self.journeydict[dimension][thing] = journey

    def toggle_menu_visibility(self, stringly):
        """Given a string arg of the form boardname.menuname, toggle the
visibility of the given menu on the given board.

"""
        (boardname, menuname) = stringly.split('.')
        menu = self.menudict[boardname][menuname]
        menu.toggle_visibility()

    def insert_things(self, things):
        thingrows = [tuple(it) for it in things]
        self.insert_rows("thing", thingrows)

    def insert_places(self, places):
        placerows = [tuple(it) for it in places]
        self.insert_rows("place", placerows)

    def insert_portals(self, ports):
        portrows = [tuple(it) for it in ports]
        self.insert_rows("portal", portrows)

    def insert_pawns(self, pawns):
        pawnrows = [tuple(it) for it in pawns]
        self.insert_rows("pawn", pawnrows)

    def insert_spots(self, spots):
        spotrows = [tuple(it) for it in spots]
        self.insert_rows("spot", spotrows)

    def insert_rows(self, tabname, rows):
        qrystr = insstr(tabname, rows)
        qrylst = untuple(rows)
        self.c.execute(qrystr, qrylst)

    def keys_known(self, tabname, keynames, keys):
        # Return a sublist of keys containing those keys that are
        # already in the table by the given name, tabname.
        keynamesstr = ", ".join(keynames)
        qrystr = ("SELECT " + keynamesstr + " FROM " + tabname +
                  " WHERE (" + keynamesstr + ") IN ("
                  + questionmarks(keys) + ");")
        qrylst = untuple(keys)
        self.c.execute(qrystr, qrylst)
        return self.c.fetchall()

    def keys_unknown(self, tabname, keynames, keys):
        keys_known = self.keys_known(tabname, keynames, keys)
        keys_known_set = set(keys_known)
        test_keys_set = set(keys)
        keys_unknown_set = test_keys_set.difference(keys_known_set)
        return iter(keys_unknown_set)

    def keys_known_not_loaded(self, tabname, keynames, keys_loaded):
        # This will most likely be used for finding keys to delete.
        keynamesstr = ", ".join(keynames)
        qrystr = ("SELECT " + keynamesstr + " FROM " + tabname +
                  " WHERE (" + keynamesstr + ") NOT IN (" +
                  questionmarks(keys_loaded) + ");")
        qrylst = untuple(keys_loaded)
        self.c.execute(qrystr, qrylst)

    def rows_missing(self, tabname, keynames, rows):
        keylen = len(keynames)
        key2row = dict([(row[:keylen], row) for row in rows])
        keys = key2row.keys()
        keys_missing = self.keys_unknown(tabname, keynames, keys)
        return [key2row[key] for key in keys_missing]

    def rows_different(self, tabname, keynames, valnames, rows):
        keylen = len(keynames)
        keys = [row[:keylen] for row in rows]
        keys_qm = questionmarks(keys)
        rows_qm = questionmarks(rows)
        keyvalstr = ", ".join(keynames + valnames)
        keystr = ", ".join(keynames)
        qrystr = ("SELECT " + keyvalstr + " FROM " + tabname +
                  " WHERE (" + keystr + ") IN (" + keys_qm +
                  ") AND (" + keyvalstr + ") NOT IN (" + rows_qm + ");")
        qrylst = untuple(keys) + untuple(rows)
        self.c.execute(qrystr, qrylst)
        return self.c.fetchall()
