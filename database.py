import sqlite3
from place import Place
from portal import Portal
from route import Route
from widgets import Color, MenuItem, Menu, Spot, Pawn, Board, Style
from thing import Thing
from attrcheck import LowerBoundCheck, UpperBoundCheck, \
    TypeCheck, ListCheck, AttrCheck
from graph import Dimension
from pyglet.resource import image, Image

tabs = ["""create table item (name text primary key);""",
        """create table dimension (name text primary key);""",
        """create table place (name text primary key, dimension text, foreign
key(name) references item(name), foreign key(dimension) references
dimension(name));""",
        """create table thing (name text primary key, dimension text, foreign
key(name) references item(name));""",
        """create table portal (name text primary key, dimension text, map
text, from_place text, to_place text, foreign key(name) references
item(name), foreign key(dimension) references dimension(name), foreign
key(map) references map(name), foreign key(from_place) references
place(name), foreign key(to_place) references place(name),
check(from_place<>to_place));""",
        """create table map (name text primary key, dimension text, foreign
key(dimension) references dimension(name));""",
        """create table mappedness (item text, map text, foreign key(item)
references item(name), foreign key(map) references map(name));""",
        """create table containment (dimension text, contained text, container
text, foreign key(dimension) references dimension(name), foreign
key(contained) references item(name), foreign key(container)
references item(name), check(contained<>container), primary
key(dimension, contained));""",
        """create table attribute (name text primary key, type text, lower,
upper);""",
        """create table attribution (attribute, attributed_to, value, foreign
key(attribute) references permitted_values(attribute), foreign
key(attributed_to) references item(name), foreign key(value)
references permitted_values(value), primary key(attribute,
attributed_to));""",
        """create table permitted (attribute, value, foreign key(attribute)
references attribute(name), primary key(attribute, value));""",
        """create table img (name text primary key, path, rltile);""",
        """create table board (map text primary key, width integer, height
integer, wallpaper, foreign key(map) references map(name), foreign
key(wallpaper) references image(name));""",
        """create table spot (place text, board text, x integer, y integer, r
integer, foreign key(place) references place(name), foreign key(board)
references board(name), primary key(place, board));""",
        """create table pawn (thing text, board text, img text, spot text,
foreign key(img) references img(name), foreign key(thing) references
thing(name), foreign key(spot) references spot(place), primary
key(thing, board));""",
        """create table color (name text primary key, red integer not null
check(red between 0 and 255), green integer not null check(green
between 0 and 255), blue integer not null check(blue between 0 and
255));""",
        """create table style (name text primary key, fontface text not null,
fontsize integer not null, spacing integer, bg_inactive, bg_active,
fg_inactive, fg_active, foreign key(bg_inactive) references
color(name), foreign key(bg_active) references color(name), foreign
key(fg_inactive) references color(name), foreign key(fg_active)
references color(name));""",
        """create table menu (name text primary key, x float not null, y float
not null, width float not null, height float not null, style text
default 'Default', visible boolean default 0, foreign key(style)
references style(name));""",
        """create table menuitem (menu text, idx integer, text text, onclick
text, closer boolean, foreign key(menu) references menu(name), primary
key(menu, idx));""",
        """create table step (map text, thing text, ord integer, destination
text, progress float, portal text, foreign key(map) references
map(name), foreign key(thing) references thing(name), foreign
key(portal) references portal(name), foreign key(destination)
references place(name), check(progress>=0.0), check(progress<1.0),
primary key(map, thing, ord, destination));"""]

