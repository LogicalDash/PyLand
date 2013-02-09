import sqlite3
from place import Place
from portal import Portal
from route import Route
from widgets import *
from thing import Thing
from attrcheck import *
from dimension import Dimension

defaultCommit=True
testDB=False

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
    return ', '.join([ valuesrow(x) for i in xrange(0,y) ])

def valuesins(tab, x, y):
    return "insert into " + tab + " values " + valuesrows(x, y) + ";"

def valuesknow(tab, keyexp, x, y):
    return "select count(*) from " + tab + " where " + keyexp + " in (" + valuesrows(x, y) + ");"

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

    def __init__(self, dbfile, xfuncs = {}, defaultCommit=True):
        self.conn = sqlite3.connect(dbfile)
        self.readcursor = self.conn.cursor()
        self.writecursor = self.conn.cursor()

        self.new = []
        self.altered = []
        
        self.placemap = {}
        self.portalmap = {}
        self.portalorigdestmap = {}
        self.thingmap = {}
        self.spotmap = {}
        self.imgmap = {}
        self.dimmap = {}
        self.boardmap = {}
        self.menumap = {}
        self.menuitemmap = {}
        self.attrvalmap = {}
        self.attrcheckmap = {}
        self.pawnmap = {}
        self.stylemap = {}
        self.colormap = {}

        self.contained_in = {} # This maps strings to other strings, not to Python objects.
        self.contents = {} # ditto


        self.mapmap = { Place : self.placemap,
                        Portal : self.portalmap,
                        Thing : self.thingmap,
                        Spot : self.spotmap,
                        pyglet.resource.image : self.imgmap,
                        Dimension : self.dimmap,
                        Board : self.boardmap,
                        Menu : self.menumap,
                        MenuItem : self.menuitemmap,
                        AttrCheck : self.attrcheckmap,
                        Pawn : self.pawnmap,
                        Style : self.stylemap,
                        Color : self.colormap }
        # This maps strings to functions,
        # giving a user with access to the database the ability to
        # call that function. Not sure how yet.
        self.func = { 'saveplace' : self.saveplace,
                      'getplace' : self.getplace,
                      'delplace' : self.delplace,
                      'savething' : self.savething,
                      'getthing' : self.getthing,
                      'delthing' : self.delthing,
                      'getitem' : self.getitem,
                      'getattribute' : self.getattribute,
                      'saveattribute' : self.saveattribute,
                      'writeattribute' : self.writeattribute,
                      'delattribute' : self.delattribute }
        self.typ = { 'str' : str,
                     'int' : int,
                     'float' : float,
                     'bool' : bool }
        self.func.update(xfuncs)
    def __del__(self):
        self.readcursor.close()
        self.writecursor.close()
        self.conn.commit()
        self.conn.close()
    def mkschema(self):
        # items shall cover everything that has attributes.
        # items may or may not correspond to anything in the gameworld.
        # they may be places. they may be things. they may be people.
        self.writecursor.execute("create table item (name text primary key);")
        self.writecursor.execute("create table place (name text primary key, foreign key(name) references item(name));")
        self.writecursor.execute("create table thing (name text primary key, foreign key(name) references item(name));")
        self.writecursor.execute("create table portal (name text primary key, from_place, to_place, foreign key(name) references item(name), foreign key(from_place) references place(name), foreign key(to_place) references place(name), check(from_place<>to_place));")
        self.writecursor.execute("create table dimension (name text primary key, foreign key(name) references item(name));")
        self.writecursor.execute("create table containment (contained, container, foreign key(contained) references item(name), foreign key(container) references item(name), check(contained<>container), primary key(contained));")
        self.writecursor.execute("create table attribute (name text primary key, type text, lower, upper);")
        self.writecursor.execute("create table attribution (attribute, attributed_to, value, foreign key(attribute) references permitted_values(attribute), foreign key(attributed_to) references item(name), foreign key(value) references permitted_values(value), primary key(attribute, attributed_to));")
        self.writecursor.execute("create table permitted (attribute, value, foreign key(attribute) references attribute(name), primary key(attribute, value));")
        self.writecursor.execute("create table img (name text primary key, path, rltile);")
        self.writecursor.execute("create table board (name text primary key, width integer, height integer, wallpaper, foreign key(wallpaper) references image(name));")
        self.writecursor.execute("create table spot (place text, board text, x integer, y integer, r integer, foreign key(place) references place(name), foreign key(board) references board(name), primary key(place, board));")
        self.writecursor.execute("create table pawn (thing text, board text, img text, spot text, foreign key(img) references img(name), foreign key(thing) references thing(name), foreign key(spot) references spot(place), primary key(thing, board));")
        self.writecursor.execute("create table color (name text primary key, red integer not null check(red between 0 and 255), green integer not null check(green between 0 and 255), blue integer not null check(blue between 0 and 255));")
        self.writecursor.execute("create table style (name text primary key, fontface text not null, fontsize integer not null, spacing integer, bg_inactive, bg_active, fg_inactive, fg_active, foreign key(bg_inactive) references color(name), foreign key(bg_active) references color(name), foreign key(fg_inactive) references color(name), foreign key(fg_active) references color(name));")
        self.writecursor.execute("create table menu (name text primary key, x float not null, y float not null, width float not null, height float not null, style text default 'Default', visible boolean default 0, foreign key(style) references style(name));")
        self.writecursor.execute("create table menuitem (menu text, idx integer, text text, onclick text, closer boolean, foreign key(menu) references menu(name), primary key(menu, idx));")
        self.writecursor.execute("create table step (thing text, ord integer, destination text, progress float, portal text, foreign key(thing) references thing(name), foreign key(portal) references portal(name), foreign key(destination) references place(name), check(progress>=0.0), check(progress<1.0), primary key(thing, ord, destination));")

        # I think maybe I will want to actually store pawns in the database eventually.
        # Later...
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
            return [ n[0]+n[1] for n in tups ]
        self.mkmanycolor(f(default.colors), commit=False)
        self.mkmanystyle(f(default.styles), commit=False)
        self.mkmanymenu(f(default.menus), commit=False)
        self.mkmanymenuitem(f(default.menuitems), commit=False)
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
        querystr = valsknow(tname, keyexp, len(keytups[0]), len(keytups))
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
        querystr = valsknow(tname, keyexp, keylen, numkeys)
        keys = untuple(keytups)
        self.readcursor.execute(querystr, keys)
        r = self.readcursor.fetchone()
        if r in [None, []]:
            return False
        elif r[0] == numkeys:
            return True
        else:
            return False

    def remember(self, obj):
        """ Store changes for immediate accessibility and eventual write to disk.
        
        Whenever you make a new object, or modify an existing
        object, of a class that should be saved in the database, pass
        the object to this method. The database will put it in the
        appropriate dictionary and write it to disk when the time
        comes.

        """
        if obj.__class__ not in self.mapmap.keys():
            raise TypeError("I have no idea how to remember this!")
        m = self.mapmap[obj.__class__]
        if m.has_value(obj):
            self.altered.append(obj)
        elif m.has_key(obj.name): # SHOULDN'T happen--but just in case...
            raise Exception("Duplicate LiSE object by the name of " + obj.name)
        else:
            self.new.append(obj)
            m[obj.name] = obj

    def mk(self, tname, valtup, commit=defaultCommit):
        return self.mkmany(tname, [valtup], commit)

    def know(self, tname, keyexp, keytup):
        return self.knowany(tname, keyexp, [keytup])

    def knowdimension(name):
        self.readcursor.execute("select count(*) from dimension where name=?;")
        return self.readcursor.fetchone()[0] == 1

    def havedimension(dim):
        return self.knowdimension(dim.name)

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
        # Places should always exist in the database before they are Python objects.
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into place values (?);", (name,))
        if commit:
            self.conn.commit()

    def updplace(self, name, commit=defaultCommit):
        pass

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
        portals = self.getportal(name) # should return an iterable
        contents = self.getcontents(name)
        p = Place(name) # I think I might have to handle nulls special
        self.placemap[name] = p
        for port in portals:
            p.portals.append(self.getportal(port[0]))
        for item in contents:
            th = self.getthing(item[0])
            p.addthing(th)
        return p

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if self.placemap.has_key(name):
            return self.placemap[name]
        else:
            return self.loadplace(name)

    def delplace(self, name):
        if self.placemap.has_key(name):
            del self.placemap[name]
        self.writecursor.execute("delete from place where name=?;", (name,))
        self.writecursor.execute("delete from item where name=?;", (name,))

    def knowthing(self, name):
        self.readcursor.execute("select count(*) from thing where name=?;",
                                (name,))
        return self.readcursor.fetchone()[0] == 1
        
    def knowsomething(self, namesingletons):
        return self.knowany("thing", "(name)", namesingletons)

    def knowsomethings(self, namesingletons):
        return self.knowsomething(namesingletons)

    def knowallthing(self, namesingletons):
        return self.knowall("thing", "(name)", namesingletons)

    def knowallthings(self, namesingletons):
        return self.knowallthing(namesingletons)

    def havething(self, thing):
        return self.knowthing(thing.name)

    def mkthing(self, name, commit=defaultCommit):
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into thing values (?);", (name,))
        if commit:
            self.conn.commit()

    def mkmanything(self, thingtups, commit=defaultCommit):
        thingen = [ (thing[0],) for thing in thingtups ]
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
        self.readcursor.execute("select container from containment where contained=?;", (name,))
        loc_s = self.getcontainer(name)
        loc = self.getitem(loc_s)
        atts = self.getattributiondict(attribute=None, attributed_to=name)
        th = Thing(name, loc, atts)
        self.thingmap[name] = th
        return th

    def getthing(self, name):
        if self.thingmap.has_key(name):
            return self.thingmap[name]
        else:
            return self.loadthing(name)

    def delthing(self, thing, commit=defaultCommit):
        if self.thingmap.has_key(thing):
            del self.thingmap[thing]
        self.writecursor.execute("delete from containment where contained=? or container=?;", (thing, thing))
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
        if self.thingmap.has_key(name):
            return self.thingmap[name]
        elif self.placemap.has_key(name):
            return self.placemap[name]
        elif self.portalmap.has_key(name):
            return self.portalmap[name]
        else:
            return self.loaditem(name)
            
    def knowcontainment(self, contained):
        self.readcursor.execute("select count(*) from containment where contained=?;",
                       (contained,))
        return self.readcursor.fetchone()[0] == 1

    def knowsomecontainment(self, singletons):
        return self.knowany("containment", "(contained)", singletons)

    def knowallcontainment(self, singletons):
        return self.knowall("containment", "(contained)", singletons)

    def havecontainment(self, item):
        contained = item.loc
        return self.knowcontainment(item)

    def mkcontainment(self, contained, container, commit=defaultCommit):
        self.writecursor.execute("insert into containment values (?, ?);",
                  (contained, container))
        if commit:
            self.conn.commit()

    def mkmanycontainment(self, conttups, commit=defaultCommit):
        querystr = valuesins("containment", 2, len(conttups))
        flattups = []
        for tup in conttups:
            if type(tup) is tuple:
                flattups.append(tup[0])
                flattups.append(tup[1])
            else:
                flattups.append(tup)
        self.writecursor.execute(querystr, flattups)
        if commit:
            self.conn.commit()

    def updcontainment(self, contained, container, commit=defaultCommit):
        self.writecursor.execute("update containment set container=? where contained=?;",
                  (container, contained))
        if commit:
            self.conn.commit()

    def modcontainment(self, contained, container):
        oldcontainer = self.contained_in[contained]
        if oldcontainer == container:
            return
        self.contained_in[contained] = container
        self.contents[oldcontainer].remove(contained)
        self.contents[container].append(contained)

    def writecontainment(self, contained, container, commit=defaultCommit):
        if self.knowcontainment(contained):
            self.updcontainment(contained, container, commit)
        else:
            self.mkcontainment(contained, container, commit)

    def savecontainment(self, contained, commit=defaultCommit):
        self.writecontainment(contained, contained.loc)

    def loadcontainment(self, contained):
        self.readcursor.execute("select container from containment where contained=?;", (contained,))
        try:
            item = self.readcursor.fetchone()[0]
        except IndexError:
            return None
        self.contained_in[contained] = item
        if self.contents.has_key(item):
            self.contents[item].append(contained)
        else:
            self.contents[item] = [item]
        return item

    def getcontainment(self, contained):
        if self.contained_in.has_key(contained):
            return self.contained_in[contained]
        else:
            return self.loadcontainment(contained)

    def cullcontainment(self, container, keeps=[], commit=defaultCommit):
        if len(keeps) == 0:
            self.writecursor.execute("delete from containment where container=?;", (container,))
        else:
            inner = "?, " * (len(keeps) - 1)
            left = "delete from containment where container=? and contained not in ("
            right = "?);"
            sqlitefmtstr = left + inner + right
            self.writecursor.execute(sqlitefmtstr, [container] + keeps)
        if commit:
            self.conn.commit()

    def getcontainer(self, contained):
        return self.getcontainment(contained)

    def knowcontents(self, container):
        self.readcursor.execute("select count(*) from containment where container=?;",
                                (container,))
        return self.readcursor.fetchone()[0] > 0

    def havecontents(self, container):
        return self.knowcontents(container.name)

    def loadcontents(self, container):
        self.readcursor.execute("select contained from containment where container=?;",
                                (container,))
        c = []
        for contained in self.readcursor:
            if not self.contained_in.has_key(contained[0]):
                self.contained_in[contained[0]] = container
            c.append(contained[0])
        self.contents[container] = c
        return c

    def getcontents(self, container):
        if self.contents.has_key(container):
            return self.contents[container]
        else:
            return self.loadcontents(container)

    def knowattribute(self, name):
        self.readcursor.execute("select count(*) from attribute where name=?;", (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanyattribute(self, singletons):
        return self.knowany("attribute", "(name)", singletons)

    def knowallattribute(self, singletons):
        return self.knowall("attribute", "(name)", singletons)

    def mkattribute(self, name, typ=None, permitted=[], lower=None, upper=None, commit=defaultCommit):
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
        if typ=='':
            typ=None
        elif typ not in self.typ.values():
            raise TypeError("LiSE does not support this type: " + typ)
        self.writecursor.execute("insert into attribute values (?, ?, ?, ?);", (name, typ, lower, upper))
        for perm in permitted:
            self.writecursor.execute("insert into permitted values (?, ?);", (name, perm))
        if commit:
            self.conn.commit()

    def mkmanyattribute(self, tups, commit=defaultCommit):
        nopermitted = [ (tup[0], tup[1], tup[3], tup[4]) for tup in tups ]
        onlypermitted = [ tup[2] for tup in tups ]
        self.mkmany("attribute", nopermitted, commit=False)
        self.mkmanypermitted(onlypermitted, commit=False)
        if commit:
            self.conn.commit()

    def updattribute(self, name, typ, permitted, lower, upper, commit):
        self.writecursor.execute("update attribute set type=?, lower=?, upper=? where name=?;",
                                 (typ, lower, upper))
        self.readcursor.execute("select value from permitted where attribute=?;", (name,))
        knownperms = [ row[0] for row in self.readcursor ]
        createdperms = [ perm for perm in permitted if perm not in knownperms ]
        deletedperms = [ perm for perm in knownperms if perm not in permitted ]
        for perm in createdperms:
            self.writepermitted(name, perm, commit=False)
        for perm in deletedperms:
            self.delpermitted(name, perm, commit=False)
        if commit:
            self.conn.commit()

    def writeattribute(self, name, typ=None, permitted=[], lower=None, upper=None, commit=defaultCommit):
        if False in [lower.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            lower=None
        if False in [upper.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            upper=None
        if typ not in self.typ.keys():
            typ=None
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
        self.readcursor.execute("select type, lower, upper from attribute where name=?;",
                                (name,))
        (typ, lo, hi) = self.readcursor.fetchone()
        self.readcursor.execute("select value from permitted where attribute=?;", (name,))
        perms = [ row[0] for row in self.readcursor ]
        attrcheck = AttrCheck(name, typ, perms, lo, hi)
        self.attrcheckmap[name] = attrcheck
        return attrcheck

    def getattribute(self, name):
        if self.attrcheckmap.has_key(name):
            return self.attrcheckmap[name]
        else:
            return self.loadattribute(name)

    def delattribute(self, name, commit=defaultCommit):
        if self.attrcheckmap.has_key(name):
            del self.attrcheckmap[name]
        self.writecursor.execute("delete from attribute where name=?;", (name,))
        if commit:
            self.conn.commit()

    def knowpermitted(self, attr, val=None):
        if val is None:
            self.readcursor.execute("select count(*) from permitted where attribute=?;", (attr,))
        else:
            self.readcursor.execute("select count(*) from permitted where attribute=? and value=?;",
                                    (attr, val))
        return self.readcursor.fetchone()[0] > 0

    def knowanypermitted(self, attrval):
        if len(attrval[0]) == 1: # names only
            return self.knowany("permitted", "(attribute)", attrval)
        else:
            return self.knowany("permitted", "(attribute, value)", attrval)

    def knowallpermitted(self, attrval):
        if len(attrval[0]) == 1:
            return self.knowall("permitted", "(attribute)", attrval)
        else:
            return self.knowall("permitted", "(attribute, value)", attrval)

    def havepermitted(self, attrcheck):
        perms = [ n for n in check.lst for check in attrcheck.checks if isinstance(check, ListCheck) ]
        numperm = len(perms)
        left = "select count(*) from permitted where attribute=? and value in ("
        middle = "?, " * numperm - 1
        right = "?);"
        querystr = left + middle + right
        self.readcursor.execute(querystr, perms)
        return numperm == self.readcursor.fetchone()[0]

    def mkpermitted(self, attr, val, commit=defaultCommit):
        self.writecursor.execute("insert into permitted values (?, ?);", (attr, val))
        if commit:
            self.conn.commit()

    def mkmanypermitted(self, pairs, commit=defaultCommit):
        actualpairs = [ pair for pair in pairs if len(pair) == 2 ]
        if len(actualpairs) == 0:
            return
        meaningfulpairs = [ pair for pair in actualpairs if len(pair[0]) > 0 ]
        self.mkmany("permitted", meaningfulpairs, commit)

    def writepermitted(self, attr, val, commit=defaultCommit):
        if not self.knowpermitted(attr, val):
            self.mkpermitted(attr, val, commit)

    def loadpermitted(self, attr):
        self.readcursor.execute("select val from permitted where attribute=?;", (attr,))
        perms = [ row[0] for row in self.readcursor ]
        if self.attrcheckmap.has_key(attr):
            attrcheck = self.attrcheckmap[attr]
            attrcheck.lstcheck = ListCheck(perms)
        else:
            attrcheck = AttrCheck(attr, vals=perms)
            self.attrcheckmap[attr] = attrcheck
        return attrcheck

    def getpermitted(self, attr):
        if self.attrcheckmap.has_key(attr):
            attrcheck = self.attrcheckmap[attr]
            if isinstance(attrcheck, ListCheck):
                return attrcheck.lst
            else:
                return []
        else:
            return self.loadpermitted(attr)

    def delpermitted(self, attr, val, commit=defaultCommit):
        self.writecursor.execute("delete from permitted where attribute=? and value=?;",
                                 (attr, val))
        if commit:
            self.conn.commit()
            
    def knowattribution(self, attr, item):
        self.readcursor.execute("select count(*) from attribution where attribute=? and attributed_to=?;",
                       (attr, item))
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
        if attrcheck.check(val):
            self.writecursor.execute("update attribution set value=? where attributed_to=? and attribute=?;",
                                     (val, item, attr))
        else:
            raise ValueError("%s is not a legal value for %s" % (str(val), attr))

    def writeattribution(self, attr, item, val, commit=defaultCommit):
        self.readcursor.execute("select count(*) from attribution where attribute=? and attributed_to=?;", (attr, item))
        if self.readcursor.fetchone()[0] == 1:
            self.updattribution(attr, item, val, commit)
        else:
            self.mkattribution(attr, item, val, commit)

    def writeattributionson(self, itemname, commit=defaultCommit):
        for attrval in self.attrvalmap[itemname].iteritems():
            self.writeattribution(attrval[0], itemname, attrval[1], commit)

    def saveattributionson(self, item, commit=defaultCommit):
        self.writeattributionson(item.name, commit)

    def delattribution(self, attr, item, commit=defaultCommit):
        self.writecursor.execute("delete from attribution where attribute=? and attributed_to=?;",
                                 (attr, item))
        if commit:
            self.conn.commit()

    def cullattribution(self, item, keeps=[], commit=defaultCommit):
        if len(keeps) == 0:
            self.writecursor.execute("delete from attribution where attributed_to=?;", (item,))
        else:
            inner = "?, " * (len(keeps) - 1)
            left = "delete from attribution where attributed_to=? and attribute not in ("
            right = "?);"
            sqlitefmtstr = left + inner + right
            self.writecursor.execute(sqlitefmtstr, [item] + keeps)
        if commit:
            self.conn.commit()

    def set_attr_upper_bound(self, attr, upper, commit=defaultCommit):
        self.readcursor.execute("select count(*) from attribute where name=?;", (attr,))
        if self.readcursor.fetchone()[0] == 0:
            self.writecursor.execute("insert into attribute values (?, ?, ?, ?);", (attr, None, None, upper))
        else:
            self.writecursor.execute("update attribute set upper=? where name=?;", (upper, attr))
        if commit:
            self.conn.commit()

    def set_attr_lower_bound(self, attr, lower, commit=defaultCommit):
        self.readcursor.execute("select count(*) from attribute where name=?;", (attr,))
        if self.readcursor.fetchone()[0] == 0:
            self.writecursor.execute("insert into attribute values (?, ?, ?, ?)'", (attr, None, lower, None))
        else:
            self.writecursor.execute("update attribute set lower=? where name=?;", (lower, attr))
        if commit:
            self.conn.commit()

    def set_attr_bounds(self, attr, lower, upper, commit=defaultCommit):
        self.readcursor.execute("select count(*) from attribute where name=?;", (attr,))
        if self.readcursor.fetchone()[0] == 0:
            self.writecursor.execute("insert into attribute values (?, ?, ?, ?);", (attr, None, lower, upper))
        else:
            self.writecursor.execute("update attribute set lower=?, upper=? where name=?;", (lower, upper, attr))
        if commit:
            self.conn.commit()

    def set_attr_type(self, attr, typ):
        self.readcursor.execute("select count(*) from attribute where name=?;", (attr,))
        if self.readcursor.fetchone()[0] == 0:
            self.writecursor.execute("insert into attribute values (?, ?, ?, ?);", (attr, typ, None, None))
        else:
            self.writecursor.execute("update attribute set type=? where name=?;", (typ, attr))
        if commit:
            self.conn.commit()

    def loadattribution(self, attr, item):
        self.readcursor.execute("select val from attribution where attribute=? and attributed_to=?;", (attr, item))
        v = self.readcursor.fetchone()[0]
        if self.getattribute(attr).check(v):
            self.attrvalmap[item][attr] = v
            return v
        else:
            raise ValueError("Loaded the value %s for the attribute %s, yet it isn't a legal value for that attribute. How did it get there?" % (str(v), attr))

    def loadattributionson(self, item):
        self.readcursor.execute("select attr, val from attribution where attributed_to=?;", (item,))
        r = {}
        for row in self.readcursor:
            if self.getattribute(row[0]).check(row[1]):
                self.attrvalmap[item][row[0]] = row[1]
            else:
                raise ValueError("Loaded the value %s for the attribute %s, yet it isn't a legal value for that attribute. How did it get there?" % (str(row[1]), row[0]))

    def getattribution(self, attr, item):
        if self.attrvalmap.has_key(item):
            if self.attrvalmap[item].has_key[attr]:
                return self.attrvalmap[item][attr]
            else:
                return self.loadattribution(attr, item)
        else:
            return self.loadattribution(attr, item)

    def getattributionson(self, item):
        if not self.attrvalmap.has_key(item):
            self.loadattributionson(item)
        return self.attrvalmap[item]

    def knowportal(self, orig_or_name, dest=None):
        if dest is None:
            self.readcursor.execute("select count(*) from portal where name=?;",
                           (orig_or_name,))
        else:
            self.readcursor.execute("select count(*) from portal where from_place=? and to_place=?;",
            (orig_or_name, dest))
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
        self.writecursor.execute("insert into portal values (?, ?, ?);", (name, orig, dest))
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
        self.writecursor.execute("update portal set from_place=?, to_place=? where name=?;", (orig, dest, name))
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
        port = self.portalmap[name]
        if port.orig is not orig or port.dest is not dest:
            port.orig = orig
            port.dest = dest
            self.altered.append(port)

    def loadportal(self, name):
        self.readcursor.execute("select from_place, to_place from portal where name=?", (name,))
        row = self.readcursor.fetchone()
        if row is None:
            return None
        attdict = self.getattributionson(name)
        port = Portal(name, row[0], row[1], attdict)
        self.portalmap[name] = port
        return port

    def getportal(self, orig_or_name, dest=None):
        if self.portalmap.has_key(orig_or_name):
            return self.portalmap[orig_or_name]
        elif dest is not None:
            if self.portalorigdestmap.has_key(orig_or_name):
                if self.portalorigdestmap[orig_or_name].has_key(dest):
                    return self.portalorigdestmap[orig_or_name][dest]
                else:
                    raise Exception("No portal connecting %s to %s." % (orig_or_name, dest))
            else:
                raise Exception("No portals from %s." % orig_or_name)
        elif self.portalorigdestmap.has_key(orig_or_name):
            return self.portalorigdestmap[orig_or_name].values() # actual Portal objects
        else:
            return self.loadportal(orig_or_name)

    def delportal(self, orig_or_name, dest=None, commit=defaultCommit):
        if dest is None:
            self.writecursor.execute("delete from portal where name=?", (orig_or_name,))
            iname = orig_or_name
        else:
            self.writecursor.execute("delete from portal where from_place=? and to_place=?", (orig_or_name, dest))
            iname = "portal[%s->%s]" % (orig_or_name, dest)
        self.writecursor.execute("delete from item where name=?;", (iname,))
        if commit:
            self.conn.commit()

    def cullportals(self, orig, keeps, commit=defaultCommit):
        self.readcursor.execute("select name from portal where from_place=?;", (orig,))
        flatnames = [ row[0] for row in self.readcursor ]
        undesired = [ trash for trash in flatnames if trash not in keeps ]
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
        self.readcursor.execute("select count(*) from spot where place=?;", (place,))
        return self.readcursor.fetchone()[0] > 0

    def knowanyspot(self, tups):
        return self.knowany("spot", "(place)", tups)

    def knowallspot(self, tups):
        return self.knowall("spot", "(place)", tups)

    def havespot(self, place):
        if self.spotmap.has_key(place):
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
        self.writecursor.execute("update spot set x=?, y=?, r=? where place=? and board=?;",
                                 (x, y, r, place, board))
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
        self.readcursor.execute("select x, y, r from spot where place=? and board=?;",
                                (placen, boardn))
        spottup = (self.getplace(placen), self.getboard(boardn)) + self.readcursor.fetchone()
        spot = Spot(*spottup)
        self.spotmap[place] = spot
        return spot

    def getspot(self, placen):
        if self.spotmap.has_key(placen):
            return self.spotmap[placen]
        else:
            return self.loadspot(placen)

    def delspot(self, place, commit=defaultCommit):
        self.writecursor.execute("delete from spot where place=?;", (place,))
        if commit:
            self.conn.commit()

    def knowimg(self, name):
        self.readcursor.execute("select count(*) from img where name=?;", (name,))
        return self.readcursor.fetchone()[0] == 1

    def knowanyimg(self, tups):
        return self.knowany("img", "(name)", tups)

    def knowallimg(self, tups):
        return self.knowall("img", "(name)", tups)

    def haveimg(self, img):
        return self.knowimg(img.name)

    def mkimg(self, name, path, rl=False, commit=defaultCommit):
        self.writecursor.execute("insert into img values (?, ?, ?);", (name, path, rl))
        if commit:
            self.conn.commit()

    def mkmanyimg(self, tups, commit=defaultCommit):
        self.mkmany("img", tups)

    def updimg(self, name, path, rl=False, commit=defaultCommit):
        self.writecursor.execute("update img set path=?, rltile=? where name=?;", (path, rl, name))
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
        badimg = pyglet.resource.image(path)
        badimgd = badimg.get_image_data()
        bad_rgba = badimgd.get_data('RGBA', badimgd.pitch)
        badimgd.set_data('RGBA', badimgd.pitch, bad_rgba.replace('\xffGll','\x00Gll').replace('\xff.', '\x00.'))
        rtex = badimgd.get_texture()
        rtex.name = name
        self.imgmap[name] = rtex
        return rtex

    def loadimgfile(self, name, path):
        tex = pyglet.resource.image(path).get_image_data().get_texture()
        tex.name = name
        self.imgmap[name] = tex
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
        if self.imgmap.has_key(name):
            return self.imgmap[name]
        else:
            return self.loadimg(name)

    def delimg(self, name, commit=defaultCommit):
        if self.imgmap.has_key(name):
            del self.imgmap[name]
        self.writecursor.execute("delete from img where name=?;", (name,))
        if commit:
            self.conn.commit()

    def cullimgs(self, commit=defaultCommit):
        keeps = self.imgmap.keys()
        left = "delete from img where name not in ("
        middle = "?, " * (len(keeps) - 1)
        right = "?);"
        querystr = left + middle + right
        self.writecursor.execute(querystr, keeps)
        if commit:
            self.conn.commit()

    def mkmenuitem(self, menuname, idx, text, onclick, closer=True, commit=defaultCommit):
        self.writecursor.execute("insert into menuitem values (?, ?, ?, ?, ?);", (menuname, idx, text, onclick, closer))
        if commit:
            self.conn.commit()

    def mkmanymenuitem(self, mitup, commit=defaultCommit):
        self.mkmany("menuitem", mitup, commit)

    def knowmenuitem(self, menuname, idx):
        self.readcursor.execute("select count(*) from menuitem where menu=? and idx=? limit 1;", (menuname, idx))
        return self.readcursor.fetchone()[0] == 1

    def knowanymenuitem(self, pairs):
        return self.knowany("menuitem", "(menu, idx)", pairs)

    def knowallmenuitem(self, pairs):
        return self.knowall("menuitem", "(menu, idx)", pairs)

    def havemenuitem(self, menuitem):
        return self.knowmenuitem(menuitem.menuname, menuitem.i)

    def updmenuitem(self, menuname, idx, text, onclick, closer, commit=defaultCommit):
        self.writecursor.execute("update menuitem set text=?, onclick=?, closer=? where menu=? and idx=?;", (text, onclick, closer, menuname, idx))
        if commit:
            self.conn.commit()

    def syncmenuitem(self, mi):
        self.sync('menuitem', mi)

    def writemenuitem(self, menu, i, text, onclick, closer=True, commit=defaultCommit):
        if self.knowmenuitem(menu, i):
            self.updmenuitem(menu, i, text, onclick, closer, commit)
        else:
            self.mkmenuitem(menu, i, text, onclick, closer, commit)

    def loadmenuitem(self, menuname, idx):
        self.readcursor.execute("select text, onclick, closer from menuitem where menu=? and idx=?;", (menuname, idx))
        row = self.readcursor.fetchone()
        self.menuitemmap[menuname][idx] = row
        return row

    def getmenuitem(self, menuname, idx):
        if self.menuitemmap.has_key(menuname):
            if self.menuitemmap[menuname].has_key(idx):
                return self.menuitemmap[menuname][idx]
            else:
                return self.loadmenuitem(menuname, idx)
        else:
            return self.loadmenuitem(menuname, idx)

    def delmenuitem(self, menuname, i, commit=defaultCommit):
        if self.menuitemmap.has_key(menuname):
            if self.menuitemmap[menuname].has_key(i):
                del self.menuitemmap[menuname][i]
        self.writecursor.execute("delete from menuitem where menu=? and index=?;",
                                 (menuname, i))
        if commit:
            self.conn.commit()

    def knowboard(self, name, w, h, wallpaper):
        self.readcursor.execute("select count(*) from board where name=?;", (name,))
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
        self.writecursor.execute("update board set width=?, height=?, wallpaper=? where name=?;",
                                 (w, h, wallpaper, name))
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
        self.readcursor.execute("select width, height, wallpaper from board where name=?;",
                                (name,))
        tup = self.readcursor.fetchone()
        wall = self.getimg(tup[2])
        board = Board(tup[0], tup[1], wall)
        self.boardmap[name] = board
        return board

    def getboard(self, name):
        if self.boardmap.has_key(name):
            return self.boardmap[name]
        else:
            return self.loadboard(name)

    def delboard(self, name, commit=defaultCommit):
        if self.boardmap.has_key(name):
            del self.boardmap[name]
        self.writecursor.execute("delete from board where name=?;", (name,))
        if commit:
            self.conn.commit()

    def knowpawn(self, item, board=None):
        if board is None:
            self.readcursor.execute("select count(*) from pawn where item=?;", (item,))
        else:
            self.readcursor.execute("select count(*) from pawn where item=? and board=?;", (item, board))
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
        self.writecursor.execute("update pawn set img=?, x=?, y=?, spot=? where item=? and board=?;",
                                 (img, x, y, spot, item, board))
        if commit:
            self.conn.commit()

    def writepawn(self, item, board, img, x, y, spot, commit=defaultCommit):
        if self.knowpawn(name):
            self.updpawn(item, board, img, x, y, spot, commit)
        else:
            self.mkpawn(item, board, img, x, y, spot, commit)

    def loadpawn(self, itemn, boardn):
        self.readcursor.execute("select img, x, y, spot from pawn where itemn=? and boardn=?;",
                                (itemn, boardn))
        (imgn, boardn, x, y, spotn) = self.readcursor.fetchone()
        img = self.getimg(imgn)
        item = self.getitem(itemn)
        board = self.getboard(boardn)
        spot = self.getspot(spotn)
        pawn = Pawn(item, img, board, x, y, spot)
        pawn.route = self.getroute(pawn)
        self.pawnmap[boardn][itemn] = pawn
        return pawn

    def getpawn(self, itemn, boardn):
        if self.pawnmap.has_key(boardn) and self.pawnmap[itemn].has_key(itemn):
            return self.pawnmap[boardn][itemn]
        else:
            return self.loadpawn(itemn, boardn)

    def delpawn(self, itemn, boardn, commit=defaultCommit):
        if self.pawnmap.has_key(boardn) and self.pawnmap.has_key(itemn):
            del self.pawnmap[boardn][itemn]
        self.writecursor.execute("delete from pawn where name=?;", (name,))
        if commit:
            self.conn.commit()

    def cullpawns(self, commit=defaultCommit):
        keeps = self.pawnmap.keys()
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
        self.readcursor.execute("select count(*) from step where thing=? limit 1;", (thingn,))
        return self.readcursor.fetchone()[0]==1

    def haveroute(self, pawn):
        return self.knowroute(pawn.thing.name)

    def loadroute(self, thingn, destn):
        self.readcursor.execute("select ord, progress, portal from step where thing=?"
                                " and route_destination=?;", (thingn, destn))
        steps = self.readcursor.fetchall()
        thing = self.getthing(thingn)
        dest = self.getplace(destn)
        route = Route(steps, thing, dest)
        self.routemap[thingn][destn] = route
        return route

    def getroute(self, thingn, destn):
        if self.routemap.has_key(thingn) and self.routemap[thingn].has_key(destn):
            return self.routemap[thingn][destn]
        else:
            return self.loadroute(thingn)

    def delroute(self, thingn, destn, commit=defaultCommit):
        if self.routemap.has_key(thingn) and self.routemap[thingn].has_key(destn):
            del self.routemap[thingn]
        self.writecursor.execute("delete from step where thing=? and destination=?;", (thingn, destn))
        if commit:
            self.conn.commit()

    def knowcolor(self, name):
        self.readcursor.execute("select count(*) from color where name=?;", (name,))
        return self.readcursor.fetchone()[0] == 1

    def havecolor(self, color):
        return self.knowcolor(color.name)

    def mkcolor(self, name, r, g, b, commit=defaultCommit):
        self.writecursor.execute("insert into color values (?, ?, ?, ?);", (name, r, g, b))
        if commit:
            self.conn.commit()

    def mkmanycolor(self, colortups, commit=defaultCommit):
        self.mkmany("color", colortups, commit)
    
    def updcolor(self, name, r, g, b, commit=defaultCommit):
        self.writecursor.execute("update color set red=?, green=?, blue=? where name=?;",
                                 (r, g, b, name))
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
        self.readcursor.execute("select name, red, green, blue from color where name=?;", (name,))
        color = Color(*self.readcursor.fetchone())
        color.name = name
        self.colormap[name] = color
        return color

    def getcolor(self, name):
        if self.colormap.has_key(name):
            return self.colormap[name]
        else:
            return self.loadcolor(name)

    def delcolor(self, name, commit=defaultCommit):
        if self.colormap.has_key(name):
            del self.colormap[name]
        self.writecursor.execute("delete from color where name=?;", (name,))
        if commit:
            self.conn.commit()

    def knowstyle(self, name):
        self.readcursor.execute("select count(*) from style where name=?;", (name,))
        return self.readcursor.fetchone()[0] == 1

    def havestyle(self, style):
        return self.knowstyle(style.name)

    def mkstyle(self, name, fontface, fontsize, spacing,
                bg_inactive, bg_active, fg_inactive, fg_active, commit=defaultCommit):
        self.writecursor.execute("insert into style values (?, ?, ?, ?, ?, ?, ?, ?);",
                                 (name, fontface, fontsize, spacing, bg_inactive, bg_active,
                                  fg_inactive, fg_active))
        if commit:
            self.conn.commit()

    def mkmanystyle(self, styletups, commit=defaultCommit):
        self.mkmany("style", styletups, commit)

    def updstyle(self, name, fontface, fontsize, spacing,
                bg_inactive, bg_active, fg_inactive, fg_active, commit=defaultCommit):
        self.writecursor.execute("update style set fontface=?, fontsize=?, spacing=?, "
                                 "bg_inactive=?, bg_active=?, fg_inactive=?, fg_active=? "
                                 "where name=?;",
                                 (fontface, fontsize, spacing, bg_inactive, bg_active,
                                  fg_inactive, fg_active, name))
        if commit:
            self.conn.commit()

    def writestyle(self, name, fontface, fontsize, spacing,
                   bg_inactive, bg_active, fg_inactive, fg_active, commit=defaultCommit):
        if self.knowstyle(name):
            self.updstyle(name, fontface, fontsize, spacing, bg_inactive, bg_active,
                          fg_inactive, fg_active, commit)
        else:
            self.mkstyle(name, fontface, fontsize, spacing, bg_inactive, bg_active,
                         fg_inactive, fg_active, commit)

    def savestyle(self, style, commit=defaultCommit):
        self.writestyle(style.name, style.fontface, style.fontsize,
                        style.spacing, style.bg_inactive.name,
                        style.bg_active.name, style.fg_inactive.name,
                        style.fg_active.name, commit)

    def loadstyle(self, name):
        if not self.knowstyle(name):
            raise ValueError("No such style: %s" % name)
        self.readcursor.execute("select fontface, fontsize, spacing, "
                                "bg_inactive, bg_active, fg_inactive, "
                                "fg_active "
                                "from style where name=?;",
                                (name,))
        (ff, fs, s, bg_i, bg_a, fg_i, fg_a) = self.readcursor.fetchone()
        sty = Style(name, ff, fs, s, self.getcolor(bg_i),
                    self.getcolor(bg_a), self.getcolor(fg_i),
                    self.getcolor(fg_a))
        self.stylemap[name] = sty
        return sty

    def getstyle(self, name):
        if self.stylemap.has_key(name):
            return self.stylemap[name]
        else:
            return self.loadstyle(name)

    def delstyle(self, name):
        if self.stylemap.has_key(name):
            del self.stylemap[name]
        if self.knowstyle(name):
            self.writecursor.execute("delete from style where name=?;", (name,))

    def knowmenu(self, name):
        self.readcursor.execute("select count(*) from menu where name=?;", (name,))
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
        self.writecursor.execute("insert into menu values (?, ?, ?, ?, ?, ?, ?);",
                                 (name, x, y, w, h, sty, dv))
        if commit:
            self.conn.commit()

    def mkmanymenu(self, menutups, commit=defaultCommit):
        self.mkmany("menu", menutups)

    def updmenu(self, name, x, y, w, h, sty, commit=defaultCommit):
        # you may not change the default-visibility after making the menu
        self.writecursor.execute("update menu set x=?, y=?, width=?, height=?, style=? where name=?;",
                                 (x, y, w, h, sty, name))
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
                       menu.getwidth(), menu.getheight(), menu.style.name, menu.visible, commit)
        self.new.remove(menu)
        self.altered.remove(menu)

    def loadmenu(self, name):
        if not self.knowmenu(name):
            raise ValueError("Menu does not exist: %s" % name)
        self.readcursor.execute("select name, x, y, width, height, style, visible from menu where name=?;",
                                (name,))
        menu = Menu(*self.readcursor.fetchone())
        self.menumap[name] = menu
        return menu
        
    def getmenu(self, name):
        if self.menumap.has_key(name):
            return self.menumap[name]
        elif window is not None:
            return self.loadmenu(name)
        else:
            raise Exception("Could not load the menu: " + name)

    def delmenu(self, name, commit=defaultCommit):
        if self.menumap.has_key(name):
            del self.menumap[name]
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
            # clas is the class of object to test.
            # keytup is a tuple of the primary key to use. valtup is a
            # tuple of the rest of the record to use. testSomething will
            # make the record for that key and those values and test that
            # stuff done with the record is correct. I've assumed that keytup concatenated with valtup
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
                getter = getattr(db, 'get'+suf)            
                writer(*mkargs)
                jbo = getter(*keytup)
                self.assertEqual(obj, jbo)
            elif testname == 'del':
                killer = getattr(db, 'del'+suf)
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
            tabkey = [ ('place', default.places, Place),
                       ('portal', default.portals, Portal),
                       ('thing', default.things, Thing),
                       ('color', default.colors, Color),
                       ('style', default.styles, Style),
                       ('attribute', default.attributes, AttrCheck),
                       ('attribution', default.attributions, Attribution) ]
            for pair in tabkey:
                suf = pair[0]
                for val in pair[1]:
                    for test in testl:
                        print "Testing %s%s" % (test, suf)
                        self.testSomething(db, suf, pair[2], val[0], val[1], test)
                          
    dtc = DatabaseTestCase()
    dtc.runTest()
