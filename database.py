import sqlite3
from place import Place
from portal import Portal
from widgets import Spot
from thing import Thing

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
