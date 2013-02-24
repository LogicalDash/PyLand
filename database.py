import sqlite3
from place import Place
from portal import Portal
from widgets import Color, MenuItem, Menu, Spot, Pawn, Board, Style
from thing import Thing
from attrcheck import LowerBoundCheck, UpperBoundCheck, \
    TypeCheck, ListCheck, AttrCheck
from graph import Dimension, Map, Route
from pyglet.resource import image
from parms import tabs

defaultCommit = True
testDB = True


def untuple(tuplist):
    r = []
    for tup in tuplist:
        r += list(tup)
    return r


def valuesrow(n):
    if n < 1:
        return
    elif n == 1:
        return '(?)'
    else:
        left = '('
        mid = '?, ' * (n - 1)
        right = '?)'
        return left+mid+right


def valuesrows(x, y):
    return ', '.join([valuesrow(x) for i in xrange(0, y)])


def valuesins(tab, x, y):
    return "insert into " + tab + " values " + valuesrows(x, y) + ";"


def valuesknow(tab, keyexp, x, y):
    return "select count(*) from " + tab + " where " + \
        keyexp + " in (" + valuesrows(x, y) + ");"


def valuesget(tab, keynames, valnames, y):
    qm_in = ["?"] * len(keynames)
    qm_mid = "(" + ", ".join(qm_in) + ")"
    qm_out = [qm_mid] * y
    return "select " + ", ".join(keynames+valnames) + " from " + tab +\
        " where (" + ", ".join(keynames) + ") in (" + ", ".join(qm_out) + ");"


def haskeytup(dic, tup):
    i = 0
    lookup = dic
    while i < len(tup):
        try:
            lookup = lookup[tup[i]]
            i += 1
        except KeyError:
            return False
    return True


