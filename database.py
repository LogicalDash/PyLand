# Problems:
#
# The various database functions can't all be the same for every
# object class. It doesn't make sense to have an update method for
# Place, for instance, since the table only records that a place
# exists by a certain name.
import sqlite3, sys, os
from widgets import Color, MenuItem, Menu, Spot, Pawn, Board, Style
from thing import Thing
from graph import Journey, Dimension, Place, Portal
from pyglet.resource import image
from parms import tabs, default

sys.path.append(os.curdir)

defaultCommit = True


def qrystr_insert_into(tabname, tuplst):
    q = ["?"] * len(tuplst[0])
    qs = "(" + ", ".join(q) + ")"
    qm = [qs] * len(tuplst)
    return "INSERT INTO " + tabname + " VALUES " + ", ".join(qm) + ";"


class Database:
    def __init__(self, dbfile, xfuncs={}, defaultCommit=True):
        self.conn = sqlite3.connect(dbfile)
        self.readcursor = self.conn.cursor()
        self.writecursor = self.conn.cursor()
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
        self.func = xfuncs
        self.imgs2load = []

    def __del__(self):
        self.readcursor.close()
        self.writecursor.close()
        self.conn.commit()
        self.conn.close()

    def _write_all(self, qrystr, qrytups):
        qrylst = []
        for tup in qrytups:
            qrylst += tup
        self.writecursor.execute(qrystr, qrylst)

    def _insert_all(self, tabname, qrytups):
        qrystr = qrystr_insert_into(tabname, qrytups)
        self._write_all(qrystr, qrytups)

    def mkschema(self):
        for tab in tabs:
            self.writecursor.execute(tab)
        self.conn.commit()

    def initialized(self):
        try:
            for tab in ["thing", "place", "attribute", "img"]:
                self.readcursor.execute("select * from ? limit 1;", (tab,))
        except:
            return False
        return True

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

    def insert_defaults(self):
        # dimensions first because a lot of other stuff requires them
        self._insert_all("dimension", (default.dimensions,))
        # items
        self._insert_all("item", default.things)
        self._insert_all("item", default.places)
        portalkeys = [portal[:2] for portal in default.portals]
        self._insert_all("item", portalkeys)
        self._insert_all("thing", default.things)
        self._insert_all("place", default.places)
        self._insert_all("portal", default.portals)
        self._insert_all("location", default.locations)
        self._insert_all("containment", default.containments)
        self._insert_all("journey_step", default.steps)
        self._insert_all("img", default.imgs)
        self._insert_all("spot", default.spots)
        self._insert_all("pawn", default.pawns)
        self._insert_all("menuitem", default.menuitems)
        self._insert_all("color", default.colors)
        self._insert_all("style", default.styles)
        self._insert_all("menu", default.menus)
        self._insert_all("board", default.boards)
        self._insert_all("boardmenu", default.boardmenu)

    def load_board(self, dimension):
        qrystr = "SELECT width, height, wallpaper "\
                 "FROM board WHERE dimension=?;"
        qrytup = (dimension,)
        self.readcursor.execute(qrystr, qrytup)
        (w, h, texname) = self.readcursor.fetchone()
        self.imgs2load = [texname]
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
        pawns = self.pawndict[dimension].values()
        menus = self.menudict.values()
        self.load_imgs()
        for spot in spots:
            spot.img = self.imgdict[spot.img]
        for pawn in pawns:
            pawn.img = self.imgdict[pawn.img]
        texture = self.imgdict[texname]
        board = Board(dimension, w, h, texture, spots, pawns, menus)
        self.boarddict[dimension] = board

    def load_menus_for_board(self, board):
        qrystr = "SELECT menu FROM boardmenu WHERE board=?;"
        self.readcursor.execute(qrystr, (board,))
        menunames = [row[0] for row in self.readcursor]
        qm = ["?"] * len(menunames)
        qrystr = "SELECT name, x, y, width, height, style, visible "\
                 "FROM menu WHERE name IN (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, menunames)
        menurows = self.readcursor.fetchall()
        stylenames = [row[5] for row in menurows]
        qm = ["?"] * len(stylenames)
        qrystr = "SELECT name, fontface, fontsize, spacing, "\
                 "bg_inactive, bg_active, fg_inactive, fg_active "\
                 "FROM style WHERE name IN (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, stylenames)
        stylerows = self.readcursor.fetchall()
        colornames = []
        for row in stylerows:
            colornames.extend(iter(row[4:]))
        qm = ["?"] * len(colornames)
        qrystr = "SELECT name, red, green, blue, alpha FROM color "\
                 "WHERE name IN (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, colornames)
        for row in self.readcursor:
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
        menunames = []
        for row in menurows:
            (name, x, y, w, h, sty, vis) = row
            menunames.append(name)
            style = self.styledict[sty]
            menu = Menu(name, x, y, w, h, style, vis)
            self.menudict[name] = menu
        self.load_items_in_menus(menunames)

    def load_items_in_menus(self, names):
        qm = ["?"] * len(names)
        qrystr = "SELECT menuitem.menu, idx, text, onclick, closer "\
                 "FROM menuitem JOIN boardmenu ON "\
                 "menuitem.menu=boardmenu.menu "\
                 "WHERE menuitem.menu IN (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, names)
        md = self.menudict
        mid = self.menuitemdict
        for row in self.readcursor:
            (menun, idx, text, fname, closer) = row
            onclick = self.func[fname]
            mi = MenuItem(menun, idx, text, onclick, closer)
            menu = md[menun]
            while len(menu.items) <= idx:
                menu.items.append(None)
            menu.items[idx] = mi
            if menun not in mid:
                mid[menun] = {}
            mid[menun][idx] = mi

    def load_places_in_dimension(self, dimension):
        qrystr = "SELECT name FROM place WHERE dimension=?;"
        self.readcursor.execute(qrystr, (dimension,))
        pd = self.placedict
        if dimension not in pd:
            pd[dimension] = {}
        for row in self.readcursor:
            name = row[0]
            place = Place(dimension, name)
            pd[dimension][name] = place

    def load_things_in_dimension(self, dimension):
        qrystr = "SELECT thing, place FROM location WHERE dimension=?;"
        self.readcursor.execute(qrystr, (dimension,))
        td = self.thingdict
        pcd = self.placecontentsdict
        for d in [td, pcd]:
            if dimension not in d:
                d[dimension] = {}
        for row in self.readcursor:
            (name, location) = row
            thing = Thing(dimension, name, location)
            td[dimension][name] = thing
            if location not in pcd[dimension]:
                pcd[dimension][location] = []
            pcd[dimension][location].append(thing)

    def load_portals_in_dimension(self, dimension):
        qrystr = "SELECT name, from_place, to_place FROM portal "\
                 "WHERE dimension=?;"
        self.readcursor.execute(qrystr, (dimension,))
        for row in self.readcursor:
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
        self.readcursor.execute(qrystr, (dimension,))
        container = self.containerdict
        contents = self.contentsdict
        if dimension not in container:
            container[dimension] = {}
        if dimension not in contents:
            contents[dimension] = {}
        for row in self.readcursor:
            (inside, outside) = row
            container[dimension][inside] = outside
            if outside not in contents[dimension]:
                contents[dimension][outside] = []
            contents[dimension][outside].append(inside)

    def load_spots_for_board(self, dimension):
        qrystr = "SELECT place, img, x, y "\
                 "FROM spot WHERE dimension=?;"
        self.readcursor.execute(qrystr, (dimension,))
        sd = self.spotdict
        if dimension not in sd:
            sd[dimension] = {}
        for row in self.readcursor:
            (place, img, x, y) = row
            self.imgs2load.append(img)
            spot = Spot(dimension, place, img, x, y)
            sd[dimension][place] = spot

    def load_pawns_for_board(self, dimension):
        qrystr = "SELECT dimension, thing, img "\
                 "FROM pawn WHERE dimension=?;"
        self.readcursor.execute(qrystr, (dimension,))
        pd = self.pawndict
        if dimension not in pd:
            pd[dimension] = {}
        for row in self.readcursor:
            (dimension, thing, img) = row
            self.imgs2load.append(img)
            place = self.thingdict[dimension][thing].location
            pawn = Pawn(dimension, thing, place, img)
            pd[dimension][thing] = pawn

    def load_imgs(self):
        qm = ["?"] * len(self.imgs2load)
        qrystr = "SELECT name, path, rltile FROM img WHERE name IN (" +\
                 ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, self.imgs2load)
        regular = []
        rltile = []
        for row in self.readcursor:
            if row[2]:
                rltile.append(row)
            else:
                regular.append(row)
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
        self.readcursor.execute(qrystr, (dimension,))
        if dimension not in self.journeydict:
            self.journeydict[dimension] = {}
        for row in self.readcursor:
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

db = Database(":memory:", default.stubs)
db.mkschema()
db.insert_defaults()
db.load_board('Physical')
print db.boarddict['Physical']