defaultCommit = True
testDB = False


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
    # this is really ugly
    sl = ["select", " "]
    for keyname in keynames:
        sl.append(keyname)
        sl.append(", ")
    for valname in valnames:
        sl.append(valname)
        sl.append(", ")
    sl[-1] = " "
    sl += ["from", " ", tab, " ", "where", " ", "("]
    for keyname in keynames:
        sl.append(keyname)
        sl.append(", ")
    sl[-1] = ")"
    sl += [" ", "in", " "]
    val = ["("]
    for i in xrange(0, len(keynames)):
        val += ["?", ", "]
    val[-1] = ")"
    vallst = ["("]
    for i in xrange(0, y):
        vallst += val
        vallst.append(", ")
    vallst[-1] = ")"
    return "".join(sl + vallst) + ";"


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
        self.new = []
        self.altered = []
        self.placedict = {}
        self.portaldict = {}
        self.portalorigdestdict = {}
        self.portaldestorigdict = {}
        self.thingdict = {}
        self.spotdict = {}
        self.imgdict = {}
        self.dimdict = {}
        self.boarddict = {}
        self.menudict = {}
        self.menuitemdict = {}
        self.attrvaldict = {}
        self.attrcheckdict = {}
        self.pawndict = {}
        self.styledict = {}
        self.colordict = {}
        self.contained_in = {}  # This maps strings to other strings,
                                # not to Python objects.
        self.contents = {}  # ditto
        self.contents2 = {}
        # contents2 uses the container name as the first key, and then
        # the dimension name. This is pretty much only used for the
        # loadmanyplace method. I'd like to get rid of it...
        self.classdict = {Place: self.placedict,
                          Portal: self.portaldict,
                          Thing: self.thingdict,
                          Spot: self.spotdict,
                          Image: self.imgdict,
                          Dimension: self.dimdict,
                          Board: self.boarddict,
                          Menu: self.menudict,
                          MenuItem: self.menuitemdict,
                          AttrCheck: self.attrcheckdict,
                          Pawn: self.pawndict,
                          Style: self.styledict,
                          Color: self.colordict}
        # This maps strings to functions,
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
        self.func.update(xfuncs)

    def __del__(self):
        self.readcursor.close()
        self.writecursor.close()
        self.conn.commit()
        self.conn.close()

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

    def loadmany(self, tname, keyexp, valexp, keytups, clas):
        # TODO test the fuck out of this
        querystr = valuesget(tname, keyexp, valexp, len(keytups))
        keylst = untuple(keytups)
        self.readcursor.execute(querystr, keylst)
        r = []
        keylen = len(keyexp)
        for row in self.readcursor:
            # Create object of the class in question
            obj = clas(*row)
            # Get the map to store it in
            key = row[:keylen]
            m = self.classdict[clas]
            # Create the map if it doesn't exist yet
            while len(key) > 1:
                if key[0] not in m:
                    m[key[0]] = {}
                m = m[key[0]]
                key = key[1:]
            # At last, assign the key to the object
            m[key[0]] = obj
            # and put it in the list to be returned
            r.append(obj)
        return r

    def knowdimension(self, name):
        self.readcursor.execute("select count(*) from dimension where name=?;")
        return self.readcursor.fetchone()[0] == 1

    def havedimension(self, dim):
        return self.knowdimension(dim.name)

    def mkdimension(self, name, commit=defaultCommit):
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into dimension values (?);", (name,))
        if commit:
            self.conn.commit()

    def mkmanydimension(self, tups, commit=defaultCommit):
        self.mkmany("item", tups, commit=False)
        self.mkmany("dimension", tups, commit=False)
        if commit:
            self.conn.commit()

    def loaddimension(self, name):
        # fetch all the places and portals in the dimension,
        # then make the dimensio
        qrystr = "select contained from containment where container=? "\
                 "join place on name=contained;"
        self.readcursor.execute(qrystr, (name,))
        qrylst = [row[0] for row in self.readcursor.fetchall()]
        places = self.getmanyplace(qrylst)
        qrystr = "select contained from containment where container=? "\
                 "join portal on name=contained;"
        self.readcursor.execute(qrystr, (name,))
        portals = self.getmanyportal(self.readcursor)
        dimension = Dimension(name, places, portals)
        self.dimdict[name] = dimension
        return dimension

    def loadmanydimension(self, names):
        # This'll be easier if I create the Dimension objects
        # first, and then assign them places and portals.
        dimd = dict([(n, Dimension[n]) for n in names])
        # get all the places in a dimension with name in names; with
        # the name next to the place
        querystr = "select container, contained from containment "\
                   "where container in ("
        questionmarks = ["?"] * len(names)
        querystr += ", ".join(questionmarks) + ")"
        querystr += " join place on name=contained;"
        self.readcursor.execute(querystr, names)
        # get the Place of the name given in the second column, and
        # assign it to the dimension of the name given in the first
        # column
        for row in self.readcursor:
            dimd[row[0]].places.append(self.getplace(row[1]))
        # As above, for portals.
        querystr = "select container, contained from containment "\
                   "where container in ("
        querystr += ", ".join(questionmarks) + ")"
        querystr += " join portal on name=contained;"
        self.readcursor.execute(querystr, names)
        for row in self.readcursor:
            dimd[row[0]].portals.append(self.getportal(row[1]))
        self.dimdict.update(dimd)
        return dimd.itervalues()

    def getdimension(self, name):
        if name in self.dimdict:
            return self.dimdict[name]
        else:
            return self.loaddimension(name)

    def getmanydimension(self, names):
        unloaded = list(names)
        r = []
        for name in unloaded:
            if name in self.dimdict:
                dim = self.dimdict[name]
                r.append(dim)
                name = ''
        unloaded.remove('')
        r += self.loadmanydimension(unloaded)
        return r

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

    def mkplace(self, name, commit=defaultCommit):
        # Places should always exist in the database before they are
        # Python objects.
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into place values (?);", (name,))
        if commit:
            self.conn.commit()

    def mkmanyplace(self, placetups, commit=defaultCommit):
        self.mkmany("thing", placetups, commit=False)
        self.mkmany("place", placetups, commit=False)
        if commit:
            self.conn.commit()

    def writeplace(self, name, commit=defaultCommit):
        if not self.knowplace(name):
            self.mkplace(name, commit=False)
        if commit:
            self.conn.commit()

    def saveplace(self, place, commit=defaultCommit):
        self.writeplace(place.name, commit)

    def loadplace(self, name):
        if not self.knowplace(name):
            return None
        qrystr = "select name from portal where from_place=?;"
        self.readcursor.execute(qrystr, (name,))
        portals = self.getmanyportal([row[0] for row in self.readcursor])
        qrystr = "select contained from containment where container=?;"
        self.readcursor.execute(qrystr, (name,))
        contents = self.getmanything([row[0] for row in self.readcursor])
        qrystr = "select attribute, value from attribute "\
                 "where attributed_to=?;"
        self.readcursor.execute(qrystr, (name,))
        attributes = self.getmanyattribution([row[0] for row in
                                              self.readcursor])
        p = Place(name, attributes, contents, portals)
        self.placedict[name] = p
        return p

    def loadmanyplace(self, names):
        # portals
        questionmarks = ["?"] * len(names)
        qmstr = ", ".join(questionmarks)
        querystr = "select name from portal where from_place in "\
                   "(" + qmstr + ");"
        self.readcursor.execute(querystr, names)
        portrows = self.readcursor.fetchall()
        for row in self.readcursor:
            if row[0] in place2port:
                place2port[row[0]].append(row[1])
            else:
                place2port[row[0]] = [row[1]]
        # things. not bothering to check for thingness, containment is
        # supposed to do that
        querystr = "select contained from containment "\
                   "where container in (" + qmstr + ");"
        self.readcursor.execute(querystr, names)
        thingrows = self.readcursor.fetchall()
        # attributes
        querystr = "select attributed_to, attribute, value from attribution "\
                   "where attributed_to in (" + qmstr + ");"
        self.readcursor.execute(querystr, names)
        place2attr = {}
        for row in self.readcursor:
            if row[0] not in place2attr:
                place2attr[row[0]] = {}
            place2attr[row[0]][row[1]] = row[2]
        # I have the name of every thing and portal in this place, but
        # I want the Python objects of them.  Normally I'd call
        # getmanything and then assign them en masse but in this case
        # it would cause problems matching the thing to the place it's
        # in. So I'll call getmanything and then look things up in the
        # containment map.
        portnames = untuple(portrows)
        self.getmanyportal(portnames) # I need to write this method
        thingnames = untuple(thingrows)
        self.getmanything(thingnames)
        r = []
        for name in names:
            p = Place(name, place2attr[name], self.getcontents(name),
                      self.getportalsfrom(name))
            self.placedict[name] = p
            r.append(p)
        return r

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if name in self.placedict:
            return self.placedict[name]
        else:
            return self.loadplace(name)

    def getmanyplace(self, names):
        unloaded = list(names)
        r = []
        for name in unloaded:
            if name in self.placedict:
                r.append(self.placedict[name])
                name = ''
        unloaded.remove('')
        r += self.loadmanyplace(unloaded)
        return r

    def delplace(self, name):
        if name in self.placedict:
            del self.placedict[name]
        self.writecursor.execute("delete from place where name=?;", (name,))
        self.writecursor.execute("delete from item where name=?;", (name,))

    def knowthing(self, name):
        self.readcursor.execute("select count(*) from thing where name=?;",
                                (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanything(self, namesingletons):
        return self.knowany("thing", "(name)", namesingletons)

    def knowallthing(self, namesingletons):
        return self.knowall("thing", "(name)", namesingletons)

    def havething(self, thing):
        return self.knowthing(thing.name)

    def mkthing(self, name, commit=defaultCommit):
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into thing values (?);", (name,))
        if commit:
            self.conn.commit()

    def mkmanything(self, thingtups, commit=defaultCommit):
        thingen = [(thing[0],) for thing in thingtups]
        self.mkmany("item", thingen, commit=False)
        self.mkmany("thing", thingen, commit=False)
        self.mkmany("containment", thingtups, commit=False)
        if commit:
            self.conn.commit()

    def updthing(self, name, commit=defaultCommit):
        pass

    def writething(self, name, commit=defaultCommit):
        if self.knowthing(name):
            self.updthing(name, commit)
        else:
            self.mkthing(name, commit)

    def savething(self, thing, commit=defaultCommit):
        if thing.loc is None:
            loc = ''
        else:
            loc = thing.loc.name
        self.writething(thing.name, loc, thing.att.iteritems(), commit)

    def loadthing(self, name):
        self.readcursor.execute("select container from containment "
                                "where contained=?;", (name,))
        atts = self.getattributiondict(attribute=None, attributed_to=name)
        th = Thing(name, atts=atts)
        locs = [self.getitem(it) for it in self.getcontainer(name)]
        th.loc = dict(locs)
        self.thingdict[name] = th
        return th

    def loadmanything(self, names):
        th = {}
        outer = self.getmanycontainer(names)
        inner = self.getmanycontents(names)
        atts = self.getattributionsonmany(names)
        for it in names:
            loc = outer[it]
            cont = inner[it]
            att = atts[it]
            th[it] = Thing(it, loc, att, cont)
        self.thingdict.update(th)
        return th

    def getthing(self, name):
        if name in self.thingdict:
            return self.thingdict[name]
        else:
            return self.loadthing(name)

    def delthing(self, thing, commit=defaultCommit):
        if thing in self.thingdict:
            del self.thingdict[thing]
        self.writecursor.execute("delete from containment where "
                                 "contained=? or container=?;", (thing, thing))
        self.writecursor.execute("delete from thing where name=?;", (thing,))
        self.writecursor.execute("delete from item where name=?;", (thing,))
        if commit:
            self.conn.commit()

    def loaditem(self, name):
        if self.knowthing(name):
            return self.loadthing(name)
        elif self.knowplace(name):
            return self.loadplace(name)
        elif self.knowportal(name):
            return self.loadportal(name)
        else:
            return None

    def getitem(self, name):
        if name in self.thingdict:
            return self.thingdict[name]
        elif name in self.placedict:
            return self.placedict[name]
        elif name in self.portaldict:
            return self.portaldict[name]
        else:
            return self.loaditem(name)

    def _container_loaded(self, contained, dimension):
        return dimension in self.contained_in and\
            contained in self.contained_in[dimension]

    def _contents_loaded(self, container, dimension):
        return dimension in self.contents and\
            container in self.contents[dimension]

    def mkcontainment(self, contained, container, dimension='Physical',
                      commit=defaultCommit):
        self.writecursor.execute("insert into containment values (?, ?, ?);",
                                 (dimension, contained, container))
        if commit:
            self.conn.commit()

    def mkmanycontainment(self, conttups, dimension='Physical',
                          commit=defaultCommit):
        querystr = valuesins("containment", 3, len(conttups))
        flattups = []
        for tup in conttups:
            flattups.append(tup[0])
            flattups.append(tup[1])
            flattups.append(dimension)
        self.writecursor.execute(querystr, flattups)
        if commit:
            self.conn.commit()

    def updcontainment(self, contained, container, dimension='Physical',
                       commit=defaultCommit):
        qrystr = "update containment set container=? where contained=? "\
                 "and dimension=?;"
        self.writecursor.execute(qrystr, (container, contained, dimension))
        if commit:
            self.conn.commit()

    def writecontainment(self, contained, container, dimension='Physical',
                         commit=defaultCommit):
        if self.knowcontainment(contained, dimension):
            self.updcontainment(contained, container, dimension, commit)
        else:
            self.mkcontainment(contained, container, dimension, commit)

    def loadcontainer(self, containedn, dimension='Physical'):
        self.readcursor.execute("select dimension, contained, "
                                "container from containment where contained=? "
                                "and dimension=?;", (containedn, dimension))
        row = self.readcursor.fetchone()
        if len(row) == 0:
            return None
        else:
            self._contain(*row)
            return row[2]

    def loadcontents(self, container, dimension='Physical'):
        self.readcursor.execute("select dimension, contained, container "
                                "from containment where container=? and "
                                "dimension=?;", (container, dimension))
        r = self.readcursor.fetchall()
        for row in r:
            self._contain(*row)
        return r

    def loadmanycontainer(self, contained, dimensions=None):
        r = {}
        left = "select dimension, contained, container " +\
               "from containment where contained in ("
        qm = ", ".join(["?"] * len(contained))
        if dimensions is None:
            qrystr = left + qm + ");"
            self.readcursor.execute(qrystr, contained)
        else:
            qrystr = left + qm + ") and dimension in ("
            qrystr += ", ".join(["?"] * len(dimensions)) + ");"
            self.readcursor.execute(qrystr, contained + dimensions)
        for row in self.readcursor:
            (dim, inside, outside) = row
            if dim not in r:
                r[dim] = {}
            r[dim][inside] = outside
            self._contain(dim, inside, outside)
        return r

    def _contain(self, dimension, contained, container):
        "Internal use"
        # Update the containment dictionaries without touching the
        # database.  That means insert contained into container under
        # dimension, append contained unto the contents of container
        # under dimension, and if contained already had a container,
        # find it, call it oldcontainer, and remove contained from the
        # contents of oldcontainer under dimension.
        if dimension not in self.contents:
            self.contents[dimension] = {}
        if dimension not in self.contained_in:
            self.contained_in[dimension] = {}
        if container not in self.contents[dimension]:
            self.contents[dimension][container] = [contained]
        else:
            self.contents[dimension][container].append(contained)
        if container not in self.contents2:
            self.contents2[container] = {}
        if dimension not in self.contents2[container]:
            self.contents2[container][dimension] = [contained]
        else:
            self.contents2[container][dimension].append(contained)
        oldcontainer = self.getcontainer(contained, dimension)
        self.contained_in[dimension][contained] = container
        if oldcontainer is not None:
            self.contents[dimension][oldcontainer].remove(contained)

    def getcontainer(self, contained, dimension='Physical'):
        if dimension in self.contained_in and\
           contained in self.contained_in[dimension]:
            return self.contained_in[dimension][contained]
        else:
            return self.loadcontainer(contained, dimension)

    def getmanycontainer(self, contents, dimensions=None):
        r = {}  # in dimension x, y is contained in z
        if dimensions is None:
            dimensions = self.contained_in.iterkeys()
        for dimension in dimensions:
            if dimension not in r:
                r[dimension] = {}
            for contained in contents:
                if contained in self.contained_in[dimension]:
                    it = self.contained_in[dimension][contained]
                else:
                    it = self.loadcontainer(contained, dimension)
                r[dimension][contained] = it
        return r

    def getcontents(self, container, dimension='Physical'):
        if dimension in self.contents and\
           container in self.contents[dimension]:
            return self.contents[dimension][container]

    def getmanycontents(self, containers, dimensions=None):
        r = {}  # in dimension x, y contains [z1, z2, ...]
        if dimensions is None:
            dimensions = self.contents.iterkeys()
        for dimension in dimensions:
            if dimension not in r:
                r[dimension] = {}
            for container in containers:
                if container in self.contents[dimension]:
                    it = self.contents[dimension][container]
                else:
                    it = self.loadcontents(container, dimension)
                r[dimension][container] = it
        return r

    def cullcontainment(self, container, keeps=[], commit=defaultCommit):
        if len(keeps) == 0:
            qrystr = "delete from containment where container=?;"
            self.writecursor.execute(qrystr, (container,))
        else:
            inner = "?, " * (len(keeps) - 1)
            left = "delete from containment where container=? "\
                   "and contained not in ("
            right = "?);"
            sqlitefmtstr = left + inner + right
            self.writecursor.execute(sqlitefmtstr, [container] + keeps)
        if commit:
            self.conn.commit()

    def knowcontents(self, container):
        qrystr = "select count(*) from containment where container=?;"
        self.readcursor.execute(qrystr, (container,))
        return self.readcursor.fetchone()[0] > 0

    def havecontents(self, container):
        return self.knowcontents(container.name)

    def knowattribute(self, name):
        qrystr = "select count(*) from attribute where name=?;"
        self.readcursor.execute(qrystr, (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanyattribute(self, singletons):
        return self.knowany("attribute", "(name)", singletons)

    def knowallattribute(self, singletons):
        return self.knowall("attribute", "(name)", singletons)

    def mkattribute(self, name, typ=None, permitted=[], lower=None,
                    upper=None, commit=defaultCommit):
        """Define an attribute type for LiSE items to have.

        Call this method to define an attribute that an item in the
        game can have. These attributes are not the same as the ones
        that every Python object has, although they behave similarly.

        You can define an attribute with just a name, but you might
        want to limit what values are acceptable for it. To do this,
        you may supply any of the other parameters:

        typ is a string. Valid types here are 'str', 'int',
        'float', and 'bool'.

        permitted is a list of values that the attribute is allowed to
        take on. Every value in this list will be permitted, even if
        it's the wrong type, or it falls out of the bounds.

        lower and upper should be numbers. Values of the attribute
        that are below lower or above upper will be rejected unless
        they're in the permitted list.

        """
        if typ == '':
            typ = None
        elif typ not in self.typ.values():
            raise TypeError("LiSE does not support this type: " + typ)
        qrystr = "insert into attribute values (?, ?, ?, ?);"
        self.writecursor.execute(qrystr, (name, typ, lower, upper))
        for perm in permitted:
            self.writecursor.execute("insert into permitted values (?, ?);",
                                     (name, perm))
        if commit:
            self.conn.commit()

    def mkmanyattribute(self, tups, commit=defaultCommit):
        nopermitted = [(tup[0], tup[1], tup[3], tup[4]) for tup in tups]
        onlypermitted = [tup[2] for tup in tups]
        self.mkmany("attribute", nopermitted, commit=False)
        self.mkmanypermitted(onlypermitted, commit=False)
        if commit:
            self.conn.commit()

    def updattribute(self, name, typ, permitted, lower, upper, commit):
        qrystr = "update attribute set type=?, lower=?, upper=? where name=?;"
        self.writecursor.execute(qrystr, (typ, lower, upper))
        qrystr = "select value from permitted where attribute=?;"
        self.readcursor.execute(qrystr, (name,))
        knownperms = [row[0] for row in self.readcursor]
        createdperms = [perm for perm in permitted if perm not in knownperms]
        deletedperms = [perm for perm in knownperms if perm not in permitted]
        for perm in createdperms:
            self.writepermitted(name, perm, commit=False)
        for perm in deletedperms:
            self.delpermitted(name, perm, commit=False)
        if commit:
            self.conn.commit()

    def writeattribute(self, name, typ=None, permitted=[], lower=None,
                       upper=None, commit=defaultCommit):
        if False in [lower.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            lower = None
        if False in [upper.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            upper = None
        if typ not in self.typ.keys():
            typ = None
        if self.knowattribute(name):
            self.updattribute(name, typ, permitted, lower, upper, commit)
        else:
            self.mkattribute(name, typ, permitted, lower, upper, commit)

    def saveattribute(self, attrcheck, commit=defaultCommit):
        assert(isinstance(attrcheck, AttrCheck))
        permitted = []
        lo = None
        hi = None
        typ = None
        for check in attrcheck.checks:
            if isinstance(check, LowerBoundCheck):
                lo = check.bound
            elif isinstance(check, UpperBoundCheck):
                hi = check.bound
            elif isinstance(check, TypeCheck):
                typ = check.typ
            elif isinstance(check, ListCheck):
                permitted += check.list
        self.writeattribute(attrcheck.name, typ, permitted, lo, hi, commit)

    def loadattribute(self, name):
        qrystr = "select type, lower, upper from attribute where name=?;"
        self.readcursor.execute(qrystr, (name,))
        (typ, lo, hi) = self.readcursor.fetchone()
        qrystr = "select value from permitted where attribute=?;"
        self.readcursor.execute(qrystr, (name,))
        perms = [row[0] for row in self.readcursor]
        attrcheck = AttrCheck(name, typ, perms, lo, hi)
        self.attrcheckdict[name] = attrcheck
        return attrcheck

    def loadmanyattribute(self, names):
        r = []
        qrystr = valuesget("attribute", ("name",),
                           ("type", "lower", "upper"), len(names))
        self.readcursor.execute(qrystr, names)
        ntlu_rows = self.readcursor.fetchall()
        qrystr = valuesget("permitted", ("attribute",), ("value",), len(names))
        self.readcursor.execute(qrystr, names)
        perm_dict = {}
        for row in self.readcursor:
            (att, val) = row
            if att in perm_dict:
                perm_dict[att].append(val)
            else:
                perm_dict[att] = [val]
        for row in ntlu_rows:
            (name, typ, lo, hi) = row
            if name in perm_dict:
                r.append(AttrCheck(name, typ, perm_dict[name], lo, hi))
            else:
                r.append(AttrCheck(name, typ, [], lo, hi))
        for ac in r:
            self.attrcheckdict[ac.name] = ac
        return r

    def getattribute(self, name):
        if name in self.attrcheckdict:
            return self.attrcheckdict[name]
        else:
            return self.loadattribute(name)

    def getmanyattribute(self, names):
        unloaded = [name for name in names if name not in self.attrcheckmap]
        self.loadmanyattribute(unloaded)
        return [self.attrcheckmap[name] for name in names]

    def delattribute(self, name, commit=defaultCommit):
        if name in self.attrcheckdict:
            del self.attrcheckdict[name]
        qrystr = "delete from attribute where name=?;"
        self.writecursor.execute(qrystr, (name,))
        if commit:
            self.conn.commit()

    def knowpermitted(self, attr, val=None):
        qrystr = "select count(*) from permitted where attribute=?"
        if val is None:
            self.readcursor.execute(qrystr, (attr,))
        else:
            qrystr += " and value=?"
            self.readcursor.execute(qrystr, (attr, val))
        return self.readcursor.fetchone()[0] > 0

    def knowanypermitted(self, attrval):
        if len(attrval[0]) == 1:  # names only
            return self.knowany("permitted", "(attribute)", attrval)
        else:
            return self.knowany("permitted", "(attribute, value)", attrval)

    def knowallpermitted(self, attrval):
        if len(attrval[0]) == 1:
            return self.knowall("permitted", "(attribute)", attrval)
        else:
            return self.knowall("permitted", "(attribute, value)", attrval)

    def havepermitted(self, attrcheck):
        perms = [check.lst for check in attrcheck.checks
                 if isinstance(check, ListCheck)]
        numperm = len(perms)
        left = "select count(*) from permitted "\
               "where attribute=? and value in ("
        middle = "?, " * numperm - 1
        right = "?);"
        querystr = left + middle + right
        self.readcursor.execute(querystr, perms)
        return numperm == self.readcursor.fetchone()[0]

    def mkpermitted(self, attr, val, commit=defaultCommit):
        qrystr = "insert into permitted values (?, ?);"
        self.writecursor.execute(qrystr, (attr, val))
        if commit:
            self.conn.commit()

    def mkmanypermitted(self, pairs, commit=defaultCommit):
        actualpairs = [pair for pair in pairs if len(pair) == 2]
        if len(actualpairs) == 0:
            return
        meaningfulpairs = [pair for pair in actualpairs if len(pair[0]) > 0]
        self.mkmany("permitted", meaningfulpairs, commit)

    def writepermitted(self, attr, val, commit=defaultCommit):
        if not self.knowpermitted(attr, val):
            self.mkpermitted(attr, val, commit)

    def loadpermitted(self, attr):
        qrystr = "select val from permitted where attribute=?;"
        self.readcursor.execute(qrystr, (attr,))
        perms = [row[0] for row in self.readcursor]
        if attr in self.attrcheckdict:
            attrcheck = self.attrcheckdict[attr]
            attrcheck.lstcheck = ListCheck(perms)
        else:
            attrcheck = AttrCheck(attr, vals=perms)
            self.attrcheckdict[attr] = attrcheck
        return attrcheck

    def getpermitted(self, attr):
        if attr in self.attrcheckdict:
            attrcheck = self.attrcheckdict[attr]
            if isinstance(attrcheck, ListCheck):
                return attrcheck.lst
            else:
                return []
        else:
            return self.loadpermitted(attr)

    def delpermitted(self, attr, val, commit=defaultCommit):
        qrystr = "delete from permitted where attribute=? and value=?;"
        self.writecursor.execute(qrystr, (attr, val))
        if commit:
            self.conn.commit()

    def _attribute(self, item, att, val):
        "internal use"
        if not item in self.attrvalmap:
            self.attrvalmap[item] = {}
        self.attrvalmap[item][att] = val

    def knowattribution(self, attr, item):
        qrystr = "select count(*) from attribution where attribute=? "\
                 "and attributed_to=?;"
        self.readcursor.execute(qrystr, (attr, item))
        return self.readcursor.fetchone()[0] > 0

    def knowanyattribution(self, pairs):
        return self.knowany("attribution", "(attribute, attributed_to)",
                            pairs)

    def knowallattribution(self, pairs):
        return self.knowall("attribution", "(attribute, attributed_to)",
                            pairs)

    def mkattribution(self, attr, item, val, commit=defaultCommit):
        self.writecursor.execute("insert into attribution values (?, ?, ?);",
                                 (attr, item, val))
        if commit:
            self.conn.commit()

    def mkmanyattribution(self, attups, commit=defaultCommit):
        self.mkmany("attribution", attups, commit)

    def updattribution(self, item, attr, val, commit=defaultCommit):
        attrcheck = self.getattribute(attr)
        qrystr = "update attribution set value=? where attributed_to=? "\
                 "and attribute=?;"
        if attrcheck.check(val):
            self.writecursor.execute(qrystr, (val, item, attr))
        else:
            raise ValueError("%s is not a legal value for %s" %
                             (str(val), attr))

    def writeattribution(self, attr, item, val, commit=defaultCommit):
        qrystr = "select count(*) from attribution where attribute=? "\
                 "and attributed_to=?;"
        self.readcursor.execute(qrystr, (attr, item))
        if self.readcursor.fetchone()[0] == 1:
            self.updattribution(attr, item, val, commit)
        else:
            self.mkattribution(attr, item, val, commit)

    def writeattributionson(self, itemname, commit=defaultCommit):
        for attrval in self.attrvaldict[itemname].iteritems():
            self.writeattribution(attrval[0], itemname, attrval[1], commit)

    def saveattributionson(self, item, commit=defaultCommit):
        self.writeattributionson(item.name, commit)

    def delattribution(self, attr, item, commit=defaultCommit):
        qrystr = "delete from attribution where attribute=? "\
                 "and attributed_to=?;"
        self.writecursor.execute(qrystr, (attr, item))
        if commit:
            self.conn.commit()

    def cullattribution(self, item, keeps=[], commit=defaultCommit):
        qrystr = "delete from attribution where attributed_to=?"
        if len(keeps) == 0:
            self.writecursor.execute(qrystr, (item,))
        else:
            inner = "?, " * (len(keeps) - 1)
            left = qrystr + " and attribute not in ("
            right = "?);"
            sqlitefmtstr = left + inner + right
            self.writecursor.execute(sqlitefmtstr, [item] + keeps)
        if commit:
            self.conn.commit()

    def set_attr_upper_bound(self, attr, upper, commit=defaultCommit):
        qrystr = "select count(*) from attribute where name=?;"
        self.readcursor.execute(qrystr, (attr,))
        if self.readcursor.fetchone()[0] == 0:
            qrystr = "insert into attribute values (?, ?, ?, ?);"
            self.writecursor.execute(qrystr, (attr, None, None, upper))
        else:
            qrystr = "update attribute set upper=? where name=?;"
            self.writecursor.execute(qrystr, (upper, attr))
        if commit:
            self.conn.commit()

    def set_attr_lower_bound(self, attr, lower, commit=defaultCommit):
        qrystr = "select count(*) from attribute where name=?;"
        self.readcursor.execute(qrystr, (attr,))
        if self.readcursor.fetchone()[0] == 0:
            qrystr = "insert into attribute values (?, ?, ?, ?)"
            self.writecursor.execute(qrystr, (attr, None, lower, None))
        else:
            qrystr = "update attribute set lower=? where name=?;"
            self.writecursor.execute(qrystr, (lower, attr))
        if commit:
            self.conn.commit()

    def set_attr_bounds(self, attr, lower, upper, commit=defaultCommit):
        qrystr = "select count(*) from attribute where name=?;"
        self.readcursor.execute(qrystr, (attr,))
        if self.readcursor.fetchone()[0] == 0:
            qrystr = "insert into attribute values (?, ?, ?, ?);"
            self.writecursor.execute(qrystr, (attr, None, lower, upper))
        else:
            qrystr = "update attribute set lower=?, upper=? where name=?;"
            self.writecursor.execute(qrystr, (lower, upper, attr))
        if commit:
            self.conn.commit()

    def set_attr_type(self, attr, typ, commit=defaultCommit):
        qrystr = "select count(*) from attribute where name=?;"
        self.readcursor.execute(qrystr, (attr,))
        if self.readcursor.fetchone()[0] == 0:
            qrystr = "insert into attribute values (?, ?, ?, ?);"
            self.writecursor.execute(qrystr, (attr, typ, None, None))
        else:
            qrystr = "update attribute set type=? where name=?;"
            self.writecursor.execute(qrystr, (typ, attr))
        if commit:
            self.conn.commit()

    def loadattribution(self, attr, item):
        qrystr = "select val from attribution where attribute=? "\
                 "and attributed_to=?;"
        self.readcursor.execute(qrystr, (attr, item))
        v = self.readcursor.fetchone()[0]
        self._attribute(item, attr, v)
        return v

    def loadmanyattribution(self, pairs):
        qrystr = valuesget("attribution", ("attribute", "attributed_to"),
                           ("value"))
        qrylst = untuple(pairs)
        self.readcursor.execute(qrystr, qrylst)
        r = {}
        for row in self.readcursor:
            if row[1] not in r:
                r[row[1]] = {}
            r[row[1]][row[0]] = row[2]
            self._attribute(row[1], row[0], row[2])

    def loadattributionson(self, item):
        qrystr = "select attr, val from attribution where attributed_to=?;"
        self.readcursor.execute(qrystr, (item,))
        r = {}
        if item not in self.attrvaldict:
            self.attrvaldict[item] = {}
        for row in self.readcursor:
            r[row[0]] = row[1]
            self.attrvaldict[item][row[0]] = row[1]
        return r

    def loadattributionsonmany(self, items):
        qrystr = valuesget("attribution", ("attribute", "attributed_to"),
                           ("value"), len(items))
        qrylst = untuple(items)
        self.readcursor.execute(qrystr, qrylst)
        r = {}
        for row in self.readcursor:
            if row[1] not in r:
                r[row[1]] = {}
            r[row[1]][row[0]] = row[2]
            self._attribute(row[1], row[0], row[2])
        return r

    def getattribution(self, attr, item):
        if item in self.attrvaldict:
            if self.attrvaldict[item].has_key[attr]:
                return self.attrvaldict[item][attr]
            else:
                return self.loadattribution(attr, item)
        else:
            return self.loadattribution(attr, item)

    def getattributionson(self, item):
        if item not in self.attrvaldict:
            self.loadattributionson(item)
        return self.attrvaldict[item]

    def getattributionsonmany(self, items):
        loaded = items
        unloaded = []
        i = 0
        l = len(loaded)
        while i < l:
            if loaded[i] not in self.attrvaldict:
                unloaded.append(loaded[i])
                del loaded[i]
            i += 1
        a = {}
        for item in loaded:
            a[item] = self.attrvaldict[item]
        a.update(self.loadattributionsonmany(items))
        return a

    def knowportal(self, orig_or_name, dest=None):
        if dest is None:
            qrystr = "select count(*) from portal where name=?;"
            self.readcursor.execute(qrystr, (orig_or_name,))
        else:
            qrystr = "select count(*) from portal where "\
                     "from_place=? and to_place=?;"
            self.readcursor.execute(qrystr, (orig_or_name, dest))
        return self.readcursor.fetchone()[0] == 1

    def knowanyportal(self, tups):
        if len(tups[0]) == 1:
            return self.knowany("portal", "(name)", tups)
        else:
            return self.knowany("portal", "(from_place, to_place)", tups)

    def knowallportal(self, tups):
        if len(tups[0]) == 1:
            return self.knowall("portal", "(name)", tups)
        else:
            return self.knowall("portal", "(from_place, to_place)", tups)

    def haveportal(self, portal):
        return self.knowportal(portal.name)

    def mkportal(self, name, orig, dest, commit=defaultCommit):
        qrystr = "insert into portal values (?, ?, ?);"
        self.writecursor.execute(qrystr, (name, orig, dest))
        if commit:
            self.conn.commit()

    def mkmanyportal(self, porttups, commit=defaultCommit):
        pnames = [(tup[0],) for tup in porttups]
        self.mkmany("item", pnames, commit=False)
        better = []
        for tup in porttups:
            better.append(tup[0:3])
            if tup[3]:
                recip = ("portal[%s->%s]" % (tup[2], tup[1]), tup[2], tup[1])
                better.append(recip)
        self.mkmany("portal", better, commit=False)
        if commit:
            self.conn.commit()

    def updportal(self, name, orig, dest, commit=defaultCommit):
        qrystr = "update portal set from_place=?, to_place=? where name=?;"
        self.writecursor.execute(qrystr, (orig, dest, name))
        if commit:
            self.conn.commit()

    def writeportal(self, name, orig, dest, commit=defaultCommit):
        if self.knowportal(name):
            self.updportal(name, orig, dest, commit)
        else:
            self.mkportal(name, orig, dest, commit)

    def saveportal(self, port, commit=defaultCommit):
        self.writeportal(port.name, port.orig, port.dest, commit)

    def modportal(self, name, orig, dest):
        port = self.portaldict[name]
        if port.orig is not orig or port.dest is not dest:
            port.orig = orig
            port.dest = dest
            self.altered.append(port)

    def _connect(self, port):
        "Internal use"
        self.portaldict[port.name] = port
        self.portalorigdestdict[port.orig][port.dest] = port
        self.portaldestorigdict[port.dest][port.orig] = port

    def loadportal(self, name):
        qrystr = "select from_place, to_place from portal where name=?"
        self.readcursor.execute(qrystr, (name,))
        row = self.readcursor.fetchone()
        if row is None:
            return None
        attdict = self.getattributionson(name)
        port = Portal(name, row[0], row[1], attdict)
        self._connect(port)
        return port

    def loadportalsfrom(self, orig):
        qrystr = "select name, from_place, to_place "\
                 "from portal where from_place=?"
        self.readcursor.execute(qrystr, (orig,))
        r = {}
        for row in self.readcursor:
            name = row[0]
            dest = row[2]
            attdict = self.getattributionson(name)
            port = Portal(name, orig, dest, attdict)
            r[name] = port
            self._connect(port)
        return r

    def getportal(self, name):
        if name in self.portaldict:
            return self.portaldict[name]
        else:
            return self.loadportal(name)

    def getportalsfrom(self, orig):
        if orig in self.portalorigdestdict:
            return self.portalorigdestdict[orig].values()
        else:
            return self.loadportalsfrom(orig)

    def delportal(self, orig_or_name, dest=None, commit=defaultCommit):
        if dest is None:
            qrystr = "delete from portal where name=?"
            self.writecursor.execute(qrystr, (orig_or_name,))
            iname = orig_or_name
        else:
            qrystr = "delete from portal where from_place=? and to_place=?"
            self.writecursor.execute(qrystr, (orig_or_name, dest))
            iname = "portal[%s->%s]" % (orig_or_name, dest)
        self.writecursor.execute("delete from item where name=?;", (iname,))
        if commit:
            self.conn.commit()

    def cullportals(self, orig, keeps, commit=defaultCommit):
        qrystr = "select name from portal where from_place=?;"
        self.readcursor.execute(qrystr, (orig,))
        flatnames = [row[0] for row in self.readcursor]
        undesired = [trash for trash in flatnames if trash not in keeps]
        left = "delete from portal where name in ("
        mid = "?, " * len(undesired) - 1
        right = "?);"
        querystr = left + mid + right
        self.writecursor.execute(querystr, undesired)
        left = left.replace("portal", "item")
        querystr = left + mid + right
        self.writecursor.execute(querystr, undesired)
        if commit:
            self.conn.commit()

    def knowspot(self, place):
        qrystr = "select count(*) from spot where place=?;"
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

    def getspot(self, placen, boardn):
        if boardn in self.spotdict and placen in self.spotdict[boardn]:
            return self.spotdict[boardn][placen]
        else:
            return self.loadspot(placen, boardn)

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

    def syncimg(self, img):
        self.sync('img', img)

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

    def getimg(self, name):
        if name in self.imgdict:
            return self.imgdict[name]
        else:
            return self.loadimg(name)

    def delimg(self, name, commit=defaultCommit):
        if name in self.imgdict:
            del self.imgdict[name]
        self.writecursor.execute("delete from img where name=?;", (name,))
        if commit:
            self.conn.commit()

    def cullimgs(self, commit=defaultCommit):
        keeps = self.imgdict.keys()
        left = "delete from img where name not in ("
        middle = "?, " * (len(keeps) - 1)
        right = "?);"
        querystr = left + middle + right
        self.writecursor.execute(querystr, keeps)
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

    def syncmenuitem(self, mi):
        self.sync('menuitem', mi)

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
        row = self.readcursor.fetchone()
        self.menuitemdict[menuname][idx] = row
        return row

    def getmenuitem(self, menuname, idx):
        if menuname in self.menuitemdict:
            if idx in self.menuitemdict[menuname]:
                return self.menuitemdict[menuname][idx]
            else:
                return self.loadmenuitem(menuname, idx)
        else:
            return self.loadmenuitem(menuname, idx)

    def delmenuitem(self, menuname, i, commit=defaultCommit):
        qrystr = "delete from menuitem where menu=? and index=?;"
        if menuname in self.menuitemdict:
            if i in self.menuitemdict[menuname]:
                del self.menuitemdict[menuname][i]
        self.writecursor.execute(qrystr, (menuname, i))
        if commit:
            self.conn.commit()

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

    def syncboard(self, board):
        self.sync('board', board)

    def writeboard(self, name, w, h, wallpaper, commit=defaultCommit):
        if self.knowboard(name):
            self.updboard(name, w, h, wallpaper, commit)
        else:
            self.mkboard(name, w, h, wallpaper, commit)

    def loadboard(self, name):
        qrystr = "select width, height, wallpaper from board where name=?;"
        self.readcursor.execute(qrystr, (name,))
        tup = self.readcursor.fetchone()
        wall = self.getimg(tup[2])
        board = Board(tup[0], tup[1], wall)
        self.boarddict[name] = board
        return board

    def getboard(self, name):
        if name in self.boarddict:
            return self.boarddict[name]
        else:
            return self.loadboard(name)

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
        self.pawndict[boardn][thingn] = pawn
        return pawn

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

    def loadroute(self, thingn, destn):
        qrystr = "select ord, progress, portal from step where thing=?"\
                 " and destination=?;"
        self.readcursor.execute(qrystr, (thingn, destn))
        steps = self.readcursor.fetchall()
        thing = self.getthing(thingn)
        dest = self.getplace(destn)
        route = Route(steps, thing, dest)
        self.routedict[thingn][destn] = route
        return route

    def getroute(self, thingn, destn):
        if thingn in self.routedict and destn in self.routedict[thingn]:
            return self.routedict[thingn][destn]
        else:
            return self.loadroute(thingn)

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

    def getcolor(self, name):
        if name in self.colordict:
            return self.colordict[name]
        else:
            return self.loadcolor(name)

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

    def getstyle(self, name):
        if name in self.styledict:
            return self.styledict[name]
        else:
            return self.loadstyle(name)

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
        menu = Menu(*self.readcursor.fetchone())
        self.menudict[name] = menu
        return menu

    def getmenu(self, name):
        if name in self.menudict:
            return self.menudict[name]
        else:
            return self.loadmenu(name)

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