class Database:
    """Method naming conventions:

    mksomething(...) means write a record for a new entity

    updsomething(...) means update the record for an entity--blithely
    assuming it exists

    syncsomething(...) takes a something object; puts it into the
    appropriate dictionary if it's not there; or if it is, and the
    existing something object in the dictionary is not the same as the
    one supplied, then it is made so. If the something object has been
    added or changed, it goes into self.altered to be written to
    database later. The exception is if there's no record by that name
    in the database yet, in which case it goes into self.new.

    I'm not sure I really need syncsomething. I figured I'd use it
    when replacing old items with new, or when I'm not sure I've
    created an item already, but both of those cases are covered if I
    only ever create things thru the DB.

    modsomething(...) exists only when there's no something class for
    syncsomething to sync. It's like updsomething, but for stuff in
    RAM.

    This I can see a clear use for, at least in the case of
    modcontainment. When I change something's location, I want to
    update the dictionaries in the database as well.

    writesomething(...) calls mksomething or updsomething depending on
    whether or not an entity already exists in the database. As
    arguments it takes the same things that mksomething does.

    savesomething(...) takes a Python object of one of the game's
    classes as its first argument, and calls writesomething with
    arguments taken from the appropriate attributes of the Python
    object.

    loadsomething(...) fetches data from the database, constructs an
    appropriate Python object out of it, puts the object in
    somethingmap, and returns the object. Widgets can only be loaded
    if the wf attribute is set to the appropriate WidgetFactory.

    getsomething(...) fetches and returns an object from somethingmap
    if possible. But if somethingmap doesn't have it, get it from
    loadsomething instead.

    knowsomething(...) checks to see if the database has a record with
    the given information

    havesomething(...) takes a Python object and calls knowsomething
    with the appropriate attributes. It only exists if the table
    called something stores data for Python objects.

    delsomething(...) takes only what's necessary to identify
    something, and deletes the thing from the database and from the
    dictionaries.

    cullsomething(...) takes a partial key and a list of somethings,
    and deletes those somethings that match the partial key but aren't
    in the list.

    """

    def __init__(self, dbfile, xfuncs={}, defaultCommit=True):
        self.conn = sqlite3.connect(dbfile)
        self.readcursor = self.conn.cursor()
        self.writecursor = self.conn.cursor()
        self.altered = []
        self.placedict = {}
        self.portaldict = {}
        self.portalorigdestdict = {}
        self.portaldestorigdict = {}
        self.thingdict = {}
        self.spotdict = {}
        self.imgdict = {}
        self.dimdict = {}
        self.attributiondict = {}
        self.attrcheckdict = {}
        self.mapdict = {}
        self.boarddict = {}
        self.menudict = {}
        self.menuitemdict = {}
        self.pawndict = {}
        self.styledict = {}
        self.colordict = {}
        self.contained_in = {}  # This maps strings to other strings,
                                # not to Python objects.
        self.contents = {}  # ditto
        self.contents2 = {}
        # self.contents2 uses the container name as the first key, and then
        # the dimension name. This is pretty much only used for the
        # loadmanyplace method. I'd like to get rid of it...
        # self.func his maps strings to functions,
        # giving a user with access to the database the ability to
        # call that function. Not sure how yet.
        self.func = {'saveplace': self.saveplace,
                     'getplace': self.getplace,
                     'savething': self.savething,
                     'getthing': self.getthing,
                     'getitem': self.getitem,
                     'getattribute': self.getattribute,
                     'saveattribute': self.saveattribute,
                     'writeattribute': self.writeattribute}
        self.typ = {'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool}
        self.saver = {}
        self.func.update(xfuncs)

    def __del__(self):
        self.readcursor.close()
        self.writecursor.close()
        self.conn.commit()
        self.conn.close()

    def _remember_place(self, place):
        if place.dimension not in self.placedict:
            self.placedict[place.dimension] = {}
        self.placedict[place.dimension][place.name] = place

    def _remember_thing(self, thing):
        if thing.dimension not in self.thingdict:
            self.thingdict[thing.dimensios] = {}
        self.thingdict[thing.dimension][thing.name] = thing

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

    def insert_defaults(self, default, commit=defaultCommit):
        def f(tups):
            return [n[0] + n[1] for n in tups]
        self.mkmanycolor(f(default.colors), commit=False)
        self.mkmanystyle(f(default.styles), commit=False)
        self.mkmanymenu(f(default.menus), commit=False)
        self.mkmanymenuitem(f(default.menuitems), commit=False)
        self.mkdimension('Physical', commit=False)
        self.mkmap('Default', 'Physical', commit=False)
        self.mkmanyplace(f(default.places), commit=False)
        self.mkmanyportal(f(default.portals), commit=False)
        self.mkmanything(f(default.things), commit=False)
        self.mkmanyattribute(f(default.attributes), commit=False)
        self.mkmanyattribution(f(default.attributions), commit=False)
        self.mkimg('defaultwall', 'wallpape.jpg', commit=False)
        self.mkboard('Default', 800, 600, 'defaultwall', commit=False)
        if commit:
            self.conn.commit()

    def mkmany(self, tname, valtups, commit=defaultCommit):
        querystr = valuesins(tname, len(valtups[0]), len(valtups))
        vals = untuple(valtups)
        self.writecursor.execute(querystr, vals)
        if commit:
            self.conn.commit()

    def knowany(self, tname, keyexp, keytups):
        querystr = valuesknow(tname, keyexp, len(keytups[0]), len(keytups))
        keys = untuple(keytups)
        self.readcursor.execute(querystr, keys)
        r = self.readcursor.fetchone()
        if r in [None, []]:
            return False
        elif r[0] == 0:
            return False
        else:
            return True

    def knowall(self, tname, keyexp, keytups):
        numkeys = len(keytups)
        keylen = len(keytups[0])
        querystr = valuesknow(tname, keyexp, keylen, numkeys)
        keys = untuple(keytups)
        self.readcursor.execute(querystr, keys)
        r = self.readcursor.fetchone()
        if r in [None, []]:
            return False
        elif r[0] == numkeys:
            return True
        else:
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
        elif isinstance(obj, Map):
            self.mapdict[obj.name] = obj
        else:
            raise Exception("I have nowhere to put this!")
        self.altered.append(obj)

        def sync(self):
            "Call this to write all altered objects to the database on disk."
            for clas in self.saver.keys():
                checked = []
                clasobjs = []
                while len(self.altered) > 0:
                    altered = self.altered.pop()
                    if isinstance(altered, clas):
                        clasobjs.append(altered)
                    else:
                        checked.append(altered)
                self.altered = checked
                saver = self.manysaver[clas]
                saver(clasobjs, commit=False)
            if len(altered) > 0:
                raise Exception("While syncing, found some altered objects "
                                "that I don't know how to save.")
                self.conn.rollback()
            else:
                self.conn.commit()

    def knowdimension(self, name):
        qrystr = "select count(*) from dimension where name=? limit 1;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def havedimension(self, dim):
        return self.knowdimension(dim.name)

    def mkdimension(self, name, commit=defaultCommit):
        self.writecursor.execute("insert into dimension values (?);", (name,))
        if commit:
            self.conn.commit()

    def mkmanydimension(self, names, commit=defaultCommit):
        tups = [(name,) for name in names]
        self.mkmany("dimension", ("name"), tups, commit=False)
        if commit:
            self.conn.commit()

    def knowplace(self, name):
        self.readcursor.execute("select count(*) from place where name=?;",
                                (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowsomeplace(self, keytups):
        return self.knowany("place", "(name)", keytups)

    def knowsomeplaces(self, keytups):
        return self.knowsomeplace(keytups)

    def knowallplace(self, keytups):
        return self.knowall("place", "(name)", keytups)

    def knowallplaces(self, keytups):
        return self.knowallplace(keytups)

    def haveplace(self, place):
        return self.knowplace(place.name)

    def mkplace(self, dimension, place, commit=defaultCommit):
        qrystr = "insert into item values (?, ?);"
        qrytup = (dimension, place)
        self.writecursor.execute(qrystr, qrytup)
        qrystr = "insert into place values (?, ?);"
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanyplace(self, tups, commit=defaultCommit):
        self.mkmany("item", ("dimension", "name"), tups, commit=False)
        self.mkmany("place", ("dimension", "name"), tups, commit=False)
        if commit:
            self.conn.commit()

    def loadplace(self, dim, name):
        contents = self.getcontents(dim, name)
        portals = self.getportalsfrom(dim, name)
        place = Place(dim, name, contents, portals)
        self._remember_place(place)
        return place

    def loadmanyplace(self, tups):
        """Assume that each of the given tuples represents the primary key of
a Place. Load everything in the Place, and every attribute it
has. Return a 2-dimensional dictionary mapping names and dimensions to
Place objects.

        """
        # Also, update the placedict
        self.loadcontentsofmany(tups)
        self.loadportalsfrommany(tups)
        r = {}
        for tup in tups:
            (dim, name) = tup
            if dim not in r:
                r[dim] = {}
            conts = self.contents[dim][name]
            ports = self.portalorigdestdict[dim][name]
            pl = Place(dim, name, conts, ports)
            r[dim][name] = pl
        self.placedict.update(r)
        return r

    def knowthing(self, dimension, name):
        self.readcursor.execute("select count(*) from thing where name=?;",
                                (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanything(self, tups):
        return self.knowany("thing", "(dimension, name)", tups)

    def knowallthing(self, tups):
        return self.knowall("thing", "(dimension, name)", tups)

    def havething(self, thing):
        return self.knowthing(thing.dimension, thing.name)

    def mkthing(self, dimension, name, commit=defaultCommit):
        qrystr = "insert into item values (?, ?);"
        self.writecursor.execute(qrystr, (dimension, name))
        qrystr = "insert into thing values (?, ?);"
        self.writecursor.execute(qrystr, (dimension, name))
        if commit:
            self.conn.commit()

    def mkmanything(self, thingtups, commit=defaultCommit):
        self.mkmany("item", ("dimension", "name"), thingtups, commit=False)
        self.mkmany("thing", ("dimension", "name"), thingtups, commit=False)
        if commit:
            self.conn.commit()

    def writething(self, dimension, name, commit=defaultCommit):
        if not self.knowthing(dimension, name):
            self.mkthing(dimension, name, commit)

    def loadthing(self, dimension, name):
        loc = self.getcontainer(dimension, name)
        cont = self.getcontents(dimension, name)
        th = Thing(dimension, name, loc, cont)
        self._remember_thing(th)
        return th

    def loadmanything(self, tups):
        """Assume that each of the given tuples represents the primary key of a
Thing. Load the given Things. Return a 2-dimensional dictionary
mapping names and dimensions to Place objects.

        """
        self.loadmanycontainer(tups)
        self.loadcontentsofmany(tups)
        r = {}
        for tup in tups:
            (dim, name) = tup
            loc = self.getcontainer(dim, name)
            conts = self.getcontents(dim, name)
            if dim not in r:
                r[dim] = {}
            th = Thing(dim, name, loc, conts)
            r[dim][name] = th
        self.thingdict.update(r)
        return r

    def getthing(self, dimension, name):
        if dimension in self.thingdict and name in self.thingdict[dimension]:
            return self.thingdict[dimension][name]
        else:
            return self.loadthing(dimension, name)

    def getmanything(self, tups):
        unloaded = []
        for tup in tups:
            (dim, name) = tup
            if dim not in self.thingdict or name not in self.thingdict[dim]:
                unloaded.append(tup)
        self.loadmanything(unloaded)
        r = {}
        for tup in tups:
            (dim, name) = tup
            if dim not in r:
                r[dim] = {}
            r[dim][name] = self.thingdict[dim][name]
        return r

    def knowitem(self, dimension, name):
        return self.knowthing(dimension, name) or \
            self.knowplace(dimension, name) or \
            self.knowportal(dimension, name)

    def loaditem(self, dimension, name):
        if self.knowthing(dimension, name):
            return self.loadthing(dimension, name)
        elif self.knowplace(dimension, name):
            return self.loadplace(dimension, name)
        elif self.knowportal(dimension, name):
            return self.loadportal(dimension, name)
        else:
            return None

    def getitem(self, dimension, name):
        if dimension in self.thingdict and \
           name in self.thingdict[dimension]:
            return self.thingdict[dimension][name]
        elif dimension in self.placedict and \
             name in self.placedict[dimension]:
            return self.placedict[dimension][name]
        elif dimension in self.portaldict and \
             name in self.portaldict[dimension]:
            return self.portaldict[dimension][name]
        else:
            return self.loaditem(dimension, name)

    def getcontents(self, dimension, container):
        if dimension not in self.contents or\
           container not in self.contents[dimension]:
            return self.loadcontents(dimension, container)
        else:
            return self.contents[dimension][container]

    def cullcontainment(self, dimension, container, keeps=[],
                        commit=defaultCommit):
        if len(keeps) == 0:
            qrystr = "delete from containment where "\
                     "dimension=? and container=?;"
            qrytup = (dimension, container)
            self.writecursor.execute(qrystr, qrytup)
        else:
            qm = ["(?, ?)"] * len(keeps)
            qrystr = "delete from containment where "\
                     "dimension=? and container=? and "\
                     "(dimension, contained) not in (" + ", ".join(qm) + ");"
            qrylst = [dimension, container] + untuple(keeps)
            self.writecursor.execute(qrystr, qrylst)
        if commit:
            self.conn.commit()

    def knowcontents(self, dimension, container):
        qrystr = "select count(*) from containment "\
                 "where dimension=? and container=? limit 1;"
        self.readcursor.execute(qrystr, (container,))
        return self.readcursor.fetchone()[0] > 0

    def havecontents(self, container):
        return self.knowcontents(container.dimension, container.name)

    def mkcontainment(self, dimension, contained, container,
                      commit=defaultCommit):
        qrystr = "insert into containment values (?, ?, ?);"
        qrytup = (dimension, contained, container)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanycontainment(self, tups, commit=defaultCommit):
        self.mkmany("containment", ("dimension", "contained"), tups, commit)

    def updcontainment(self, dimension, contained, container,
                       commit=defaultCommit):
        qrystr = "update containment set container=? "\
                 "where dimension=? and contained=?;"
        qrytup = (container, dimension, contained)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.default.commit()

    def updcontents(self, dimension, container, contents_list,
                    commit=defaultCommit):
        qrystr = "select dimension, contained from containment "\
                 "where dimension=? and container=?;"
        qrytup = (dimension, container)
        self.readcursor.execute(qrystr, qrytup)
        already = self.readcursor.fetchall()
        delete = [contained for contained in already
                  if contained not in contents_list]
        add = [contained for contained in contents_list
               if contained not in already]
        self.deletemanycontainment(delete, commit=False)
        self.mkmanycontainment(add, commit=False)
        if commit:
            self.conn.commit()

    def writecontainment(self, dimension, contained, container,
                         commit=defaultCommit):
        if self.knowcontainment(dimension, contained):
            self.updcontainment(dimension, contained, container, commit)
        else:
            self.mkcontainment(dimension, contained, container, commit)

    def writecontents(self, dimension, container, contained_list,
                      commit=defaultCommit):
        if self.knowcontents(dimension, container):
            # I might supply a list of names of contained things
            # without the dimensions on, but then again I might pair
            # in dimensions because that's what I did elsewhere.
            if isinstance(contained_list[0], tuple):
                contents_list = contained_list
            else:
                contents_list = [(dimension, contained)
                                 for contained in contained_list]
            self.updcontents(dimension, container, contents_list, commit)
        else:
            containtups = [(dimension, container, contained)
                           for contained in contained_list]
            self.mkmanycontainment(containtups, commit)

    def savecontents(self, container, commit=defaultCommit):
        self.writecontents(container.dimension, container.name,
                           container.contents, commit)

    def knowportal(self, dimension, portal):
        qrystr = "select count(*) from portal where "\
                 "dimension=? and portal=? limit 1;"
        qrytup = (dimension, portal)
        self.readcursor.execute(qrystr, qrytup)
        return self.readcursor.fetchone()[0] == 1

    def haveportal(self, port):
        return self.knowportal(port.dimension, port.name)

    def mkportal(self, dimension, name, orig, dest,
                 commit=defaultCommit):
        qrystr = "insert into portal values (?, ?, ?, ?);"
        qrytup = (dimension, name, orig, dest)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def updportal(self, dimension, name, orig, dest,
                  commit=defaultCommit):
        qrystr = "update portal set from_place=?, to_place=? "\
                 "where dimension=? and name=?;"
        qrytup = (orig, dest, dimension, name)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def writeportal(self, dimension, name, orig, dest,
                    commit=defaultCommit):
        if self.knowportal(dimension, name):
            self.updportal(dimension, name, orig, dest, commit)
        else:
            self.mkportal(dimension, name, orig, dest, commit)

    def saveportal(self, port, commit=defaultCommit):
        self.writeportal(port.dimension, port.name,
                         port.orig.name, port.dest.name,
                         commit)

    def loadportal(self, dimension, name):
        qrystr = "select from_place, to_place from portal "\
                 "where dimension=? and name=?;"
        qrytup = (dimension, name)
        self.readcursor.execute(qrystr, qrytup)
        (orign, destn) = self.readcursor.fetchone()
        orig = self.getplace(orign)
        dest = self.getplace(destn)
        port = Portal(dimension, name, orig, dest)
        self._remember_portal(port)
        return port

    def getportal(self, dimension, name):
        if dimension in self.portaldict and \
           name in self.portaldict[dimension]:
            return self.portaldict[dimension][name]
        else:
            return self.loadportal(dimension, name)

    def delportal(self, dimension, name, commit=defaultCommit):
        if dimension in self.portaldict and name in self.portaldict[dimension]:
            port = self.portaldict[dimension][name]
            self._forget_portal(port)
        qrystr = "delete from portal where dimension=? and name=?;"
        qrytup = (dimension, name)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def knowspot(self, place):
        qrystr = "select count(*) from spot where place=?; limit 1"
        self.readcursor.execute(qrystr, (place,))
        return self.readcursor.fetchone()[0] > 0

    def knowanyspot(self, tups):
        return self.knowany("spot", "(place)", tups)

    def knowallspot(self, tups):
        return self.knowall("spot", "(place)", tups)

    def havespot(self, place):
        if place in self.spotdict:
            return True
        else:
            return self.knowspot(place.name)

    def mkspot(self, place, board, x, y, r, commit=defaultCommit):
        self.writecursor.execute("insert into spot values (?, ?, ?, ?);",
                                 (place, board, x, y, r))
        if commit:
            self.conn.commit()

    def mkmanyspot(self, tups, commit=defaultCommit):
        self.mkmany("spot", tups, commit)

    def updspot(self, place, board, x, y, r, commit=defaultCommit):
        qrystr = "update spot set x=?, y=?, r=? where place=? and board=?;"
        self.writecursor.execute(qrystr, (x, y, r, place, board))
        if commit:
            self.conn.commit()

    def writespot(self, place, x, y, r, commit=defaultCommit):
        if self.knowspot(place):
            self.updspot(place, x, y, r, commit)
        else:
            self.mkspot(place, x, y, r, commit)

    def savespot(self, spot, commit=defaultCommit):
        self.writespot(spot.place.name, spot.x, spot.y, spot.r, commit)
        self.new.remove(spot)
        self.altered.remove(spot)

    def loadspot(self, placen, boardn):
        qrystr = "select x, y, r from spot where place=? and board=?;"
        self.readcursor.execute(qrystr, (placen, boardn))
        spottup = (self.getplace(placen),
                   self.getboard(boardn)) + self.readcursor.fetchone()
        spot = Spot(*spottup)
        if boardn not in self.spotdict:
            self.spotdict[boardn] = {}
        self.spotdict[boardn][placen] = spot
        return spot

    def loadmanyspot(self, placeboards):
        qrystr = valuesget("spot", ("place", "board"), ("x", "y", "r"),
                           len(placeboards))
        self.readcursor.execute(qrystr, placeboards)
        r = {}
        for row in self.readcursor:
            (place, board, x, y, r) = row
            spot = Spot(*row)
            if board not in r:
                r[board] = {}
            r[board][place] = spot
            self.spotdict[board][place] = spot
        return r

    def getspot(self, placen, boardn):
        if boardn in self.spotdict and placen in self.spotdict[boardn]:
            return self.spotdict[boardn][placen]
        else:
            return self.loadspot(placen, boardn)

    def getmanyspot(self, placeboards):
        loaded = []
        unloaded = []
        for placeboard in placeboards:
            (place, board) = placeboard
            if board in self.spotdict and place in self.spotdict[board]:
                loaded.append(placeboard)
            else:
                unloaded.append(placeboard)
        r = {}
        for placeboard in loaded:
            (place, board) = placeboard
            spot = self.spotdict[board][place]
            if board not in r:
                r[board] = {}
            r[board][place] = spot
        r.update(self.loadmanyspot(unloaded))
        return r

    def delspot(self, place, commit=defaultCommit):
        self.writecursor.execute("delete from spot where place=?;", (place,))
        if commit:
            self.conn.commit()

    def knowimg(self, name):
        qrystr = "select count(*) from img where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanyimg(self, tups):
        return self.knowany("img", "(name)", tups)

    def knowallimg(self, tups):
        return self.knowall("img", "(name)", tups)

    def haveimg(self, img):
        return self.knowimg(img.name)

    def mkimg(self, name, path, rl=False, commit=defaultCommit):
        qrystr = "insert into img values (?, ?, ?);"
        self.writecursor.execute(qrystr, (name, path, rl))
        if commit:
            self.conn.commit()

    def mkmanyimg(self, tups, commit=defaultCommit):
        self.mkmany("img", tups)

    def updimg(self, name, path, rl=False, commit=defaultCommit):
        qrystr = "update img set path=?, rltile=? where name=?;"
        self.writecursor.execute(qrystr, (path, rl, name))
        if commit:
            self.conn.commit()

    def writeimg(self, name, path, rl=False, commit=defaultCommit):
        if self.knowimg(name):
            self.updimg(name, path, rl, commit)
        else:
            self.mkimg(name, path, rl, commit)

    def loadrltile(self, name, path):
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

    def loadimgfile(self, name, path):
        tex = image(path).get_image_data().get_texture()
        tex.name = name
        self.imgdict[name] = tex
        return tex

    def loadimg(self, name):
        self.readcursor.execute("select * from img where name=?", (name,))
        row = self.readcursor.fetchone()
        if row is None:
            return
        elif row[2]:
            return self.loadrltile(name, row[1])
        else:
            return self.loadimgfile(name, row[1])

    def loadmanyimg(self, names):
        qrystr = valuesget("img", ("name"), ("path", "rltile"), len(names))
        self.readcursor.execute(qrystr, names)
        r = {}
        for row in self.readcursor:
            name = row[0]
            if row[2]:
                r[name] = self.loadrltile(name, row[1])
            else:
                r[name] = self.loadimgfile(name, row[1])
        return r

    def getimg(self, name):
        if name in self.imgdict:
            return self.imgdict[name]
        else:
            return self.loadimg(name)

    def getmanyimg(self, names):
        loaded = []
        unloaded = []
        for name in names:
            if name in self.imgdict:
                loaded.append(name)
            else:
                unloaded.append(name)
        r = {}
        for name in loaded:
            r[name] = self.imgdict[name]
        r.update(self.loadmanyimg(names))
        return r

    def delimg(self, name, commit=defaultCommit):
        if name in self.imgdict:
            del self.imgdict[name]
        self.writecursor.execute("delete from img where name=?;", (name,))
        if commit:
            self.conn.commit()

    def cullimgs(self, keeps, commit=defaultCommit):
        keeps = self.imgdict.keys()
        qm = ["?"] * len(keeps)
        qrystr = "delete from img where name not in ("
        qrystr += ", ".join(qm) + ");"
        self.writecursor.execute(qrystr, keeps)
        if commit:
            self.conn.commit()

    def mkmenuitem(self, menuname, idx, text, onclick, closer=True,
                   commit=defaultCommit):
        qrystr = "insert into menuitem values (?, ?, ?, ?, ?);"
        qrytup = (menuname, idx, text, onclick, closer)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanymenuitem(self, mitup, commit=defaultCommit):
        self.mkmany("menuitem", mitup, commit)

    def knowmenuitem(self, menuname, idx):
        qrystr = "select count(*) from menuitem where menu=? "\
                 "and idx=? limit 1;"
        self.readcursor.execute(qrystr, (menuname, idx))
        return self.readcursor.fetchone()[0] == 1

    def knowanymenuitem(self, pairs):
        return self.knowany("menuitem", "(menu, idx)", pairs)

    def knowallmenuitem(self, pairs):
        return self.knowall("menuitem", "(menu, idx)", pairs)

    def havemenuitem(self, menuitem):
        return self.knowmenuitem(menuitem.menuname, menuitem.i)

    def updmenuitem(self, menuname, idx, text, onclick, closer,
                    commit=defaultCommit):
        qrystr = "update menuitem set text=?, onclick=?, closer=? "\
                 "where menu=? and idx=?;"
        qrytup = (text, onclick, closer, menuname, idx)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def writemenuitem(self, menu, i, text, onclick, closer=True,
                      commit=defaultCommit):
        if self.knowmenuitem(menu, i):
            self.updmenuitem(menu, i, text, onclick, closer, commit)
        else:
            self.mkmenuitem(menu, i, text, onclick, closer, commit)

    def loadmenuitem(self, menuname, idx):
        qrystr = "select text, onclick, closer from menuitem "\
                 "where menu=? and idx=?;"
        self.readcursor.execute(qrystr, (menuname, idx))
        (text, onclick, closer) = self.readcursor.fetchone()
        menuitem = MenuItem(menuname, idx, text, onclick, closer)
        if menuname not in self.menuitemdict:
            self.menuitemdict[menuname] = {}
        self.menuitemdict[menuname][idx] = menuitem
        return menuitem

    def loadmanymenuitem(self, nameidx):
        qrystr = valuesget("menuitem", ("menu", "idx"),
                           ("text", "onclick", "closer"), len(nameidx))
        self.readcursor.execute(qrystr, nameidx)
        r = {}
        for row in self.readcursor:
            (menu, idx, text, onclick, closer) = row
            mi = MenuItem(*row)
            if menu not in r:
                r[menu] = {}
            if menu not in self.menuitemdict:
                self.menuitemdict[menu] = {}
            r[menu][idx] = mi
            self.menuitemdict[menu][idx] = mi
        return r

    def getmenuitem(self, menuname, idx):
        if menuname in self.menuitemdict:
            if idx in self.menuitemdict[menuname]:
                return self.menuitemdict[menuname][idx]
            else:
                return self.loadmenuitem(menuname, idx)
        else:
            return self.loadmenuitem(menuname, idx)

    def getmanymenuitem(self, menuidx):
        loaded = []
        unloaded = []
        for item in menuidx:
            (menu, idx) = item
            if menu in self.menuitemdict and idx in self.menuitemdict[menu]:
                loaded.append(item)
            else:
                unloaded.append(item)
        r = {}
        for item in loaded:
            (menu, idx) = item
            if menu not in r:
                r[menu] = {}
            r[menu][idx] = self.menuitemdict[menu][idx]
        r.update(self.loadmanymenuitem(unloaded))
        return r

    def delmenuitem(self, menuname, i, commit=defaultCommit):
        qrystr = "delete from menuitem where menu=? and index=?;"
        if menuname in self.menuitemdict:
            if i in self.menuitemdict[menuname]:
                del self.menuitemdict[menuname][i]
        self.writecursor.execute(qrystr, (menuname, i))
        if commit:
            self.conn.commit()

    def knowmap(self, name):
        qrystr = "select count(*) from map where name=? limit 1;"
        qrytup = (name,)
        self.readcursor.execute(qrystr, qrytup)
        return self.readcursor.fetchone()[0] == 1

    def havemap(self, mp):
        return self.knowmap(mp.name)

    def mkmap(self, name, dimension, commit=defaultCommit):
        qrystr = "insert into map values (?, ?);"
        qrytup = (name, dimension)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanymap(self, maptups, commit=defaultCommit):
        self.mkmany("map", maptups, commit)

    def updmap(self, name, dimension, commit=defaultCommit):
        qrystr = "update map set dimension=? where name=?;"
        qrytup = (dimension, name)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def updmanymap(self, tups, commit=defaultCommit):
        for tup in tups:
            self.updmap(tup[0], tup[1], commit)

    def writemap(self, name, dimension, commit=defaultCommit):
        if self.knowmap(name):
            self.updmap(name, dimension, commit)
        else:
            self.mkmap(name, dimension, commit)

    def writemanymap(self, tups, commit=defaultCommit):
        for tup in tups:
            self.writemap(tup[0], tup[1], commit)

    def savemap(self, mp):
        self.savemanyplace(mp.places)
        self.savemanyportal(mp.portals)
        self.writemap(mp.name, mp.dimension)

    def loadmap(self, name):
        qrystr = "select dimension from map where name=?;"
        qrytup = (name,)
        self.readcursor.execute(qrystr, qrytup)
        dim = self.readcursor.fetchone()[0]
        qrystr = "select place from mappedness where map=?;"
        self.readcursor.execute(qrystr, qrytup)
        placerows = self.readcursor.fetchall()
        places = self.getmanyplace(untuple(placerows))
        qm = ["?"] * len(places)
        qrystr = "select name from portal where dimension=? " +\
                 "and from_place in (" + ", ".join(qm) + ");"
        qrylst = [dim] + places
        self.readcursor.execute(qrystr, qrylst)
        portalrows = self.readcursor.fetchall()
        portals = self.getmanyportal(untuple(portalrows))
        mp = Map(name, self.getdimension(dim),
                 places, portals)
        self.mapdict[name] = mp
        return mp

    def loadmanymap(self, names):
        qrystr = valuesget("map", ("name",), ("dimension",), len(names))
        self.readcursor.execute(qrystr, names)
        rows = self.readcursor.fetchall()
        dims = [row[1] for row in rows]
        dimdict = self.getmanydimension(dims)
        mapdimdict = {}
        for row in rows:
            mapdimdict[row[0]] = dimdict[row[1]]
        qm = ["?"] * len(names)
        qrystr = "select map, place from mappedness where map in (" +\
                 ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, names)
        rows = self.readcursor.fetchall()
        placenames = [row[1] for row in rows]
        placedict = self.getmanyplace(placenames)
        mapplacedict = {}
        for row in rows:
            (mapn, placen) = row
            if mapn not in placedict:
                mapplacedict[mapn] = []
            mapplacedict[mapn].append(placedict[placen])
        qm = ["?"] * len(placedict)
        qrystr = "select map.name, portal.name from map join portal on " \
                 "map.dimension=portal.dimension and portal.from_place in (" +\
                 ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, placenames)
        rows = self.readcursor.fetchall()
        portnames = [row[1] for row in rows]
        portdict = self.getmanyportal(portnames)
        mapportaldict = {}
        for row in rows:
            (mapn, portn) = row
            if mapn not in mapportaldict:
                mapportaldict[mapn] = []
            mapportaldict[mapn].append(portdict[portn])
        mpdict = {}
        for name in names:
            mp = Map(name, mapdimdict[name], mapplacedict[name],
                     mapportaldict[name])
            mpdict[name] = name
            self.mapdict[name] = mp
        return mpdict

    def getmap(self, name):
        if name in self.mapdict:
            return self.mapdict[name]
        else:
            return self.loadmap(name)

    def getmanymap(self, names):
        loaded = []
        unloaded = []
        for name in names:
            if name in self.mapdict:
                loaded.append(name)
            else:
                unloaded.append(name)
        r = {}
        for name in loaded:
            r[name] = self.mapdict[name]
        r.update(self.loadmany(unloaded))
        return r

    def knowboard(self, name, w, h, wallpaper):
        qrystr = "select count(*) from board where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def haveboard(self, board):
        return self.knowboard(board.name)

    def mkboard(self, name, w, h, wallpaper, commit=defaultCommit):
        self.writecursor.execute("insert into board values (?, ?, ?, ?);",
                                 (name, w, h, wallpaper))
        if commit:
            self.conn.commit()

    def mkmanyboard(self, tups, commit=defaultCommit):
        self.mkmany("board", tups)

    def updboard(self, name, w, h, wallpaper, commit=defaultCommit):
        qrystr = "update board set width=?, height=?, wallpaper=? "\
                 "where name=?;"
        self.writecursor.execute(qrystr, (w, h, wallpaper, name))
        if commit:
            self.conn.commit()

    def writeboard(self, name, w, h, wallpaper, commit=defaultCommit):
        if self.knowboard(name):
            self.updboard(name, w, h, wallpaper, commit)
        else:
            self.mkboard(name, w, h, wallpaper, commit)

    def loadboard(self, mapname):
        qrystr = "select map, width, height, wallpaper "\
                 "from board where name=?;"
        self.readcursor.execute(qrystr, (mapname,))
        tup = self.readcursor.fetchone()
        pm = self.getplacemap(tup[0])
        wall = self.getimg(tup[3])
        board = Board(pm, tup[1], tup[2], wall)
        self.boarddict[mapname] = board
        return board

    def loadmanyboard(self, names):
        qrystr = valuesget("board", ("map"), ("width", "height", "wallpaper"),
                           len(names))
        self.readcursor.execute(qrystr, names)
        r = {}
        for row in self.readcursor:
            placemap = self.getplacemap(row[0])
            wallpape = self.getimg(row[3])
            board = Board(placemap, row[1], row[2], wallpape)
            r[row[0]] = board
            self.boarddict[row[0]] = board
        return r

    def getboard(self, name):
        if name in self.boarddict:
            return self.boarddict[name]
        else:
            return self.loadboard(name)

    def getmanyboard(self, names):
        loaded = []
        unloaded = []
        for name in names:
            if name in self.boarddict:
                loaded.append(name)
            else:
                unloaded.append(name)
        r = {}
        for name in loaded:
            r[name] = self.boarddict[name]
        r.update(self.loadmanyboard(unloaded))
        return r

    def delboard(self, name, commit=defaultCommit):
        if name in self.boarddict:
            del self.boarddict[name]
        self.writecursor.execute("delete from board where name=?;", (name,))
        if commit:
            self.conn.commit()

    def knowpawn(self, item, board=None):
        if board is None:
            qrystr = "select count(*) from pawn where thing=?;"
            self.readcursor.execute(qrystr, (item,))
        else:
            qrystr = "select count(*) from pawn where thing=? and board=?;"
            self.readcursor.execute(qrystr, (item, board))
        return self.readcursor.fetchone()[0] == 1

    def havepawn(self, pawn):
        return self.knowpawn(pawn.item, pawn.board)

    def mkpawn(self, item, board, img, spot, commit=defaultCommit):
        self.writecursor.execute("insert into pawn values (?, ?, ?, ?, ?, ?);",
                                 (item, img, board, spot))
        if commit:
            self.conn.commit()

    def mkmanypawn(self, tups, commit=defaultCommit):
        self.mkmany("pawn", tups)

    def updpawn(self, item, board, img, x, y, spot, commit=defaultCommit):
        qrystr = "update pawn set img=?, x=?, y=?, spot=? "\
                 "where thing=? and board=?;"
        self.writecursor.execute(qrystr, (img, x, y, spot, item, board))
        if commit:
            self.conn.commit()

    def writepawn(self, item, board, img, x, y, spot, commit=defaultCommit):
        if self.knowpawn(item):
            self.updpawn(item, board, img, x, y, spot, commit)
        else:
            self.mkpawn(item, board, img, x, y, spot, commit)

    def _lp(self, pawn):
        "Internal use"
        if not pawn.thing.name in self.pawndict:
            self.pawndict[pawn.thing.name] = {}
        self.pawndict[pawn.thing.name][pawn.board.name] = pawn

    def loadpawn(self, thingn, boardn):
        qrystr = "select thing, board, img, x, y, spot from pawn "\
                 "where thing=? and board=?;"
        self.readcursor.execute(qrystr, (thingn, boardn))
        pawnlst = list(self.readcursor.fetchone())
        pawnlst[0] = self.getthing(pawnlst[0])
        pawnlst[1] = self.getboard(pawnlst[1])
        pawnlst[2] = self.getimg(pawnlst[2])
        pawnlst[5] = self.getspot(pawnlst[5])
        pawn = Pawn(*pawnlst)
        self._lp(pawn)
        return pawn

    def loadmanypawn(self, thingboards):
        qrystr = valuesget("pawn", ("thing", "board"),
                           ("img", "x", "y", "spot"), len(thingboards))
        self.readcursor.execute(qrystr, thingboards)
        rows = self.readcursor.fetchall()
        things = self.getmanything([row[0] for row in rows])
        boards = self.getmanyboard([row[1] for row in rows])
        imgs = self.getmanyimg([row[2] for row in rows])
        spots = self.getmanyspot([row[5] for row in rows])
        pawns = [Pawn(things[row[0]], boards[row[1]], imgs[row[2]],
                      row[3], row[4], spots[row[5]]) for row in rows]
        r = {}
        for pawn in pawns:
            if pawn.thing.name not in r:
                r[pawn.thing.name] = {}
            r[pawn.thing.name][pawn.board.name] = pawn
            self._lp(pawn)
        return r

    def getpawn(self, itemn, boardn):
        if boardn in self.pawndict and itemn in self.pawndict[boardn]:
            return self.pawndict[boardn][itemn]
        else:
            return self.loadpawn(itemn, boardn)

    def delpawn(self, itemn, boardn, commit=defaultCommit):
        if boardn in self.pawndict and itemn in self.pawndict[boardn]:
            del self.pawndict[boardn][itemn]
        self.writecursor.execute("delete from pawn where name=?;", (itemn,))
        if commit:
            self.conn.commit()

    def cullpawns(self, commit=defaultCommit):
        keeps = self.pawndict.keys()
        left = "delete from pawn where name not in ("
        middle = "?, " * (len(keeps) - 1)
        right = "?);"
        querystr = left + middle + right
        self.writecursor.execute(querystr, keeps)
        if commit:
            self.conn.commit()

    # Graphs may be retrieved for either a board or a
    # dimension. Normally one board should represent one dimension,
    # but I'm keeping them separate because using the same object for
    # game logic and gui logic rubs me the wrong way.

    def knowroute(self, thingn):
        qrystr = "select count(*) from step where thing=? limit 1;"
        self.readcursor.execute(qrystr, (thingn,))
        return self.readcursor.fetchone()[0] == 1

    def haveroute(self, pawn):
        return self.knowroute(pawn.thing.name)

    def _route(self, thingn, destn, route):
        "Internal use"
        if thingn not in self.routedict:
            self.routedict[thingn] = {}
        self.routedict[thingn][destn] = route

    def loadroute(self, thingn, destn):
        qrystr = "select ord, progress, portal from step where thing=?"\
                 " and destination=?;"
        self.readcursor.execute(qrystr, (thingn, destn))
        rows = self.readcursor.fetchall()
        thing = self.getthing(thingn)
        dest = self.getplace(destn)
        steps = self.getmanyportal([row[2] for row in rows])
        route = Route(steps, thing, dest)
        self._route(thingn, destn, route)
        return route

    def loadmanyroute(self, tups):
        qm = ["(?, ?)"] * len(tups)
        qrystr = "select thing, destination, ord, progress, portal from step "\
                 "where (thing, destination) in (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, untuple(tups))
        rows = self.readcursor.fetchall()
        routesteps = {}
        routes = {}
        things = self.getmanything([row[0] for row in rows])
        dests = self.getmanyplace([row[1] for row in rows])
        ports = self.getmanyportal([row[4] for row in rows])
        for row in rows:
            port = ports[row[5]]
            idx = row[2]
            if row[0] not in routesteps:
                routesteps[row[0]] = {}
            if row[1] not in routesteps[row[0]]:
                routesteps[row[1]] = []
            while len(routesteps[row[0]][row[1]]) < idx:
                routesteps[row[0]][row[1]].append(None)
            routesteps[row[0]][row[1]][idx] = port
        for tup in tups:
            (thingn, destn) = tup
            steps = routesteps[thingn][destn]
            thing = things[thingn]
            dest = dests[destn]
            route = Route(thing, dest, steps)
            if thingn not in routes:
                routes[thingn] = {}
            routes[thingn][destn] = route
            self._route(thingn, destn, route)
        return routes

    def getroute(self, thingn, destn):
        if thingn in self.routedict and destn in self.routedict[thingn]:
            return self.routedict[thingn][destn]
        else:
            return self.loadroute(thingn)

    def getmanyroute(self, tups):
        unloaded = []
        for tup in tups:
            if tup[0] not in self.routedict or\
               tup[1] not in self.routedict[tup[0]]:
                unloaded.append(tup)
        self.loadmanyroute(unloaded)
        r = {}
        for tup in tups:
            (thing, dest) = tup
            if thing not in r:
                r[thing] = {}
            r[thing][dest] = self.routedict[thing][dest]
        return r

    def delroute(self, thingn, destn, commit=defaultCommit):
        qrystr = "delete from step where thing=? and destination=?;"
        if thingn in self.routedict and destn in self.routedict[thingn]:
            del self.routedict[thingn]
        self.writecursor.execute(qrystr, (thingn, destn))
        if commit:
            self.conn.commit()

    def knowcolor(self, name):
        qrystr = "select count(*) from color where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def havecolor(self, color):
        return self.knowcolor(color.name)

    def mkcolor(self, name, r, g, b, commit=defaultCommit):
        qrystr = "insert into color values (?, ?, ?, ?);"
        self.writecursor.execute(qrystr, (name, r, g, b))
        if commit:
            self.conn.commit()

    def mkmanycolor(self, colortups, commit=defaultCommit):
        self.mkmany("color", colortups, commit)

    def updcolor(self, name, r, g, b, commit=defaultCommit):
        qrystr = "update color set red=?, green=?, blue=? where name=?;"
        self.writecursor.execute(qrystr, (r, g, b, name))
        if commit:
            self.conn.commit()

    def writecolor(self, name, r, g, b, commit=defaultCommit):
        if self.knowcolor(name):
            self.updcolor(name, r, g, b, commit)
        else:
            self.mkcolor(name, r, g, b, commit)

    def savecolor(self, color, commit=defaultCommit):
        self.writecolor(color.name, color.red, color.green, color.blue)
        if commit:
            self.conn.commit()

    def loadcolor(self, name):
        qrystr = "select name, red, green, blue from color where name=?;"
        self.readcursor.execute(qrystr, (name,))
        color = Color(*self.readcursor.fetchone())
        color.name = name
        self.colordict[name] = color
        return color

    def loadmanycolor(self, names):
        qm = ["?"] * len(names)
        qrystr = "select name, red, green, blue from color "\
                 "where name in (" + qm + ");"
        self.readcursor.execute(qrystr, names)
        r = {}
        for row in self.readcursor:
            col = Color(*row)
            r[row[0]] = col
            self.colordict[row[0]] = col
        return r

    def getcolor(self, name):
        if name in self.colordict:
            return self.colordict[name]
        else:
            return self.loadcolor(name)

    def getmanycolor(self, names):
        unloaded = []
        for name in names:
            if name not in self.colordict:
                unloaded.append(name)
        self.loadmanycolor(unloaded)
        r = {}
        for name in names:
            r[name] = self.colordict[name]

    def delcolor(self, name, commit=defaultCommit):
        if name in self.colordict:
            del self.colordict[name]
        self.writecursor.execute("delete from color where name=?;", (name,))
        if commit:
            self.conn.commit()

    def knowstyle(self, name):
        qrystr = "select count(*) from style where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def havestyle(self, style):
        return self.knowstyle(style.name)

    def mkstyle(self, name, fontface, fontsize, spacing,
                bg_inactive, bg_active, fg_inactive, fg_active,
                commit=defaultCommit):
        qrystr = "insert into style values (?, ?, ?, ?, ?, ?, ?, ?);"
        qrytup = (name, fontface, fontsize, spacing, bg_inactive, bg_active,
                  fg_inactive, fg_active)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanystyle(self, styletups, commit=defaultCommit):
        self.mkmany("style", styletups, commit)

    def updstyle(self, name, fontface, fontsize, spacing,
                 bg_inactive, bg_active, fg_inactive, fg_active,
                 commit=defaultCommit):
        qrystr = "update style set fontface=?, fontsize=?, spacing=?, "\
                 "bg_inactive=?, bg_active=?, fg_inactive=?, fg_active=? "\
                 "where name=?;"
        qrytup = (fontface, fontsize, spacing, bg_inactive, bg_active,
                  fg_inactive, fg_active, name)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def writestyle(self, name, fontface, fontsize, spacing,
                   bg_inactive, bg_active, fg_inactive, fg_active,
                   commit=defaultCommit):
        if self.knowstyle(name):
            self.updstyle(name, fontface, fontsize, spacing, bg_inactive,
                          bg_active, fg_inactive, fg_active, commit)
        else:
            self.mkstyle(name, fontface, fontsize, spacing, bg_inactive,
                         bg_active, fg_inactive, fg_active, commit)

    def savestyle(self, style, commit=defaultCommit):
        self.writestyle(style.name, style.fontface, style.fontsize,
                        style.spacing, style.bg_inactive.name,
                        style.bg_active.name, style.fg_inactive.name,
                        style.fg_active.name, commit)

    def loadstyle(self, name):
        qrystr = "select fontface, fontsize, spacing, "\
                 "bg_inactive, bg_active, fg_inactive, fg_active "\
                 "from style where name=?;"
        if not self.knowstyle(name):
            raise ValueError("No such style: %s" % name)
        self.readcursor.execute(qrystr, (name,))
        (ff, fs, s, bg_i, bg_a, fg_i, fg_a) = self.readcursor.fetchone()
        sty = Style(name, ff, fs, s, self.getcolor(bg_i),
                    self.getcolor(bg_a), self.getcolor(fg_i),
                    self.getcolor(fg_a))
        self.styledict[name] = sty
        return sty

    def loadmanystyle(self, names):
        qm = ["?"] * len(names)
        qrystr = "select name, fontface, fontsize, spacing, "\
                 "bg_inactive, bg_active, fg_inactive, fg_active "\
                 "from style where name in (" + ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, names)
        rows = self.readcursor.fetchall()
        colors = untuple([row[4:] for row in rows])
        self.loadmanycolor(colors)
        r = {}
        for row in rows:
            (name, ff, fs, s, bg_i, bg_a, fg_i, fg_a) = row
            sty = Style(name, ff, fs, s, self.getcolor(bg_i),
                        self.getcolor(bg_a), self.getcolor(fg_i),
                        self.getcolor(fg_a))
            r[name] = sty
            self.styledict[name] = sty
        return r

    def getstyle(self, name):
        if name in self.styledict:
            return self.styledict[name]
        else:
            return self.loadstyle(name)

    def getmanystyle(self, names):
        unloaded = []
        for name in names:
            if name not in self.styledict:
                unloaded.append(name)
        self.loadmanystyle(unloaded)
        r = {}
        for name in names:
            r[name] = self.stylemap[name]
        return r

    def delstyle(self, name):
        qrystr = "delete from style where name=?;"
        if name in self.styledict:
            del self.styledict[name]
        if self.knowstyle(name):
            self.writecursor.execute(qrystr, (name,))

    def knowmenu(self, name):
        qrystr = "select count(*) from menu where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanymenu(self, tups):
        return self.knowany("menu", "(name)", tups)

    def knowallmenu(self, tups):
        return self.knowall("menu", "(name)", tups)

    def havemenu(self, menu):
        return self.knowmenu(menu.name)

    def mkmenu(self, name, x, y, w, h, sty, dv=False, commit=defaultCommit):
        # mkplace et al. will insert multiple values for their contents
        # if they are supplied. To make this work similarly I should
        # take a style object for sty, rather than a string,
        # and insert all the colors before writing the menu w. style name.
        # But I kind of like this simpler way.
        qrystr = "insert into menu values (?, ?, ?, ?, ?, ?, ?);"
        qrytup = (name, x, y, w, h, sty, dv)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def mkmanymenu(self, menutups, commit=defaultCommit):
        self.mkmany("menu", menutups)

    def updmenu(self, name, x, y, w, h, sty, commit=defaultCommit):
        # you may not change the default-visibility after making the menu
        qrystr = "update menu set x=?, y=?, width=?, height=?, style=? "\
                 "where name=?;"
        qrytup = (x, y, w, h, sty, name)
        self.writecursor.execute(qrystr, qrytup)
        if commit:
            self.conn.commit()

    def writemenu(self, name, x, y, w, h, sty, vis, commit=defaultCommit):
        if self.knowmenu(name):
            self.updmenu(name, x, y, w, h, sty, commit)
        else:
            self.mkmenu(name, x, y, w, h, sty, vis, commit)

    def savemenu(self, menu, commit=defaultCommit):
        self.savestyle(menu.style)
        self.writemenu(menu.name, menu.getleft(), menu.getbot(),
                       menu.getwidth(), menu.getheight(), menu.style.name,
                       menu.visible, commit)
        self.new.remove(menu)
        self.altered.remove(menu)

    def loadmenu(self, name):
        qrystr = "select name, x, y, width, height, style, visible "\
                 "from menu where name=?;"
        if not self.knowmenu(name):
            raise ValueError("Menu does not exist: %s" % name)
        self.readcursor.execute(qrystr, (name,))
        row = list(self.readcursor.fetchone())
        row[5] = self.getstyle(row[5])
        menu = Menu(*row)
        self.menudict[name] = menu
        return menu

    def loadmanymenu(self, names):
        qm = ["?"] * len(names)
        qrystr = "select name, x, y, width, height, style, visible "\
                 "from menu where name in (" +\
                 ", ".join(qm) + ");"
        self.readcursor.execute(qrystr, names)
        rows = self.readcursor.fetchall()
        styles = [row[5] for row in rows]
        self.loadmanystyle(styles)
        r = {}
        for row in rows:
            (name, x, y, width, height, style, visible) = row
            style = self.getstyle(style)
            menu = Menu(name, x, y, width, height, style, visible)
            r[name] = menu
            self.menudict[name] = menu
        return r

    def getmenu(self, name):
        if name in self.menudict:
            return self.menudict[name]
        else:
            return self.loadmenu(name)

    def getmanymenu(self, names):
        unloaded = []
        for name in names:
            if name not in self.menudict:
                unloaded.append(name)
        self.loadmanymenu(unloaded)
        r = {}
        for name in names:
            r[name] = self.menudict[name]
        return r

    def delmenu(self, name, commit=defaultCommit):
        if name in self.menudict:
            del self.menudict[name]
        if self.knowmenu(name):
            self.writecursor.execute("delete from menu where name=?;", (name,))
        if commit:
            self.conn.commit()


if testDB:
    import unittest
    from parms import DefaultParameters
    default = DefaultParameters()

    class DatabaseTestCase(unittest.TestCase):
        def testSomething(self, db, suf, clas, keytup, valtup, testname):
            # clas is the class of object to test.  keytup is a tuple
            # of the primary key to use. valtup is a tuple of the rest
            # of the record to use. testSomething will make the record
            # for that key and those values and test that stuff done
            # with the record is correct. I've assumed that keytup
            # concatenated with valtup
            mkargs = list(keytup)+list(valtup)
            print "mkargs = " + str(mkargs)
            knower = getattr(db, 'know'+suf)
            writer = getattr(db, 'write'+suf)
            saver = getattr(db, 'save'+suf)
            killer = getattr(db, 'del'+suf)
            loader = getattr(db, 'load'+suf)
            if testname == 'make':
                writer(*mkargs)
                self.assertTrue(knower(*keytup))
            elif testname == 'save':
                obj = loader(*keytup)
                killer(*keytup)
                saver(obj)
                self.assertTrue(knower(*keytup))
            elif testname == 'get':
                obj = loader(*keytup)
                getter = getattr(db, 'get' + suf)
                writer(*mkargs)
                jbo = getter(*keytup)
                self.assertEqual(obj, jbo)
            elif testname == 'del':
                killer = getattr(db, 'del' + suf)
                writer(*mkargs)
                self.assertTrue(knower(*keytup))
                killer(*keytup)
                self.assertFalse(knower(*keytup))

        def runTest(self):
            testl = ['make', 'save', 'get', 'del', 'make']
            db = Database(":memory:", default.stubs)
            db.mkschema()

            class Attribution:
                def __init__(self, typ, perm, lo, hi):
                    self.typ = typ
                    self.perm = perm
                    self.lo = lo
                    self.hi = hi

                def __eq__(self, other):
                    return self.typ == other.typ and\
                        self.perm == other.perm and\
                        self.lo == other.lo and\
                        self.hi == other.hi

            tabkey = [('place', default.places, Place),
                      ('portal', default.portals, Portal),
                      ('thing', default.things, Thing),
                      ('color', default.colors, Color),
                      ('style', default.styles, Style),
                      ('attribute', default.attributes, AttrCheck),
                      ('attribution', default.attributions, Attribution)]
            for pair in tabkey:
                suf = pair[0]
                for val in pair[1]:
                    for test in testl:
                        print "Testing %s%s" % (test, suf)
                        self.testSomething(db, suf, pair[2],
                                           val[0], val[1], test)

    dtc = DatabaseTestCase()

    dtc.runTest()
