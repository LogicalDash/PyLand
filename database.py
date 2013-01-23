import sys, os
sys.path.append(os.curdir)

import sqlite3
from place import Place
from portal import Portal
from widgets import *
from thing import Thing
from attrcheck import *


class Database:
    def __init__(self, dbfile, xfuncs = {}, defaultCommit=True):
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
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
        self.defaultCommit = defaultCommit
    def mkschema(self):
        c = self.c
        # items shall cover everything that has attributes.
        # items may or may not correspond to anything in the gameworld.
        # they may be places. they may be things. they may be people.
        c.execute("create table item (name text primary key);
        create table place (name text primary key, foreign key(name) references item(name));
        create table thing (name text primary key, foreign key(name) references item(name));
        create table portal (name text primary key, from_place, to_place, foreign_key(name) references item(name), foreign key(from_place) references place(name), foreign key(to_place) references place(name), check(from_place<>to_place), primary key(from_place, to_place));
        create table containment (contained, container, foreign key(contained) references item(name), foreign key(container) references item(name), check(contained<>container), primary key(contained, container));
        create table spot (place primary key, x, y, r, spotgraph, foreign key(place) references place(name));
        create table attrtype (name text primary key);
        create table attribute (name text primary key, type, lower, upper, foreign key(type) references attrtype(name));
        create table attribution (attribute, attributed_to, value, foreign key(attribute) references permitted_values(attribute), foreign key(attributed_to) references item(name), foreign key(value) references permitted_values(value), primary key(attribute, attributed_to));
        create table permitted (attribute primary key, value, foreign key(attribute) references attribute(name));
        create table img (name text primary key, path, rltile);
        create table canvas (name text primary key, width integer, height integer, wallpaper, foreign key(wallpaper) references image(name));
        create table sprite (name text primary key, img, item, canvas, x integer not null, y integer not null, foreign key(img) references img(name), foreign key(item) references item(name), foreign key(canvas) references canvas(name));
        create table color (name text primary key, red integer not null check(red between 0 and 255), green integer not null check(green between 0 and 255), blue integer not null check(blue between 0 and 255));
        create table style (name text primary key, fontface text not null, fontsize integer not null, spacing integer default 6, bg_inactive, bg_active, fg_inactive, fg_active, foreign key(bg_inactive) references color(name), foreign key(bg_active) references color(name), foreign key(fg_inactive) references color(name), foreign key(fg_active) references color(name));
        create table menu (name text primary key, x integer not null, y integer not null, width integer not null, height integer not null, style text default 'Default', foreign key(style) references style(name));
        create table menuitem (menu, index integer, text, onclick, closer boolean, foreign key(menu) references menu(name), primary key(menu, index));
        create table dialog (name text primary key, desc text, menu, foreign key(menu) references menu(name))")
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

    def insert_defaults(self, colors, styles, menus, menuitems, commit=self.defaultCommit):
        # everything is tuples
        # put everything in
        for color in colors:
            self.c.execute("insert into color values (?, ?, ?, ?);", color)
        for style in styles:
            self.c.execute("insert into style values (?, ?, ?, ?, ?, ?, ?, ?);", style)
        for menu in menus:
            self.c.execute("insert into menu values (?, ?, ?, ?, ?);", menu)
        for menuitem in menuitems:
            self.c.execute("insert into menuitem values (?, ?, ?, ?);", menuitem)
        if commit:
            self.conn.commit()

    def getcontents(self, name):
        # Assume that I'm getting a string and not a real Thing
        # object. That's the way the rest of these functions work...
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

    def putinto(self, container, contained, commit=self.defaultCommit):
        if (contained, container) in self.contained_in.iteritems():
            self.contained_in[contained] = container
        else:
            self.c.execute("insert into containment values (?, ?);", (contained, container))
        if commit:
            self.conn.commit()

    def savecontainment(self):
        citer = self.contained_in.iteritems()
        for newcontain in citer:
            self.c.execute("select count(*) from containment where container=?;", newcontain[0])
            if self.c.fetchone()[0] == 0:
                self.c.execute("insert into containment values (?, ?);", newcontain)
        for oldcontain in self.c.execute("select container, contained from containment;"):
            (container, contained) = oldcontain
            if self.containermap[contained] is not container:
                c = self.conn.cursor()
                c.execute("delete from containment where container=? and contained=?;", oldcontain)
                c.close()

    def mkplace(self, name, portals=[], contents=[], atts=[], commit=self.defaultCommit):
        # Places should always exist in the database before they are Python objects.
        c = self.c
        c.execute("insert into item values (?);", (name,))
        c.execute("insert into place values (?);", (name,))
	    for portal in portals:
		    c.execute("insert into portal values (?, ?);", [name, dest])
	    for item in contents:
		    c.execute("insert into containment values (?, ?);", [item, name])
	    for atr in atts:
		    self.attribute(atr, name, value, commit=False)
	    if commit:
		    self.conn.commit()
	    return self.loadplace(name)

    def loadplace(self, name):
	    c = self.c
	    c.execute("select * from place where name=?;", (name,))
	    firstrow = c.fetchone()
	    if firstrow is None:
		    # no such place
		    return None
	    name = firstrow[0]
	    c.execute("select to_place from portal where from_place=?;", (name,))
	    portals = c.fetchall()
	    c.execute("select contained from containment where container=?;", (name,))
	    contents = c.fetchall()
	    p = Place(name) # I think I might have to handle nulls special
	    self.placemap[name] = p
	    for port in portals:
		    d = self.getplace(port)
		    p.connect_to(d)
	    for item in contents:
		    th = self.getthing(item)
		    p.addthing(th)
	    return p

    def saveplace(self, place, commit=self.defaultCommit):
	    # This time it is an actual Place object. Presumably from self.placemap.
	    name = place.name
	    if self.contained_in.has_key(name):
		    self.c.execute("update containment set container=? where contained=?;",
					       (self.contained_in[name], name))
	    # delete portals from the database when they no longer exist.
	    ports = [port.dest for port in place.portals]
	    self.c.execute("select to_place from portal where from_place=?", (name,))
	    oldports = self.c.fetchall()
	    for oldie in oldports:
		    if oldie not in ports:
			    self.c.execute("delete from portal where from_place=? and to_place=?",
						       (name, oldie))
	    # overwrite all the old ports with the new ones.
	    # Handling insert and update separately seems to result in more queries.
            for portal in place.portals:
                name = "portal[%s->%s]" % (place.name, portal.dest.name)
                self.mkportal(name, place.name, portal.dest.name)
		# Now add all the contained things
            for th in place.contents:
                self.savething(th, commit=False)
            for att in place.attributes:
                self.c.execute("insert or replace into attribution values (?, ?, ?)", (att,))
            if commit:
                self.conn.commit()

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if self.placemap.has_key(name):
            return self.placemap[name]
        else:
            return self.loadplace(name)

    def place_exists(self, name):
        if self.placemap.has_key(name):
            return True
        self.c.execute("select count(*) from place where name=?;", (name,))
        return c.fetchone()[0] > 0

    def mkthing(self, name, loc="", atts=[], commit=self.defaultCommit):
        c = self.c
        c.execute("insert into item values (?);", (name,))
        c.execute("insert into thing values (?);", (name,))
        for att in atts:
            self.attribute(att[0], name, att[1], commit=False)
        # Only then do I add the thing to a location, because it's
        # possible the location has some restrictions that will deny this
        # thing entry, because of its attributes.
        self.putinto(name, loc, commit=False)
        if commit:
            self.conn.commit()

    def savething(self, th, commit=self.defaultCommit):
        self.c.execute("select count(*) from thing where name=?;", (th.name,))
        if self.c.fetchone()[0] == 0:
            # the thing is new
            self.c.execute("insert into item values (?);", (th.name,))
            self.c.execute("insert into thing values (?);", (th.name,))
            # I don't think there's anything to enforce places not
            # being things.  Not sure if that's a problem or what.
            self.putinto(th.name, th.location.name)
            for attp in th.att.iteritems():
                self.saveattr(attp[0], th.name, attp[1])
        else:
            self.c.execute("update containment set container=? where name=?;", (th.location.name, th.name))
            for attp in th.att.iteritems():
        if commit:
            self.conn.commit()

    def loadthing(self, name):
        c = self.c
        c.execute("select container from containment where contained=?;", (name,))
        loc_s = c.fetchone()
        if loc_s is not None:
            loc = self.getplace(loc_s)
        else:
            loc = None
        c.execute("select attribute, value from attribution where attributed_to=?;", (name,))
        atts_s_l = c.fetchall()
        atts_l = [att for att in atts_s_l]
        th = Thing(name, loc, dict(atts_l))
        self.thingmap[name] = th
        return th

    def getthing(self, name):
        if self.thingmap.has_key(name):
            return self.thingmap[name]
        else:
            return self.loadthing(name)

    def thing_exists(self, name):
        if self.thingmap.has_key(name):
            return True
        else:
            self.c.execute("select count(*) from thing where name=?;", (name,))
            return self.c.fetchone()[0] > 0

    def mkattr(self, name, types=[], permitted=[], lower=None, upper=None, commit=self.defaultCommit):
        """Define an attribute type for LiSE items to have.

        Call this method to define an attribute that an item in the
        game can have. These attributes are not the same as the ones
        that every Python object has, although they behave similarly.

        You can define an attribute with just a name, but you might
        want to limit what values are acceptable for it. To do this,
        you may supply any of the other parameters:

        types is a list of strings. Valid types here are 'str', 'int',
        'float', and 'bool'.

        permitted is a list of values that the attribute is allowed to
        take on. Every value in this list will be permitted, even if
        it's the wrong type, or it falls out of the bounds.

        lower and upper should be numbers. Values of the attribute
        that are below lower or above upper will be rejected unless
        they're in the permitted list.

        """

        if False in [lower.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            lower=None
        if False in [upper.hasattr(s) for s in ["__lt__",
		"__eq__", "__gt__"]]:
            upper=None
        if typ not in self.typ.keys():
            typ=None
        self.c.execute("insert into attribute values (?, ?, ?, ?);", name, typ, lower, upper)
        if commit:
            self.conn.commit()

    def setupper(self, attr, upper, commit=self.defaultCommit):
        self.c.execute("select count(*) from attribute where name=?;", (attr,))
        if self.c.fetchone()[0] == 0:
            self.c.execute("insert into attribute values (?, ?, ?, ?);", (attr, None, None, upper))
        else:
            self.c.execute("update attribute set upper=? where name=?;", (upper, attr))
        if commit:
            self.conn.commit()

    def setlower(self, attr, lower, commit=self.defaultCommit):
        self.c.execute("select count(*) from attribute where name=?;", (attr,))
        if self.c.fetchone()[0] == 0:
            self.c.execute("insert into attribute values (?, ?, ?, ?)'", (attr, None, lower, None))
        else:
            self.c.execute("update attribute set lower=? where name=?;", (lower, attr))
        if commit:
            self.conn.commit()

    def setbounds(self, attr, lower, upper, commit=self.defaultCommit):
        self.c.execute("select count(*) from attribute where name=?;", (attr,))
        if self.c.fetchone()[0] == 0:
            self.c.execute("insert into attribute values (?, ?, ?, ?)'", (attr, None, lower, upper))
        else:
            self.c.execute("update attribute set lower=?, upper=? where name=?;", (lower, upper, attr))
        if commit:
            self.conn.commit()

    def settype(self, attr, typ):
        self.c.execute("select count(*) from attribute where name=?;", (attr,))
        if self.c.fetchone()[0] == 0:
            self.c.execute("insert into attribute values (?, ?, ?, ?)'", (attr, typ, None, None))
        else:
            self.c.execute("update attribute set type=? where name=?;", (typ, attr))
        if commit:
            self.conn.commit()

	def attributed(self, attr, item):
		if self.loaded_item.has_key(item):
			for att in item.attributes:
				if att[0] == attr:
					return True
			return False
		else:
			self.c.execute("select count(*) from attribution where attribute=? and attributed_to=?",
						   (attr, item))
			return self.c.fetchone()[0] > 0

    def attribute(self, attr, item, val, commit=self.defaultCommit):
        self.c.execute("select type, lower, upper from attribute where name=?", (attr,))
        # That might raise an exception due to the attribute not existing. That seems appropriate.
        (typ, lo, hi) = self.c.execute.fetchone()
        self.c.execute("select value from permitted where attribute=?", (attr,))
        perm = [ row[0] for row in c ]
        if val not in perm:
            if type(val) not in [ str, int, float, bool ]:
                raise TypeError("The attribute %s is of a type not handled by LiSE." % (val,))
            if typ == 'str' and type(val) != str:
                raise TypeError("The attribute %s expects a string, but you gave it %s." % (attr, type(val)))
            elif typ == 'int' and type(val) != int:
                raise TypeError("The attribute %s expects an integer, but you gave it %s." % (attr, type(val)))
            elif typ == 'float' and type(val) != float:
                raise TypeError("The attribute %s expects a float, but you gave it %s." % (attr, type(val)))
            elif typ == 'bool' and type(val) != bool:
                raise TypeError("The attribute %s expects a boolean, but you gave it %s." % (attr, type(val)))
            elif val < lo:
                raise ValueError("The attribute %s can't go below %d." % (val, lo))
            elif val > hi:
                raise ValueError("The attribute %s can't go above %d." % (val, hi))
            else:
                self.c.execute("insert into attribution values (?, ?, ?)", (attr, item, val))
                if commit:
                    self.conn.commit()

    def saveattr(self, attr, item, val, commit=self.defaultCommit):
        if self.attributed(attr, item):
            self.c.execute("update attribution set value=? where attribute=? and attributed_to=?",
                           (val, attr, item))
            if commit:
                self.conn.commit()
        else:
            self.attribute(attr, item, val, commit)

    def permitted(self, attr, val):
        self.c.execute("select count(*) from permitted_values where attribute=? and value=?",
                       (attr, val))
        return self.c.fetchone()[0] > 0

    def permit(self, attr, val, commit=self.defaultCommit):
        self.c.execute("insert into permitted_values values (?, ?)", (attr, val))
        if commit:
            self.conn.commit()

    def delthing(self, thing, commit=self.defaultCommit):
        c = self.c
        c.execute("delete from containment where contained=? or container=?", (thing, thing))
        c.execute("delete from thing where name=?", (thing,))
        if commit:
            self.conn.commit()

    def mkportal(self, name, orig, dest, commit=self.defaultCommit):
        self.c.execute("insert into portal values (?, ?, ?)", (name, orig, dest))
        if commit:
            self.conn.commit()

    def delportal(self, orig_or_name, dest=None, commit=self.defaultCommit):
        if dest is None:
            self.c.execute("delete from portal where name=?", (orig_or_name,))
        else:
            self.c.execute("delete from portal where orig=? and dest=?", (orig_or_name, dest))
        if commit:
            self.conn.commit()

    def saveportal(self, port, commit=self.defaultCommit):
        # This makes assumptions about the way portals are named.
        # Normally this won't be a problem, just so long as the user doesn't get "clever"
        # about names for things that aren't portals.
        #
        # They shouldn't have to name anything that goes in the database, really.
        self.c.execute("select count(*) from portal limit 1")
        orig = port.orig.name
        dest = port.dest.name
        name = "portal[%s->%s]" % (orig, dest)
        if self.c.fetchone()[0] == 0:
            return self.mkportal(name, orig, dest, commit)
        else:
            self.c.execute("update portal set orig=?, dest=? where name=?", (orig, dest, name))
            if commit:
                self.conn.commit()

    def has_spot(self, place):
        if self.spotmap.has_key(place):
            return True
        else:
            self.c.execute("select count(*) from spot where place=?;", (place,))
            return self.c.fetchone()[0] > 0

    def mkspot(self, place, x, y, r, graph, commit=self.defaultCommit):
        if not self.has_spot(place):
            self.c.execute("insert into spot values (?, ?, ?, ?, ?);", (place, x, y, r, graph))
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

    def savespot(self, spot, commit=self.defaultCommit):
        alreadyspots = self.c.execute("select count(*) from spot where name=?;", (spot.place.name,)).fetchone()[0]
        alreadyspotgraph = self.c.execute("select count(*) from spotgraph where name=?;", (spot.spotgraph.name,))[0]
        if alreadyspots != 0:
            self.c.execute("update spot set x=?, y=?, r=? where name=?;", (spot.place.name, spot.x, spot.y, spot.r))
        else:
            self.c.execute("insert into spot values (?, ?, ?, ?, ?);",
                           (spot.place.name, spot.x, spot.y, spot.r, spot.spotgraph.name))
        if alreadyspotgraph != 0:
            raise ValueError("Spots must remain assigned to the same Place and SpotGraph.")
        else:
            self.c.execute("insert into spotgraph values (?, ?);",
            (spot.spotgraph.name, spot.place.name))
		if commit:
			self.conn.commit()

    def delspot(self, spot, commit=self.defaultCommit):
        self.c.execute("delete from spot where place=?;", (spot.place.name,))
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
        
    def savespotgraph(self, graph):
        for spot in graph.spots:
            self.savespot(spot)

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

    def getallimg(self):
        self.c.execute("select name from imgfile")
        return [row[0] for row in c]

    def mkmenuitem(self, menu, idx, text, onclick, closer=True):
        self.c.execute("insert into menuitem values (?, ?, ?, ?, ?);", (menu, idx, text, onclick closer))

    def loadmenuitem(self, menu, idx):
        return self.getmenu(menu)[idx]

    def mkmenu(self, name, x, y, w, h, commit=self.defaultCommit):
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



import unittest
class DatabaseTestCase(unittest.TestCase):
	def setUp(self):
		self.db = Database(":memory:")
		self.db.init()
        for menu in basic_menus:
            self.db.mkmenu(*menu)
        for menuitem in basic_menu_items:
            self.db.mkmenuitem(*menuitem)
		self.db.c.execute("select * from place")
		self.db.mkattr("lbs", types=["float"], lower=0.0)
		self.db.mkattr("meterswide", types=["float"], lower=0.0)
		self.db.mkattr("height")
		self.db.mkattr("size", types=["str"])
		self.db.mkplace("myroom")
		self.db.mkthing("mydesk", "myroom", [("lbs", 50), ("meterswide", 1.2)])
		self.db.mkthing("thesky", atts=[("height", 9001)])
		self.db.mkplace("outside", portals=["myroom"], contents=["thesky"], atts=[("size", "too big")])
	def testthing(self):
		desk = self.db.getthing("mydesk")
		self.assertEqual(desk.name, "mydesk")
		myroom = self.db.getplace("myroom")
		self.assertIs(desk.location, myroom)
		self.assertEqual(desk["lbs"], 50)
		self.assertEqual(desk["meterswide"], 1.2)
    def testplace(self):
        myroom = self.db.getplace("myroom")
        outside = self.db.getplace("outside")
        self.assertIs(myroom, outside.portals[0].dest)
        self.assertIs(outside, myroom.portals[0].dest)
        self.putinto("thesky", "outside")
        sky = self.getthing("thesky")
        self.assertIn(sky, outside.contents)
	def runTest(self):
		self.testthing()
DatabaseTestCase().run()
