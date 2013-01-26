import sys, os
sys.path.append(os.curdir)

import sqlite3
from place import Place
from portal import Portal
from widgets import *
from thing import Thing
from attrcheck import *

defaultCommit=True

class Database:
    """
    Method naming conventions:

    mksomething(...) means write a record for a new entity

    updsomething(...) means update the record for an entity--blithely
    assuming it exists

    writesomething(...) calls mksomething or updsomething depending on
    whether or not an entity already exists in the database. As
    arguments it takes the same things that mksomething does.

    savesomething(...) takes a Python object of one of the game's
    classes as its first argument, and calls writesomething with
    arguments taken from the appropriate attributes of the Python
    object.

    loadsomething(...) fetches data from the database, constructs an
    appropriate Python object out of it, puts the object in
    somethingmap, and returns the object.

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
        self.placemap = {}
        self.portalmap = {}
        self.thingmap = {}
        self.containermap = {}
        self.spotmap = {}
        self.imgmap = {}
        self.spotgraphmap = {}
        self.canvasmap = {}
        self.menumap = {}
        self.menuitemmap = {}
        self.attrvalmap = {}
        self.attrcheckmap = {}

        self.contained_in = {} # NOT a name map!
        self.func = { 'mkplace' : self.mkplace,
                      'mkthing' : self.mkthing,
                      'mkattr' : self.mkattr,
                      'mkportal' : self.mkportal,
                      'attribute' : self.attribute,
                      'getplace' : self.getplace,
                      'getthing' : self.getthing,
                      'getattr' : self.getattr,
                      'getportal' : self.getportal }
        self.typ = { 'str' : str,
                     'int' : int,
                     'float' : float,
                     'bool' : bool }
        self.func.update(xfuncs)
    def mkschema(self):
        c = self.c
        # items shall cover everything that has attributes.
        # items may or may not correspond to anything in the gameworld.
        # they may be places. they may be things. they may be people.
        c.execute("create table item (name text primary key);"
        "create table place (name text primary key, foreign key(name) references item(name));"
        "create table thing (name text primary key, foreign key(name) references item(name));"
        "create table portal (name text primary key, from_place, to_place, foreign_key(name) references item(name), foreign key(from_place) references place(name), foreign key(to_place) references place(name), check(from_place<>to_place), primary key(from_place, to_place));"
        "create table containment (contained, container, foreign key(contained) references item(name), foreign key(container) references item(name), check(contained<>container), primary key(contained));"
        "create table spot (place primary key, x, y, r, spotgraph, foreign key(place) references place(name));"
        "create table attrtype (name text primary key);"
        "create table attribute (name text primary key, type, lower, upper, foreign key(type) references attrtype(name));"
        "create table attribution (attribute, attributed_to, value, foreign key(attribute) references permitted_values(attribute), foreign key(attributed_to) references item(name), foreign key(value) references permitted_values(value), primary key(attribute, attributed_to));"
        "create table permitted (attribute primary key, value, foreign key(attribute) references attribute(name));"
        "create table img (name text primary key, path, rltile);"
        "create table canvas (name text primary key, width integer, height integer, wallpaper, foreign key(wallpaper) references image(name));"
        "create table sprite (name text primary key, img, item, canvas, x integer not null, y integer not null, foreign key(img) references img(name), foreign key(item) references item(name), foreign key(canvas) references canvas(name));"
        "create table color (name text primary key, red integer not null check(red between 0 and 255), green integer not null check(green between 0 and 255), blue integer not null check(blue between 0 and 255));"
        "create table style (name text primary key, fontface text not null, fontsize integer not null, spacing integer default 6, bg_inactive, bg_active, fg_inactive, fg_active, foreign key(bg_inactive) references color(name), foreign key(bg_active) references color(name), foreign key(fg_inactive) references color(name), foreign key(fg_active) references color(name));"
        "create table menu (name text primary key, x integer not null, y integer not null, width integer not null, height integer not null, style text default 'Default', foreign key(style) references style(name));"
        "create table menuitem (menu, index integer, text, onclick, closer boolean, foreign key(menu) references menu(name), primary key(menu, index));"
        "create table dialog (name text primary key, desc text, menu, foreign key(menu) references menu(name));")
        # I think maybe I will want to actually store sprites in the database eventually.
        # Later...
        self.conn.commit()

    def initialized(self):
        try:
            for tab in ["thing", "place", "attribute", "img"]:
                self.c.execute("select * from ? limit 1;", (tab,))
        except:
            return False
        return True

    def insert_defaults(self, d, commit=defaultCommit):
        # mostly tuples
        for color in d.colors:
            self.mkcolor(*color)
        for style in d.styles:
            self.mkstyle(*style)
        for menu in d.menus:
            self.mkmenu(*menu)
        for menuitem in d.menuitems:
            self.mkmenuitem(*menuitem)
        for place in d.places:
            self.mkplace(place) # NOT tuples
        for portal in d.portals:
            name = "portal[%s->%s]" % (portal[0], portal[1])
            self.mkportal(name, portal[0], portal[1])
        for thing in d.things:
            self.mkthing(*thing)
        for attribute in d.attributes:
            self.mkattribute(*attribute)
        for attribution in d.attributions:
            self.writeattribution(*attribution)
        if commit:
            self.conn.commit()

    def knowplace(self, name):
        self.readcursor.execute("select count(*) from place where name=?;")
        return self.readcursor.fetchone()[0] == 1

    def haveplace(self, place):
        return self.knowplace(place.name)

    def mkplace(self, name, contents=[], atts=[], commit=defaultCommit):
        # Places should always exist in the database before they are Python objects.
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into place values (?);", (name,))
        for item in contents:
            self.mkthing(*item)
        for atr in atts:
            self.writeattribution(atr, name, value, commit=False)
        if commit:
            self.conn.commit()
        return self.loadplace(name)

    def updplace(self, name, contents, atts, commit):
        for item in contents:
            self.writecontainment(item, name, commit=False)
        self.cullcontainment(contents)
        attn = [ (name, att[0], att[1]) for att in atts ]
        for att in attn:
            self.writeattribution(*attn)
        self.cullattribution(attn)

    def writeplace(self, name, contents=[], atts=[], commit=defaultCommit):
        if self.knowplace(name):
            self.updplace(name, contents, atts, commit)
        else:
            self.mkplace(name, contents, atts, commit)

    def saveplace(self, place, commit=defaultCommit):
        self.writeplace(place.name, place.contents, place.att.iteritems(), commit)

    def loadplace(self, name):
        self.readcursor.execute("select * from place where name=?;", (name,))
        firstrow = self.readcursor.fetchone()
        if firstrow is None:
            # no such place
            return None
        name = firstrow[0]
        self.readcursor.execute("select to_place from portal where from_place=?;", (name,))
        portals = self.readcursor.fetchall()
        self.readcursor.execute("select contained from containment where container=?;", (name,))
        contents = self.readcursor.fetchall()
        p = Place(name) # I think I might have to handle nulls special
        self.placemap[name] = p
        for port in portals:
            d = self.getplace(port)
            p.connect_to(d)
        for item in contents:
            th = self.getthing(item)
            p.addthing(th)
        return p

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if self.placemap.has_key(name):
            return self.placemap[name]
        else:
            return self.loadplace(name)

    def mkthing(self, name, loc=None, atts=[], commit=defaultCommit):
        self.writecursor.execute("insert into item values (?);", (name,))
        self.writecursor.execute("insert into thing values (?);", (name,))
        for att in atts:
            self.writeattribution(att[0], name, att[1], commit=False)
        # Only then do I add the thing to a location, because it's
        # possible the location has some restrictions that will deny this
        # thing entry, because of its attributes.
        if loc is not None:
            self.writecontainment(name, loc, commit=False)
        if commit:
            self.conn.commit()

    def updthing(self, name, loc=None, atts=[], commit=defaultCommit):
        for att in atts:
            self.writeattribution(att[0], name, att[1])
        if loc is not None:
            self.writecontainment(name, loc)
        self.cullattribution(name, atts)


    def writething(self, name, loc="", atts=[], commit=defaultCommit):
        self.readcursor.execute("select count(*) from thing where name=?;", (name,))
        if self.readcursor.fetchone()[0] == 1:
            self.mkthing(name, loc, atts, commit)
        else:
            self.updthing(name, loc, atts, commit)

    def savething(self, thing):
        self.writething(thing.name, thing.loc.name, thing.att.iteritems(), commit)

    def delthing(self, thing, commit=defaultCommit):
        c = self.conn.cursor()
        c.execute("delete from containment where contained=? or container=?;", (thing, thing))
        c.execute("delete from thing where name=?;", (thing,))
        c.close()
        if commit:
            self.conn.commit()

    def loadthing(self, name):
        self.readcursor.execute("select container from containment where contained=?;", (name,))
        loc_s = self.readcursor.fetchone()
        if loc_s is not None:
            loc = self.getplace(loc_s)
        else:
            loc = None
        self.readcursor.execute("select attribute, value from attribution where attributed_to=?;", (name,))
        atts_s_l = self.readcursor.fetchall()
        atts_l = [att for att in atts_s_l]
        th = Thing(name, loc, dict(atts_l))
        self.thingmap[name] = th
        return th

    def getthing(self, name):
        if self.thingmap.has_key(name):
            return self.thingmap[name]
        else:
            return self.loadthing(name)

    def knowcontainment(self, contained):
        self.readcursor.execute("select count(*) from containment where contained=?;",
                       (contained,))
        return self.readcursor.fetchone()[0] == 1

    def havecontainment(self, item):
        contained = item.loc
        return self.knowcontainment(item)

    def mkcontainment(self, contained, container, commit=defaultCommit):
        self.writecursor.execute("insert into containment values (?, ?);",
                  (contained, container))
        if commit:
            self.conn.commit()

    def updcontainment(self, contained, container, commit=defaultCommit):
        self.writecursor.execute("update containment set container=? where contained=?;",
                  (container, contained))
        if commit:
            self.conn.commit()

    def writecontainment(self, contained, container, commit=defaultCommit):
        if self.knowcontainment(contained):
            self.updcontainment(contained, container, commit)
        else:
            self.mkcontainment(contained, container, commit)

    def delcontainment(self, contained, container, commit=defaultCommit):
        self.writecursor.execute("delete from containment where contained=? and container=?;",
                       (contained, container))
        if commit:
            self.conn.commit()

    def cullcontainment(self, container, keeps, commit):
        inner = "?, " * len(keeps) - 1
        left = "delete from containment where container=? and contained not in ("
        right = "?);"
        sqlitefmtstr = left + inner + right
        self.writecursor.execute(sqlitefmtstr, [container] + keeps)

    # No such thing as a "containment object"; no savecontainment(...) method.
    # Here, have a saveallcontainment(...) instead.
    def saveallcontainment(self, commit=defaultCommit):
        citer = self.contained_in.iteritems()
        for newcontain in citer:
            self.writecontainment(newcontain, self.contained_in[newcontain], commit=False)
        for oldcontain in self.c.execute("select contained, container from containment;"):
            (contained, container) = oldcontain
            if self.containermap[contained] is not container:
                self.delcontainment(oldcontain[0], oldcontain[1], commit=False)
        if commit:
            self.conn.commit()

    def mkattribute(self, name, typ, permitted, lower, upper, commit):
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
        self.writecursor.execute("insert into attribute values (?, ?, ?, ?);", name, typ, lower, upper)
        for perm in permitted:
            self.writecursor.execute("insert into permitted values (?, ?);", name, perm)
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
            self.mkpermitted(name, perm, commit=False)
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

    def loadattribute(self, name):
        self.readcursor.execute("select type, lower, upper from attribute where name=?;",
                                (name,))
        (typ, lo, hi) = self.readcursor.fetchone()
        self.readcursor.execute("select value from permitted where attribute=?;", (name,))
        perms = [ row[0] for row in self.readcursor ]
        attrcheck = AttrCheck(typ, perms, lo, hi)
        attrcheck.name = name
        self.attrcheckmap[name] = attrcheck
        return attrcheck

    def getattribute(self, name):
        if self.attrcheckmap.has_key(name):
            return self.attrcheckmap[name]
        else:
            return self.loadattribute(name)

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
        
    def knowattribute(self, name):
        self.readcursor.execute("select count(*) from attribute where name=?;", (name,))
        return self.readcursor.fetchone()[0] == 1

    def mkpermitted(self, attr, val, commit):
        self.writecursor.execute("insert into permitted values (?, ?);", (attr, val))
        if commit:
            self.conn.commit()

    def delpermitted(self, attr, val, commit):
        self.writecursor.execute("delete from permitted where attribute=? and value=?;",
                                 (attr, val))
        if commit:
            self.conn.commit()

    def mkattribution(self, attr, item, val, commit=defaultCommit):
        attrcheck = self.getattribute(attr)
        if attrcheck.check(val):
            self.writecursor.execute("insert into attribution values (?, ?, ?);",
                                     (attr, item, val))
            if commit:
                self.conn.commit()
        else:
            raise ValueError("%s is not a legal value for %s" % (str(val), attr))

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

    def delattribution(self, attr, item, commit=defaultCommit):
        self.writecursor.execute("delete from attribution where attribute=? and attributed_to=?;",
                                 (attr, item))
        if commit:
            self.conn.commit()

    def cullattribution(self, item, keeps, commit=defaultCommit):
        inner = "?, " * len(keeps) - 1
        left = "delete from attribution where attributed_to=? and attribute not in ("
        right = "?);"
        sqlitefmtstr = left + inner + right
        self.writecursor.execute(sqlitefmtstr, [item] + keeps)
        if commit:
            self.conn.commit()

    def set_attr_upper_bound(self, attr, upper, commit=defaultCommit):
        self.readcursor.execute("select count(*) from attribute where name=?;", (attr,))
        if self.c.fetchone()[0] == 0:
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
            self.c.execute("update attribute set type=? where name=?;", (typ, attr))
        if commit:
            self.conn.commit()

    def knowattribution(self, attr, item):
        self.c.execute("select count(*) from attribution where attribute=? and attributed_to=?;",
                       (attr, item))
        return self.c.fetchone()[0] > 0

    def loadattribution(self, attr, item):
        self.readcursor.execute("select val from attribution where attribute=? and attributed_to=?;", (attr, item))
        v = self.readcursor.fetchone()[0]
        self.attrvalmap[(attr, item)] = v
        return v

    def getattribution(self, attr, item):
        if self.attrvalmap.has_key((attr, item)):
            return self.attrvalmap[(attr, item)]
        else:
            return self.loadattribution(attr, item)

    def knowportal(self, orig_or_name, dest=None):
        if dest is None:
            self.c.execute("select count(*) from portal where name=?;",
                           (orig_or_name,))
        else:
            self.c.execute("select count(*) from portal where from_place=? and to_place=?;",
            (orig_or_name, dest))
        return self.c.fetchone()[0] == 1

    def haveportal(self, portal):
        return self.knowportal(portal.orig, portal.dest)

    def mkportal(self, name, orig, dest, reciprocal=True, commit=defaultCommit):
        self.c.execute("insert into portal values (?, ?, ?);", (name, orig, dest))
        if reciprocal:
            name = 'portal[%s->%s]' % (dest, orig)
            self.c.execute("insert into portal values (?, ?, ?);" (name, dest, orig))
        if commit:
            self.conn.commit()

    def delportal(self, orig_or_name, dest=None, commit=defaultCommit):
        if dest is None:
            self.c.execute("delete from portal where name=?", (orig_or_name,))
        else:
            self.c.execute("delete from portal where from_place=? and to_place=?", (orig_or_name, dest))
        if commit:
            self.conn.commit()

    def knowspot(self, place):
        self.c.execute("select count(*) from spot where place=?;", (place,))
        return self.c.fetchone()[0] > 0

    def havespot(self, place):
        return self.knowspot(place.name)

    def mkspot(self, place, x, y, r, graph, commit=defaultCommit):
        if not self.has_spot(place):
            c = self.conn.cursor()
            c.execute("insert into spot values (?, ?, ?, ?, ?);", (place, x, y, r, graph))
            c.close()
        if commit:
            self.conn.commit()

    def loadspot(self, place):
        self.c.execute("select * from spot where place=?;", (place,))
        q = self.c.fetchone()
        r = Spot(self.getplace(q[0]), int(q[1]), int(q[2]), int(q[3]), self.getgraph(q[4]))
        self.getgraph(q[4]).add_spot(r)
        self.spotmap[place] = r
        return r

    def getspot(self, placen):
        if self.spotmap.has_key(placen):
            return self.spotmap[placen]
        else:
            return self.loadspot(placen)

    def delspot(self, spot, commit=defaultCommit):
        self.writecursor.execute("delete from spot where place=?;", (spot.place.name,))
        if commit:
            self.conn.commit()

    def loadspotgraph(self, graphn):
        self.c.execute("select spot from spotgraph where graph=?;", (graphn,))
        g = SpotGraph()
        spotgraph[graphn] = g
        for spotstring in c:
            g.add_spot(self.getspot(spotstring))
        return g

    def getspotgraph(self, graphn):
        if spotgraph.has_key(graphn):
            return self.spotgraphmap[graphn]
        else:
            return self.loadgraph(graphn)

    def mkimg(self, name, path, rl=False):
        self.c.execute("insert into img values (?, ?, ?);", (name, path, rl))

    def loadrltile(self, name, path):
        badimg = pyglet.resource.image(path)
        badimgd = badimg.get_image_data()
        bad_rgba = badimgd.get_data('RGBA', badimgd.pitch)
        badimgd.set_data('RGBA', badimgd.pitch, bad_rgba.replace('\xffGll','\x00Gll').replace('\xff.', '\x00.'))
        self.imgmap[name] = badimgd.get_texture()
        return self.imgmap[name]

    def loadimgfile(self, name, path):
        tex = pyglet.resource.image(path).get_image_data().get_texture()
        self.imgmap[name] = tex
        return tex

    def loadimg(self, name):
        self.c.execute("select * from imgfile where name=?", (name,))
        row = self.c.fetchone()
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

    def mkmenuitem(self, menuname, idx, text, onclick, closer=True, commit=defaultCommit):
        self.c.execute("insert into menuitem values (?, ?, ?, ?, ?);", (menuname, idx, text, onclick, closer))
        if commit:
            self.conn.commit()

    def menuitem_exists(self, menuname, idx):
        self.c.execute("select count(*) from menuitem where menu=? and idx=? limit 1;", (menuname, idx))
        return self.c.fetchone()[0] == 1

    def updmenuitem(self, menuname, idx, text, onclick, closer, commit=defaultCommit):
        self.c.execute("update menuitem set text=?, onclick=?, closer=? where menu=? and idx=?;", (text, onclick, closer, menuname, idx))
        if commit:
            self.conn.commit()

    def writemenuitem(self, menuname, idx, text, onclick, closer, commit=defaultCommit):
        if self.menuitem_exists(menuname, idx):
            self.updmenuitem(menuname, idx, text, onclick, closer, commit)
        else:
            self.mkmenuitem(menuname, idx, text, onclick, closer, commit)

    def loadmenuitem(self, menuname, idx):
        self.c.execute("select text, onclick, closer from menuitem where menu=? and idx=?;", (menuname, idx))
        row = self.c.fetchone()
        if len(row) != 3:
            return None
        else:
            menu = self.getmenu(menuname)
            it = menu.insert_item(idx, row[0], row[1], row[2])
            self.menuitemmap[(menuname, idx)] = it
            return it

    def getmenuitem(self, menuname, idx):
        if self.menuitemmap.has_key((menuname, idx)):
            return self.menuitemmap[(menuname, idx)]
        else:
            return self.loadmenuitem(menuname, idx)

    def mkmenu(self, name, x, y, w, h, commit=defaultCommit):
        self.c.execute("insert into menu values (?, ?, ?, ?, ?)", (name, x, y, w, h))
        if commit:
            self.c.commit()

    def loadmenu(self, name, window):
        self.c.execute("select count(*) from menuitem where menu=?;", (name,))
        itemct = c.fetchone()[0]
        if itemct == 0:
            return None
        self.c.execute("select x, y, width, height, style from menu where name=?;", (name,))
        (x, y, w, h, s) = self.c.fetchone()
        self.c.execute("select fontface, fontsize, spacing, bg_inactive, bg_active, fg_inactive, fg_active from style where name=?;", (s,))
        (ff, fs, space, bgi, bga, fgi, fga) = self.c.fetchone()
        self.c.execute("select text, onclick, closer from menuitem where menu=?;", (name,))
        menu = Menu(x, y, w, h, bgi, fgi, fga, ff, fs, window, space)
        for row in c:
            menu.add_item(*row)
        self.menu[name] = menu
        return menu

    def getmenu(self, name, window=None):
        if self.menu.has_key(name):
            return self.menu[name]
        elif window is not None:
            return self.loadmenu(name, window)
        else:
            raise Exception("When getting a menu for the first time, you need to supply the window to put it in.")

    def loadportal(self, name):
        self.c.execute("select from_place, to_place from portal where name=?", (name,))
        row = self.c.fetchone()
        if row is None:
            return None
        else:
            port = Portal(row[0], row[1])
            self.portalmap[name] = port
            return port

    def getportal(self, name):
        if self.portalmap.has_key(name):
            return self.portalmap[name]
        else:
            return self.loadportal(name)

        def getcontents(self, name):
        container = self.getthing(name)
        if self.contained_in.has_value(container):
            return [ kv[0] for kv in self.contained_in.iteritems() if kv[1] is container ]
        else:
            return self.loadcontainer(container)

    def getcontainer(self, name):
        contained = self.getthing(name)
        if self.contained_in.has_key(contained):
            return self.contained_in[contained]
        else:
            return self.loadcontained(contained)





import unittest
from parms import DefaultParameters
default = DefaultParameters()
class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db.mkschema()
        self.db.insert_defaults(default)
    def testThing(self):
        desk = self.db.getthing("mydesk")
        self.assertEqual(desk.name, "mydesk")
        myroom = self.db.getplace("myroom")
        self.assertIs(desk.location, myroom)
        self.assertEqual(desk["lbs"], 50)
        self.assertEqual(desk["meterswide"], 1.2)
    def testPlace(self):
        myroom = self.db.getplace("myroom")
        outside = self.db.getplace("outside")
        self.assertIs(myroom, outside.portals[0].dest)
        self.assertIs(outside, myroom.portals[0].dest)
        self.putinto("thesky", "outside")
        sky = self.getthing("thesky")
        self.assertIn(sky, outside.contents)
    def testPortal(self):
        for port in default.portals:
            self.db.
    def runTest(self):
        self.testPlace()
        self.testThing()

dtc = DatabaseTestCase()
dtc.run()
