# Problems:
#
# The various database functions can't all be the same for every
# object class. It doesn't make sense to have an update method for
# Place, for instance, since the table only records that a place
# exists by a certain name.
import sqlite3
from place import Place
from portal import Portal
from widgets import Color, MenuItem, Menu, Spot, Pawn, Board, Style
from thing import Thing
from graph import Journey, Dimension
from pyglet.resource import image
from parms import tabs, default

defaultCommit = True


def qrystr_insert_into(self, tabname, tuplst):
    q = ["?"] * len(tuplst[0])
    qs = "(" + ", ".join(q) + ")"
    qm = [qs] * len(tuplst)
    return "INSERT INTO " + tabname + " VALUES (" + ", ".join(qm) + ");"


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
        self.dimensiondict = {}
        self.contentsdict = {}
        self.containerdict = {}
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

    def _remember_place(self, place):
        if place.dimension not in self.placedict:
            self.placedict[place.dimension] = {}
        self.placedict[place.dimension][place.name] = place

    def _forget_place(self, place):
        if place.dimension in self.placedict and\
           place.name in self.placedict[place.dimension]:
            del self.placedict[place.dimension][place.name]

    def _remember_thing(self, thing):
        if thing.dimension not in self.thingdict:
            self.thingdict[thing.dimension] = {}
        if thing.dimension not in self.placecontentsdict:
            self.placecontentsdict[thing.dimension] = {}
        if thing.location not in self.placecontentsdict[thing.dimension]:
            self.placecontentsdict[thing.dimension][thing.location] = []
        self.thingdict[thing.dimension][thing.name] = thing
        self.placecontentsdict[thing.dimension][thing.location].append(thing)

    def _forget_thing(self, thing):
        if thing.dimension in self.thingdict and\
           thing.name in self.thingdict[thing.dimension]:
            del self.thingdict[thing.dimension][thing.name]

    def _remember_portal(self, port):
        pd = self.portaldict
        podd = self.portalorigdestdict
        pdod = self.portaldestorigdict
        dictlist = [pd, podd, pdod]
        for d in dictlist:
            if port.dimension not in d:
                d[port.dimension] = {}
        pd[port.dimension][port.name] = port
        podd[port.dimension][port.orig.name] = port.dest.name
        pdod[port.dimension][port.dest.name] = port.orig.name

    def _forget_portal(self, port):
        pd = self.portaldict
        podd = self.portalorigdestdict
        pdod = self.portaldestorigdict
        dim = port.dimension
        name = port.name
        orig = port.orig.name
        dest = port.dest.name
        if dim in pd and name in pd[dim]:
            del pd[dim][name]
        if dim in podd and orig in podd[dim]:
            del podd[dim][orig]
        if dim in pdod and dest in podd[dim]:
            del podd[dim][dest]

    def _remember_spot(self, spot):
        dim = spot.dimension
        place = spot.place.name
        if dim not in self.spotdict:
            self.spotdict[dim] = {}
        self.spotdict[dim][place] = spot

    def _forget_spot(self, spot):
        dim = spot.dimension
        place = spot.place.name
        sd = self.spotdict
        if dim in sd and place in sd[dim]:
            del sd[dim][place]

    def _remember_menu(self, menu):
        if menu.boardname not in self.menudict:
            self.menudict[menu.boardname] = {}
        self.menudict[menu.boardname][menu.name] = menu

    def _forget_menu(self, menu):
        if menu.boardname in self.menudict and \
           menu.name in self.menudict[menu.boardname]:
            del self.menudict[menu.boardname][menu.name]

    def _remember_menu_item(self, mi):
        if mi.boardname not in self.menuitemdict:
            self.menuitemdict[mi.boardname] = {}
        if mi.menuname in self.menuitemdict[mi.boardname]:
            milist = self.menuitemdict[mi.boardname][mi.menuname]
            if len(milist) < mi.idx:
                nones = [None] * (mi.idx - len(milist))
                milist.extend(nones)
                milist.append(mi)
            else:
                milist[mi.idx] = mi
        else:
            milist = [None] * mi.idx
            milist.append(mi)
            self.menuitemdict[mi.boardname][mi.menuname] = milist

    def _forget_menu_item(self, mi):
        bn = mi.boardname
        mn = mi.menuname
        idx = mi.idx
        midict = self.menuitemdict
        if bn in midict and mn in midict[bn] and len(midict[bn][mn]) >= idx:
            midict[bn][mn][idx] = None

    def _remember_containment(self, dimension, contained, container):
        if dimension not in self.containerdict:
            self.containerdict[dimension] = {}
        if dimension not in self.contentsdict:
            self.contentsdict[dimension] = {}
        if container not in self.contentsdict[dimension]:
            self.contentsdict[dimension][container] = []
        self.containerdict[dimension][contained] = container
        self.contentsdict[dimension][container].append(contained)
        # Right now there's nothing to prevent a thing containing
        # another thing twice over. Not sure if that's a problem.

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

        def insert_defaults(self, default):
            # dimensions first because a lot of other stuff requires them
            self._insert_all("dimension", default.dimensions)
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
            self._insert_all("step", default.steps)
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
            qrystr = "SELECT dimension, width, height, texture "\
                     "FROM board WHERE dimension=?;"
            qrytup = (dimension,)
            self.readcursor.execute(qrystr, qrytup)
            (dim, w, h, texname) = self.readcursor.fetchone()
            self.imgs2load = [texname]
            self.load_places_in_dimension(dimension)
            places = self.placedict[dimension].viewvalues()
            placenames = self.placedict[dimension].viewkeys()
            self.load_things_in_dimension(dimension)
            things = []
            thingnames = []
            for placename in placenames:
                thingnames_here = self.locationdict[placename]
                thingnames += thingnames_here
                for thingname in thingnames_here:
                    things.append(self.thingdict[thingname])
            self.load_portals_in_dimension(dimension)
            for place in places:
                place.portals = self.portaldict[dimension][place.name]
                place.contents = self.placecontentsdict[dimension][place.name]
            self.load_containment_in_dimension(dimension)
            for thing in things:
                thing.container = self.containerdict[dimension][thing.name]
                thing.contents = self.contentsdict[dimension][thing.name]
                thing.location = self.placedict[dimension][thing.location]
            self.load_spots_for_board(dimension)
            spots = [self.spotdict[dimension][placename]
                     for placename in placenames]
            self.load_pawns_for_board(dimension)
            pawns = [self.pawndict[dimension][thingname]
                     for thingname in thingnames]
            self.load_menus_for_board(dimension)
            menus = self.menudict[dimension].values()
            self.load_imgs()
            for spot in self.spotdict[dimension].valueiter():
                spot.img = self.imgdict[spot.img]
            for pawn in self.pawndict[dimension].valueiter():
                pawn.img = self.imgdict[pawn.img]
            texture = self.imgdict[texname]
            return Board(dim, w, h, texture, spots, pawns, menus)

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
                self._remember_color(color)
            for row in stylerows:
                (name, fontface, fontsize, spacing,
                 bg_i, bg_a, fg_i, fg_a) = row
                style = Style(name, fontface, fontsize, spacing,
                              self.colordict[bg_i],
                              self.colordict[bg_a],
                              self.colordict[fg_i],
                              self.colordict[fg_a])
                self._remember_style(style)
            menunames = []
            for row in menurows:
                (name, x, y, w, h, sty, vis) = row
                menunames.append(name)
                style = self.styledict[sty]
                menu = Menu(name, x, y, w, h, style, vis)
                self._remember_menu(menu)
            self.load_items_in_menus(menunames)

        def load_items_in_menus(self, names):
            qm = ["?"] * len(names)
            qrystr = "SELECT board, menu, idx, text, onclick, closer "\
                     "FROM menuitem JOIN boardmenu ON "\
                     "menuitem.menu=boardmenu.menu "\
                     "WHERE menuitem.menu IN (" + ", ".join(qm) + ");"
            self.readcursor.execute(qrystr, names)
            for row in self.readcursor:
                (board, menu, idx, text, fname, closer) = row
                onclick = self.func[fname]
                mi = MenuItem(board, menu, idx, text, onclick, closer)
                self._remember_menu_item(mi)

        def load_places_in_dimension(self, dimension):
            qrystr = "SELECT name FROM place WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            placetups = [(dimension, row[0]) for row in self.readcursor]
            for tup in placetups:
                place = Place(*tup)
                self._remember_place(place)

        def load_things_in_dimension(self, dimension):
            qrystr = "SELECT thing, place FROM location WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            for row in self.readcursor:
                (name, location) = row
                thing = Thing(dimension, name, location)
                self._remember_thing(thing)

        def load_portals_in_dimension(self, dimension):
            qrystr = "SELECT name, from_place, to_place FROM portal "\
                     "WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            for row in self.readcursor:
                (name, orign, destn) = row
                orig = self.placedict[dimension][orign]
                dest = self.placedict[dimension][destn]
                portal = Portal(name, orig, dest)
                self._remember_portal(portal)

        def load_containment_in_dimension(self, dimension):
            qrystr = "SELECT dimension, contained, container "\
                     "FROM containment WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            for row in self.readcursor:
                self._remember_containment(*row)

        def load_spots_for_board(self, dimension):
            qrystr = "SELECT dimension, place, img, x, y "\
                     "FROM spot WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            for row in self.readcursor:
                (dimension, place, img, x, y) = row
                place = self.placedict[dimension][place]
                self.imgs2load.append(img)
                spot = Spot(dimension, place, img, x, y)
                self._remember_spot(spot)

        def load_pawns_for_board(self, dimension):
            qrystr = "SELECT dimension, thing, img "\
                     "FROM pawn WHERE dimension=?;"
            self.readcursor.execute(qrystr, (dimension,))
            for row in self.readcursor:
                (dimension, thing, img) = row
                thing = self.thingdict[dimension][thing]
                self.imgs2load.append(img)
                pawn = Pawn(dimension, thing, img)
                self._remember_pawn(pawn)

        def load_imgs(self):
            qm = ["?"] * len(self.imgs2load)
            qrystr = "SELECT name, path, rltile FROM img WHERE name IN (" +\
                     ", ".join(qm) + ");"
            self.readcursor.execute(qrystr, self.imgs2load)
            regular = []
            rltile = []
            for row in self.readcursor:
                if row[2]:
                    rltile.append(row[0:1])
                else:
                    regular.append(row[0:1])
            for img in regular:
                self.load_regular_img(*img)
            for img in rltile:
                self.load_rltile(*img)

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
