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

# start with the map
c.execute('create table place (name unique, display_name, desc)')
# places are much like things in the database schema; but only places
# can have portals.
c.execute('create table portal (from_place, to_place, weight)')
c.execute('create table containment (contained, container)')
c.execute('create table spot (place, x, y, r, spotgraph)')
c.execute('create table thing (name unique, display_name, desc)')
c.execute('create table attribute (name unique, display_name, value)')
c.execute('create table attribution (attribute, attributed_to)')
def mkplace(name=None, display_name=None, desc=None, x_default=None, y_default=None, portals=[], contents=[], attributes=[]):
    # I'm not assuming that every place has a name; some might be
    # dynamically generated, and thence only have IDs.  It is indeed
    # permissible to have places that the player has no way of seeing
    # or otherwise knowing about, in which case name and display_name
    # are null, but those places may still contain things and portals.
    c.execute('insert into place values (?, ?, ?)', (name, display_name, desc))
    pid = c.lastrowid
    for portal in portals:
        if type(portal) is type(''):
            c.execute('select * from place where name=?', portal)
            orig = pid
            dest = c.lastrowid
        elif type(portal) is type(1):
            orig = pid
            dest = portal
        elif isinstance(portal, Place):
            orig = pid
            dest = portal.rowid
        elif isinstance(portal, Portal):
            if not hasattr(portal, 'orig'):
                # This would be the expected thing, really, but if for
                # some reason the portal already has an origin I'll use it
                orig = pid
                dest = portal.dest.rowid
            else:
                orig = portal.orig.rowid
        else:
            raise TypeError

        c.execute('insert into portal values(?,?)', (orig, dest))
    for item in contents:
        # If it's an integer, assume it's a rowid
        if type(item) == type(1):
            iid = item
        else:
            # Otherwise, it's a Thing
            iid = item.rowid
        c.execute('insert into containment values (?,?)',(iid,pid))
    for atr in attributes:
        if type(atr) == type(1):
            aid = atr
        else:
            aid = atr.rowid
        c.execute('insert into attribution values (?,?)', (aid, pid))
    if None not in [x_default, y_default]:
        c.execute('insert into spot values (?, ?, ?)', (pid, x_default, y_default))
def getplace(name):
    c.execute('select * from place where name=?', name)
    firstrow = c.fetchone()
    if firstrow is None:
        # no such place
        return None
    (name, display_name) = firstrow
    pid = c.lastrowid
    if loaded_place.has_key(pid):
        # no need to load it again, now
        return loaded_place[pid]
    c.execute('select * from portal where from_place=?', pid)
    portals = [port[1] for port in c]
    c.execute('select * from containment where container=?', pid)
    contents = [item[0] for item in c]
    c.execute('select * from spot where place=?', pid)
    spot = c.fetchone()
    p = Place(name, display_name) # I think I might have to handle nulls special
    p.rowid = pid
    loaded_place[pid] = p # must do this now, though the place is not
                          # finished yet, lest the recursive call
                          # below fail ever to happen upon a loaded
                          # place
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
def getthing(it):
    if isinstance(it, Thing):
        return it
    elif type(it) is str:
        c.execute('select * from thing where name=?',it)
    elif type(it) is int:
        c.execute('select * from thing where rowid=?', it)
    (name, display_name) = c.fetchone()
    tid = c.lastrowid
    c.execute('select * from attribution where attributed_to=?', tid)
def getattribute(it):
    pass
def insert_thing(thing, place):
    pass
def remove_thing(thing, place):
    pass
def mkportal(orig, dest):
    pass
def delportal(orig, dest):
    pass
def mkspot(place, x, y, r, graph):
    pass
def delspot(spot):
    pass
