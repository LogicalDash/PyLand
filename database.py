import sqlite3
from place import Place
from portal import Portal
from widgets import Spot
from thing import Thing

<<<<<<< HEAD

class Database:
    def __init__(self, dbfile):
        self.conn = sqlite3.connect(dbfile)
        self.c = self.conn.cursor()
        self.loaded_place = {}
        self.loaded_portal = {}
        self.loaded_contents = {}
        self.loaded_container = {}
        self.loaded_spot = {}
        self.loaded_item = {}
        self.loaded_graphic = {}
        self.loaded_graph = {}
        self.loaded_thing={}

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
        c.execute('create table imgfile (name, path, rltile);')
        c.execute('create table spotgraph (graph, spot, foreign key(spot) references place(name));')
        # I think maybe I will want to actually store sprites in the database eventually.
        # Later...
        self.conn.commit()

    def loadcontainer(self, container):
        self.c.execute("select contained from containment where container='?'", (container,))
        r = self.c.fetchall()
        self.loaded_contents[container] = r
        for contained in r:
            self.loaded_container[contained] = container
        return r

    def loadcontained(self, contained):
        self.c.execute("select container from containment where contained='?'", (contained,))
        r = self.c.fetchone()
        if self.loaded_contents.has_key(r):
            if contained not in self.loaded_contents[r]:
                self.loaded_contents[r].append(contained)
        self.loaded_container[contained] = r
        return r

    def getcontents(self, container):
        if self.loaded_contents.has_key(container):
            return self.loaded_contents[container]
        else:
            return self.loadcontainer(container)

    def getcontainer(self, contained):
        if self.loaded_container.has_key(contained):
            return self.loaded_container[contained]
        else:
            return self.loadcontained(contained)

    def mkplace(self, name, portals=[], contents=[], atts=[], commit=True):
        # Places should always exist in the database before they are Python objects.
        c = self.c
        c.execute("insert into item values ('?')", (name,))
        c.execute("insert into place values ('?')", (name,))
        for portal in portals:
            c.execute("insert into portal values ('?', '?')", [name, dest])
        for item in contents:
            c.execute("insert into containment values ('?', '?')", [item, name])
        for atr in atts:
            self.attribute(atr, name, value, commit=False)
        if commit:
            self.conn.commit()
        return self.loadplace(name)

    def loadplace(self, name):
        c = self.c
        c.execute("select * from place where name='?'", (name,))
        firstrow = c.fetchone()
        if firstrow is None:
            # no such place
            return None
        name = firstrow[0]
        c.execute("select to_place from portal where from_place='?'", (name,))
        portals = c.fetchall()
        c.execute("select contained from containment where container='?'", (name,))
        contents = c.fetchall()
        p = Place(name) # I think I might have to handle nulls special
        self.loaded_place[name] = p
        for port in portals:
            d = self.getplace(port)
            p.connect_to(d)
        for item in contents:
            th = self.getthing(item)
            p.addthing(th)
        return p

    def saveplace(self, place, commit=True):
        # This time it is an actual Place object. Presumably from self.loaded_place.
        name = place.name

        if self.loaded_contents.has_key(name):
            self.c.execute("update containment set container='?' where contained='?'",
                           (self.loaded_contents[name], name))
        # delete portals from the database when they no longer exist.
        ports = [port.dest for port in place.portals]
        self.c.execute("select to_place from portal where from_place='?'", (name,))
        oldports = self.c.fetchall()
        for oldie in oldports:
            if oldie not in ports:
                self.c.execute("delete from portal where from_place='?' and to_place='?'",
                               (name, oldie))
        # overwrite all the old ports with the new ones.
        # Handling insert and update separately seems to result in more queries.
        # This uses "or replace" which is apparently not standard SQL.
        for portal in place.portals:
            self.c.execute("insert or replace into portal values ('?', '?', '?')",
                           (name, portal.dest, portal.weight))
        # Now add all the contained things
        for th in place.contents:
            self.savething(th, commit=False) # Won't this have commits in it? Is that a problem?
            self.c.execute("insert or replace into containment values ('?', '?')", (th.name, name))
        for att in place.attributes:
            self.c.execute("insert or replace into attribution values ('?', '?', '?')", (att,))
        if commit:
            self.conn.commit()

    def getplace(self, name):
        # Remember that this returns the *loaded* version, if there is one.
        if self.loaded_place.has_key(name):
            return self.loaded_place[name]
        else:
            return self.loadplace(name)

    def place_exists(self, name):
        if self.loaded_place.has_key(name):
            return True
        self.c.execute("select * from place where name='?'", (name,))
        return self.c.rowcount > 0 # There certainly SHOULDN'T be more
                                   # than one, but this is not the
                                   # correct method in which to check
                                   # that

    def mkthing(self, name, loc="", atts=[], commit=True):
        c = self.c
        c.execute("insert into item values ('?')", (name,))
        c.execute("insert into thing values ('?')", (name,))
        attfmt = ','.join(["('?', '?', '?')" for att in atts])
        attval = []
        for att in atts:
            attval.append(att[0])
            attval.append(name)
            attval.append(att[1])
        c.execute("insert into attribution values " + attfmt, attval)
        # Only then do I add the thing to a location, because it's
        # possible the location has some restrictions that will deny this
        # thing entry, because of its attributes.
        c.execute("insert into containment values ('?', '?')", (loc, name))
        if commit:
            self.conn.commit()

    def savething(self, th, commit=True):
        self.c.execute("insert or replace into item values ('?')", (th.name,))
        self.c.execute("insert or replace into thing values ('?')", (th.name,))
        self.c.execute("insert or replace into containment values ('?', '?')",
                       (th.location.name, th.name))
        for attr in th.attributes:
            self.c.execute("insert or replace into attribution values ('?', '?', '?')", (attr,))
        if commit:
            self.conn.commit()

    def loadthing(self, name):
        c = self.c
        c.execute("select container from containment where contained='?'", (name,))
        if c.rowcount > 0:
            loc_s = c.fetchone()
            loc = self.getplace(loc_s)
        else:
            loc = None
        c.execute("select attribute, value from attribution where attributed_to='?'", (name,))
        atts_s_l = c.fetchall()
        atts_l = [att for att in atts_s_l]
        th = Thing(name, loc, dict(atts_l))
        self.loaded_thing[name] = th
        return th

    def getthing(self, name):
        if self.loaded_thing.has_key(name):
            return self.loaded_thing[name]
        else:
            return self.loadthing(name)

    def thing_exists(self, name):
        if self.loaded_thing.has_key(name):
            return True
        else:
            self.c.execute("select * from thing where name='?'", (name,))
            return self.c.rowcount > 0

    def insertthing(self, name, into, commit=True):
        self.c.execute("insert or replace into containment values ('?', '?')", (name, into))

        if self.loaded_thing.has_key(name):
            th = self.loaded_thing[name]
            if th not in self.loaded_contents[into]:
                self.loaded_contents[into].append(th)

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

        if False in [upper.hasattr(s) for s in ["__lt__", "__eq__", "__gt__"]]:
            upper=None

        if commit:
            self.conn.commit()


    def loadattr(self, attr):
        self.c.execute("select value from permitted_values where attribute='?'", (attr,))
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
            self.c.execute("select * from attribution where attribute='?' and attributed_to='?'",
                           (attr, item))
            return self.c.rowcount > 0

    def attribute(self, attr, item, val, commit=True):
        self.c.execute("insert into attribution values ('?', '?', '?')", (attr, item, val))
        if commit:
            self.conn.commit()

    def permitted(self, attr, val):
        self.c.execute("select from permitted_values where attribute='?' and value='?'",
                       (attr, val))
        return self.c.rowcount > 0

    def permit(self, attr, val, commit=True):
        self.c.execute("insert into permitted_values values ('?', '?')", (attr, val))
        if commit:
            self.conn.commit()

    def delthing(self, thing, commit=True):
        c = self.c
        c.execute("delete from containment where contained='?' or container='?'", (thing, thing))
        c.execute("delete from thing where name='?'", (thing,))
        if commit:
            self.conn.commit()

    def mkportal(self, orig, dest, commit=True):
        if not self.portal_connecting(orig, dest):
            self.c.execute("insert into portal values ('?', '?')", (orig, dest))
        if commit:
            self.conn.commit()

    def delportal(self, orig, dest, commit=True):
        self.c.execute("delete from portal where orig='?' and dest='?'", (orig, dest))
        if commit:
            self.conn.commit()

    def has_spot(self, place):
        if self.spot_loaded.has_key(place):
            return True
        else:
            self.c.execute("select * from spot where place='?'", (place,))
            return self.c.fetchone() is not None

    def mkspot(self, place, x, y, r, graph, commit=True):
        if not self.has_spot(place):
            self.c.execute("insert into spot values ('?','?','?','?','?')", (place, x, y, r, graph))
            if commit:
                self.conn.commit()

    def loadspot(self, place):
        self.c.execute("select * from spot where place='?'", (place,))
        q = self.c.fetchone()
        r = Spot(self.getplace(q[0]), int(q[1]), int(q[2]), int(q[3]), self.getgraph(q[4]))
        self.getgraph(q[4]).add_spot(r)
        self.loaded_spot[place] = r
        return r

    def getspot(self, placen):
        if self.loaded_spot.has_key(placen):
            return self.loaded_spot[placen]
        else:
            return self.loadspot(placen)

    def savespot(self, spot, commit=True):
        self.c.execute("insert or replace into spot values ('?', '?', '?', '?', '?')",
                       (spot.place.name, spot.x, spot.y, spot.r, spot.spotgraph.name))
        self.c.execute("insert or replace into spotgraph values ('?', '?')",
                       (spot.spotgraph.name, spot.place.name))
        if commit:
            self.conn.commit()

    def delspot(self, spot, commit=True):
        self.c.execute("delete from spot where place='?'", (spot.place.name,))
        if commit:
            self.conn.commit()

    def loadgraph(self, graphn):
        self.c.execute("select spot from spotgraph where graph='?'", (graphn,))
        g = SpotGraph()
        self.loaded_graph[graphn] = g
        for spotstring in c:
            g.add_spot(self.getspot(spotstring))
        return g

    def getgraph(self, graphn):
        if self.loaded_graph.has_key(graphn):
            return self.loaded_graph[graphn]
        else:
            return self.loadgraph(graphn)

