import sqlite3

conn = sqlite3.connect(':memory:') # For easy testing, don't let this last
c = conn.cursor() # what's a cursor?

# start with the map
c.execute('create table place (name unique, display_name)')
c.execute('create table portal (from_place, to_place, weight)')
c.execute('create table containment (contained, container)')
c.execute('create table spot (place, x, y)')
def mkplace(name=None, display_name=None, x_default=None, y_default=None, portals=[], contents=[]):
    # I'm not assuming that every place has a name; some might be
    # dynamically generated, and thence only have IDs.  It is indeed
    # permissible to have places that the player has no way of seeing
    # or otherwise knowing about, in which case name and display_name
    # are null, but those places may still contain things and portals.
    c.execute('insert into place values (?, ?)', (name, display_name))
    pid = c.lastrowid
    for portal in portals:
        if not hasattr(portal, 'orig'):
            # This would be the expected thing, really, but if for
            # some reason the portal already has an origin I'll use it
            orig = pid
        else:
            orig = portal.orig.rowid
        dest = portal.dest.rowid
        c.execute('insert into portal values(?,?)', (orig, dest))
    for item in contents:
        # If it's an integer, assume it's a rowid
        if type(item) == type(1):
            iid = item
        else:
            # Otherwise, it's a Thing
            iid = item.rowid
        c.execute('insert into containment values (?,?)',(iid,pid))
    if None not in [x_default, y_default]:
        c.execute('insert into spot values (?, ?, ?)', (pid, x_default, y_default))
