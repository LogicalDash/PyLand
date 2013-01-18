import sys, os
sys.path.append(os.curdir)

import sqlite3
from place import Place
from portal import Portal
from widgets import Spot
from thing import Thing
from attrcheck import *


class Database:
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        self.place = {}
        self.portal = {}
        self.contents = {}
        self.container = {}
        self.spot = {}
        self.img = {}
        self.spotgraph = {}
        self.thing= {}


    def init(self):
        c = self.c
        c.execute("create table item (name primary key);")
        # items shall cover everything that has attributes.
        # items may or may not correspond to anything in the gameworld.
        # they may be places. they may be things. they may be people.
        c.execute("create table place (name, foreign key(name) references item(name));")
        c.execute("create table thing (name, foreign key(name) references item(name));")
        c.execute("create table portal (from_place, to_place, weight default 0, foreign key(from_place) references place(name), foreign key(to_place) references place(name), check(from_place<>to_place));")
        c.execute("create table containment (contained, container, foreign key(contained) references item(name), foreign key(container) references item(name), check(contained<>container));")
        c.execute("create table spot (place, x, y, r, spotgraph, foreign key(place) references place(name));")
        c.execute("create table attribution (attribute, attributed_to, value, foreign key(attribute) references permitted_values(attribute), foreign key(attributed_to) references item(name), foreign key(value) references permitted_values(value));")
        c.execute("create table attribute (name, type, lower, upper, foreign key(type) references types(name));")
        c.execute("create table types (name);")
        c.execute("insert into types values ('int'), ('bool'), ('str'), ('float');")
        c.execute("create table permitted (attribute, value, foreign key(attribute) references attribute(name));")
        c.execute("create table img (name, path, rltile);")
        c.execute("create table spotgraph (graph, spot, foreign key(spot) references place(name));")
        # I think maybe I will want to actually store sprites in the database eventually.
        # Later...
        self.conn.commit()

    def initialized(self):
        try:
            for tab in ["thing", "place", "attribute", "img", "spotgraph"]:
                self.c.execute("select * from ?", (tab,))
        except:
            return False
        return True

    def loadcontainer(self, container):
        self.c.execute("select contained from containment where container=?", (container,))
        r = self.c.fetchall()
        self.contents[container] = r
        for contained in r:
            self.container[contained] = container
        return r

    def loadcontained(self, contained):
        self.c.execute("select container from containment where contained=?", (contained,))
        r = self.c.fetchone()
        if self.contents.has_key(r):
            if contained not in self.contents[r]:
                self.contents[r].append(contained)
        self.container[contained] = r
        return r

    def getcontents(self, container):
        if self.contents.has_key(container):
            return self.contents[container]
        else:
            return self.loadcontainer(container)

    def getcontainer(self, contained):
        if self.container.has_key(contained):
            return self.container[contained]
        else:
            return self.loadcontained(contained)

    def mkplace(self, name, portals=[], contents=[], atts=[], commit=True):
        # Places should always exist in the database before they are Python objects.
        c = self.c
        c.execute("insert into item values (?)", (name,))
        c.execute("insert into place values (?)", (name,))
        for portal in portals:
            c.execute("insert into portal values (?, ?)", [name, dest])
        for item in contents:
            c.execute("insert into containment values (?, ?)", [item, name])
        for atr in atts:
            self.attribute(atr, name, value, commit=False)
        if commit:
            self.conn.commit()
        return self.loadplace(name)

    def loadplace(self, name):
        c = self.c
        c.execute("select * from place where name=?", (name,))
        firstrow = c.fetchone()
        if firstrow is None:
            # no such place
            return None
        name = firstrow[0]
        c.execute("select to_place from portal where from_place=?", (name,))
        portals = c.fetchall()
        c.execute("select contained from containment where container=?", (name,))
        contents = c.fetchall()
        p = Place(name) # I think I might have to handle nulls special
        self.place[name] = p
        for port in portals:
            d = self.getplace(port)
            p.connect_to(d)
        for item in contents:
            th = self.getthing(item)
            p.addthing(th)
        return p

    def saveplace(self, place, commit=True):
        # This time it is an actual Place object. Presumably from self.place.
        name = place.name

        if self.contents.has_key(name):
            self.c.execute("update containment set container=? where contained=?",
                           (self.contents[name], name))
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
        # This uses "or replace" which is apparently not standard SQL.
        for portal in place.portals:
            self.c.execute("insert or replace into portal values (?, ?, ?)",
                           (name, portal.dest, portal.weight))
        # Now add all the contained things
        for th in place.contents:
            self.savething(th, commit=False) # Won't this have commits in it? Is that a problem?
            self.c.execute("insert or replace into containment values (?, ?)", (th.name, name))
        for att in place.attributes:
            self.c.execute("insert or replace into attribution values (?, ?, ?)", (att,))
        if commit:
            self.conn.commit()

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if self.place.has_key(name):
            return self.place[name]
        else:
            return self.loadplace(name)

    def place_exists(self, name):
        if self.place.has_key(name):
            return True
        self.c.execute("select count(*) from place where name=?", (name,))
        return c.fetchone()[0] > 0

    def mkthing(self, name, loc="", atts=[], commit=True):
        c = self.c
        c.execute("insert into item values (?)", (name,))
        c.execute("insert into thing values (?)", (name,))
        attfmt = ','.join(["(?, ?, ?)" for att in atts])
        attval = []
        for att in atts:
            attval.append(att[0])
            attval.append(name)
            attval.append(att[1])
        c.execute("insert into attribution values " + attfmt, attval)
        # Only then do I add the thing to a location, because it's
        # possible the location has some restrictions that will deny this
        # thing entry, because of its attributes.
        c.execute("insert into containment values (?, ?)", (loc, name))
        if commit:
            self.conn.commit()

    def savething(self, th, commit=True):
        self.c.execute("insert or replace into item values (?)", (th.name,))
        self.c.execute("insert or replace into thing values (?)", (th.name,))
        self.c.execute("insert or replace into containment values (?, ?)",
                       (th.location.name, th.name))
        for attr in th.attributes:
            self.c.execute("insert or replace into attribution values (?, ?, ?)", (attr,))
        if commit:
            self.conn.commit()

    def loadthing(self, name):
        c = self.c
        c.execute("select container from containment where contained=?", (name,))
        loc_s = c.fetchone()
        if loc_s is not None:
            loc = self.getplace(loc_s)
        else:
            loc = None
        c.execute("select attribute, value from attribution where attributed_to=?", (name,))
        atts_s_l = c.fetchall()
        atts_l = [att for att in atts_s_l]
        th = Thing(name, loc, dict(atts_l))
        self.thing[name] = th
        return th

    def getthing(self, name):
        if self.thing.has_key(name):
            return self.thing[name]
        else:
            return self.loadthing(name)

    def thing_exists(self, name):
        if self.thing.has_key(name):
            return True
        else:
            self.c.execute("select count(*) from thing where name=?", (name,))
            return self.c.fetchone()[0] > 0

    def insertthing(self, name, into, commit=True):
        self.c.execute("insert or replace into containment values (?, ?)", (name, into))

        if self.thing.has_key(name):
            th = self.thing[name]
            if th not in self.contents[into]:
                self.contents[into].append(th)

        if commit:
            self.conn.commit()


    def mkattribute(self, name, types=[], permitted=[], lower=None, upper=None, commit=True):
        """
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
        "__eq__", "__gt__"]]: upper=None

        if commit:
            self.conn.commit()


    def loadattr(self, attr):
        self.c.execute("select value from permitted_values where attribute=?", (attr,))
        r = self.c.fetchall()
        self.loaded_permitted[attr] = r
        return r

    def getattr(self, attr):
        if self.loaded_permitted.has_key(attr):
            return self.loaded_permitted[attr]
        else:
            return self.loadattr(attr)

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

    def attribute(self, attr, item, val, commit=True):
        self.c.execute("insert into attribution values (?, ?, ?)", (attr, item, val))
        if commit:
            self.conn.commit()

    def permitted(self, attr, val):
        self.c.execute("select count(*) from permitted_values where attribute=? and value=?",
                       (attr, val))
        return self.c.fetchone()[0] > 0

    def permit(self, attr, val, commit=True):
        self.c.execute("insert into permitted_values values (?, ?)", (attr, val))
        if commit:
            self.conn.commit()

    def delthing(self, thing, commit=True):
        c = self.c
        c.execute("delete from containment where contained=? or container=?", (thing, thing))
        c.execute("delete from thing where name=?", (thing,))
        if commit:
            self.conn.commit()

    def mkportal(self, orig, dest, commit=True):
        if not self.portal_connecting(orig, dest):
            self.c.execute("insert into portal values (?, ?)", (orig, dest))
        if commit:
            self.conn.commit()

    def delportal(self, orig, dest, commit=True):
        self.c.execute("delete from portal where orig=? and dest=?", (orig, dest))
        if commit:
            self.conn.commit()

    def has_spot(self, place):
        if self.spot_loaded.has_key(place):
            return True
        else:
            self.c.execute("select * from spot where place=?", (place,))
            return self.c.fetchone() is not None

    def mkspot(self, place, x, y, r, graph, commit=True):
        if not self.has_spot(place):
            self.c.execute("insert into spot values (?,?,?,?,?)", (place, x, y, r, graph))
            if commit:
                self.conn.commit()

    def loadspot(self, place):
        self.c.execute("select * from spot where place=?", (place,))
        q = self.c.fetchone()
        r = Spot(self.getplace(q[0]), int(q[1]), int(q[2]), int(q[3]), self.getgraph(q[4]))
        self.getgraph(q[4]).add_spot(r)
        self.spot[place] = r
        return r

    def getspot(self, placen):
        if self.spot.has_key(placen):
            return self.spot[placen]
        else:
            return self.loadspot(placen)

    def savespot(self, spot, commit=True):
        self.c.execute("insert or replace into spot values (?, ?, ?, ?, ?)",
                       (spot.place.name, spot.x, spot.y, spot.r, spot.spotgraph.name))
        self.c.execute("insert or replace into spotgraph values (?, ?)",
                       (spot.spotgraph.name, spot.place.name))
        if commit:
            self.conn.commit()

    def delspot(self, spot, commit=True):
        self.c.execute("delete from spot where place=?", (spot.place.name,))
        if commit:
            self.conn.commit()

    def loadspotgraph(self, graphn):
        self.c.execute("select spot from spotgraph where graph=?", (graphn,))
        g = SpotGraph()
        spotgraph[graphn] = g
        for spotstring in c:
            g.add_spot(self.getspot(spotstring))
        return g

    def getspotgraph(self, graphn):
        if spotgraph.has_key(graphn):
            return self.spotgraph[graphn]
        else:
            return self.loadgraph(graphn)

    def savespotgraph(self, graph):
        for spot in graph.spots:
            self.savespot(spot)

    def mkimg(self, name, path, rl=False):
        self.c.execute("insert into img values (?, ?, ?)", (name, path, rl))

    def loadrltile(self, name, path):
        badimg = pyglet.resource.image(path)
        badimgd = badimg.get_image_data()
        bad_rgba = badimgd.get_data('RGBA', badimgd.pitch)
        badimgd.set_data('RGBA', badimgd.pitch, bad_rgba.replace('\xffGll','\x00Gll').replace('\xff.', '\x00.'))
        self.img[name] = badimgd.get_texture()
        return self.img[name]

    def loadimgfile(self, name, path):
        tex = pyglet.resource.image(path).get_image_data().get_texture()
        self.img[name] = tex
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
        if self.img.has_key(name):
            return self.img[name]
        else:
            return self.loadimg(name)

    def getallimg(self):
        self.c.execute("select name from imgfile")
        return [row[0] for row in c]


import unittest
class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.init()
        self.db.c.execute("select * from place")
        self.db.mkattribute("lbs", types=["float"], lower=0.0)
        self.db.mkattribute("meterswide", types=["float"], lower=0.0)
        self.db.mkattribute("height")
        self.db.mkattribute("size", types=["str"])
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
    def runTest(self):
        self.testthing()
DatabaseTestCase().run()