import unittest
class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.init()
        self.db.c.execute("select * from place")
        self.db.mkattribute("lbs", types=["float"], lower=0.0)
        self.db.mkattribute("meterswide", types=["float"], lower=0.0)
        self.db.mkattribute("height")
        self.db.mkattribute("size", types=["str"]
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

=======
conn = sqlite3.connect(':memory:') # For easy testing, don't let this last
c = conn.cursor() # what's a cursor?
loaded_place = {}
loaded_portal = {}
loaded_containment = {}
loaded_spot = {}
loaded_item = {}

c.execute('create table item (name primary key)')
# items shall cover everything that has attributes.
# items may or may not correspond to anything in the gameworld.
# they may be places. they may be things. they may be people.
c.execute('create table place (name, foreign key(name) references item(name)')
c.execute('create table thing (name, foreign key(name) references item(name)')
c.execute('create table portal (from_place, to_place, weight default 0, foreign key(from_place) references place(name), foreign key(to_place) references place(name), check(from_place<>to_place))') 
c.execute('create table containment (contained, container, foreign key(contained) references item(name), foreign key(container) references item(name), check(contained<>container))') 
c.execute('create table spot (place, x, y, r, spotgraph, foreign key(place) references place(name))')
c.execute('create table attribute (name primary key)')
c.execute('create table attribution (attribute, attributed_to, value, foreign key(attribute) references attribute(name), foreign key(attributed_to) references item(name))') 
c.execute('create table permitted_values (attribute, value, foreign key(attribute) references attribute(name))') 
def mkplace(name, portals=[], contents=[], attributes=[], x_default=None, y_default=None):
    c.execute('insert into place values (?)', name)
    for portal in portals:
        if type(portal) is type(''):
            orig = name
            dest = portal
        elif type(portal) is type(1):
            c.execute('select from place where rowid=?', portal
            orig = name
            dest = c.fetchone()[0]
        elif isinstance(portal, Place):
            orig = name
            dest = portal.name
        elif isinstance(portal, Portal):
            if not hasattr(portal, 'orig'):
                # This would be the expected thing, really, but if for
                # some reason the portal already has an origin I'll use it
                orig = name
                dest = portal.dest.name
            else:
                orig = portal.orig.name
                dest = portal.dest.name
        else:
            raise TypeError

        c.execute('insert into portal values(?,?)', (orig, dest))
    for item in contents:
        c.execute('insert into containment values (?,?)',(item,name))
    for atr in attributes:
        c.execute('insert into attribution values (?,?)', (atr,name))
    if None not in [x_default, y_default]:
        c.execute('insert into spot values (?, ?, ?)', (name, x_default, y_default))
def getplace(name):
    c.execute('select * from place where name=?', name)
    firstrow = c.fetchone()
    if firstrow is None:
        # no such place
        return None
    name = firstrow[0]
    c.execute('select * from portal where from_place=?', pid)
    portals = [port[1] for port in c]
    c.execute('select * from containment where container=?', pid)
    contents = [item[0] for item in c]
    c.execute('select * from spot where place=?', pid)
    spot = c.fetchone()
    p = Place(name) # I think I might have to handle nulls special
    p.rowid = pid
    for port in portals:
        dest = getplace(port)
        if dest is not None:
            p.connect_to(dest)
    for item in contents:
        thing = getthing(item)
        if thing is not None:
            p.additem(thing)
    if spot is not None:
        realspot = Spot(p, spot[1], spot[2], spot[3], spot[4])
        p.spot = realspot # I find this more elegant than returning a
                          # tuple of place and spot.
    return p
def mkthing(name, loc, atts):
    c.execute('insert into item values (?)', (name))
    c.execute('insert into thing values (?)', (name))
    attfmt = ','.join(['(?, ?, ?)' for att in atts])
    attval = []
    for att in atts:
        attval.append(att[0])
        attval.append(name)
        attval.append(att[1])
    c.execute('insert into attribution values ' + attfmt, attval)
    # Only then do I add the thing to a location, because it's
    # possible the location has some restrictions that will deny this
    # thing entry, because of its attributes.
    c.execute('insert into containment values (?, ?)', (loc, name))
def mkattribute(name, permitted_vals=[]):
    c.execute('insert into attribute values (?)', name)
    valfmt = ','.join(['(?, ?)' for val in permitted_vals])
    valval = []
    for val in permitted_vals:
        valval.append(name)
        valval.append(val)
    c.execute('insert into permitted_values values ' + valfmt, valval)
def attributed(attr, item):
    c.execute('select * from attribution where attribute=? and attributed_to=?',(attr, item))
    return c.fetchone() is not None
def attribute(attr, item, val):
    if not attributed(aid, iid) and val_permitted(aid, val):
        c.execute('insert into attribution values (?, ?, ?)', (aid, iid, val))
def val_permitted(aid, val):
    c.execute('select * from permitted_vals where aid=? and val=?', (aid,val))
    return c.fetchone() is not None
def permit_val(aid, val):
    if not val_permitted(aid, val):
        c.execute('insert into permitted_vals values (?, ?)', (aid, val))
def getthing(it):
    if isinstance(it, Thing):
        return it
    elif type(it) is str:
        c.execute('select * from thing where name=?',it)
    elif type(it) is int:
        c.execute('select * from thing where rowid=?', it)
    name = c.fetchone()[0]
    tid = c.lastrowid
    atts = attribute_dict(tid)
    c.execute('select container from containment where contained=?', tid)
    loc = c.fetchone()[0]
    th = Thing(loc, atts)
    th.rowid = tid
    return th
def getattributes(tid):
    c.execute('select attribute, value from attributions where attributed_to=?', tid)
    return [row for row in c]
def attribute_dict(tid):
    d = {}
    for att in attributes_of(tid):
        d[att[0]] = att[1]
    return d
def permitted_vals(aid):
    c.execute('select value from permitted_vals where attribute=?', aid)
    return [val for val in c]
def getattribute(name):
    c.execute('select * from attribute where name=?', name)
    aid = c.lastrowid
    c.execute('select value from permitted_vals where attribute=?', aid)
    vl = [row[0] for row in c]
    att = Attribute(name, vl)
    att.rowid = aid
    return att
def is_in(item, place):
    c.execute('select * from containment where cointained=? and container=?', (item, place))
    return c.fetchone() is not None
def whereis(thing):
    c.execute('select container from containment where contained=?', thing)
    r = c.fetchone()
    if r is not None:
        return r[0]
    else:
        return None
def insert_thing(thing, container):
    # Part of the definition of thingness is that you can only be in
    # one container at a time.
    if is_contained_by(thing, container):
        return
    curloc = thing_loc(thing)
    if curloc is not None:
        # be liberal in what you accept, and move the thing to the new container
        c.execute('delete from containment where container=? and contained=?', (curloc, thing))
    c.execute('insert into containment values (?, ?)', (thing, container))
def insert_item(item, container):
    # now I'm not inserting a thing, just an item, so it's allowed to
    # be in two containers at once... but, I still don't want to insert it
    # twice
    if is_contained_by(item, container):
        return
    c.execute('insert into containment values (?,?)', (item, container))
def remove_item(thing, container):
    c.execute('delete from containment where contained=? and container=?', (thing, container))
def delthing(thing):
    c.execute('delete from containment where contained=?', thing)
    c.execute('delete from thing where rowid=?', thing)
def portal_exists(orig, dest):
    c.execute('select * from portal where orig=? and dest=?', (orig, dest))
    return c.fetchone() is not None
def mkportal(orig, dest):
    if not portal_connecting(orig, dest):
        c.execute('insert into portal values (?, ?)', (orig, dest))
def delportal(orig, dest):
    c.execute('delete from portal where orig=? and dest=?', (orig, dest))
def has_spot(place):
    c.execute('select * from spot where place=?', place)
    return c.fetchone() is not None
def mkspot(place, x, y, r, graph):
    if not has_spot(place):
        c.execute('insert into spot values (?,?,?,?,?)', (place, x, y, r, graph))
def delspot(spot):
    c.execute('delete from spot where place=?', spot.place.name)
>>>>>>> parent of bf4e7d4... There were a lot of singlequotes where there should have been doublequotes, and no quotes around ? tokens, even when I knew I was going to put a string there.
