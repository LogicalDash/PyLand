import igraph
from thing import Thing

class Route:
    def __init__(self, steplist, thing, dest):
        self.steplist = steplist
        self.prevsteps = []
        self.thing = thing
        self.dest = dest
        self.steplist.sort()
    def getstep(self, i):
        return self.steplist[i]
    def curstep(self):
        return self.getstep(0)
    def curprog(self):
        return self.curstep()[1]
    def curport(self):
        return self.curstep()[2]
    def prevstep(self):
        return self.prevsteps[-1]
    def move(self, prop, stepped=[]):
        """Call this with a float argument to progress the specified
        amount toward the next step. If that makes the current
        progress go to 1.0 or above, I'll move the thing to the new
        place. I will return a list of steps completed with this
        call--plus the step presently in progress on the very end.

        """
        (i, prog, port) = self.curstep()
        newprog = prog + prop
        if newprog >= 1.0:
            newstep = self.curstep()
            del self.steplist[0]
            self.prevsteps.append(newstep)
            stepped.append(newstep)
            newprog -= 1.0
            return self.move(nuprog, stepped)
        elif newprog < 0.0:
            newstep = self.prevsteps[-1]
            del self.prevsteps[-1]
            newprog += 1.0
            newstep[1] = newprog
            self.steplist.insert(0, newstep)
            stepped.append(newstep)
            return self.move(newprog, stepped)
        else:
            stepped.append((i, newprog, port))
            self.steplist[0] = (i, newprog, port)
            return stepped

class Portal:
    # Portals would be called 'exits' if that didn't make it
    # perilously easy to exit the program by mistake. They link
    # one place to another. They are one-way; if you want two-way
    # travel, make another one in the other direction. Each portal
    # has a 'weight' that probably represents how far you have to
    # go to get to the other side; this can be zero. Portals are
    # likely to impose restrictions on what can go through them
    # and when. They might require some ritual to be performed
    # prior to becoming passable, e.g. opening a door before
    # walking through it. They might be diegetic, in which case
    # they point to a Thing that the player can interact with, but
    # the portal itself is not a Thing and does not require one.
    # 
    # These are implemented as methods, although they
    # will quite often be constant values, because it's not much
    # more work and I expect that it'd cause headaches to be
    # unable to tell whether I'm dealing with a number or not.
    def __init__(self, name, origin, destination, attributes={}, avatar=None, weight=0):
        self.name = name
        self.weight = weight
        self.avatar = avatar
        self.dest = destination
        self.orig = origin
        self.att = attributes
    def __repr__(self):
        return "(" + str(self.orig) + "->" + str(self.dest) + ")"
    def __eq__(self, other):
        return self.name == other.name
    def get_weight(self):
        return weight
    def get_avatar(self):
        return avatar
    def is_passable_now(self):
        return True
    def admits(self, traveler):
        return True
    def is_passable_by(self, traveler):
        return self.isPassableNow() and self.admits(traveler)
    def get_dest(self):
        return self.dest
    def get_orig(self):
        return self.orig
    def get_ends(self):
        return [self.orig, self.dest]
    def touches(self, place):
        return self.orig is place or self.dest is place
    def find_neighboring_portals(self):
        return self.orig.portals + self.dest.portals

class Place:
    def __init__(self, name, atts=[], contents=[], portals=[], entrytests=[]):
        self.name = name
        self.att = dict(atts)
        self.contents = contents
        self.portals = portals
        self.entrytests = []
    def addthing(self, item):
        for test in self.entrytests:
            if not test(item):
                return
        self.contents.append(item)
    def rmitem(self, item):
        self.contents.remove(item)
    def __getitem__(self, key):
        return self.att[key]
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
    def __eq__(self, other):
        # The name is the key in the database. Must be unique.
        return self.name == other.name
        # for key in self.att.keys():
        #     if self[key] != other[key]:
        #         return False
        # accounted_for = []
        # for item in self.contents:
        #     if item not in other.contents:
        #         return False
        #     else:
        #         accounted_for.append(item)
        # for item in other.contents:
        #     if item not in accounted_for:
        #         if item not in self.contents:
        #             return False


class GenericGraph:
    def __init__(self, name, places=[], portals=[]):
        self.name = name
        self.places = places
        self.portals = portals
    def add_place(self, place):
        self.places.append(place)
    def add_portal(self, portal):
        self.portals.append(portal)
    def get_edge(self, portal):
        origi = self.places.index(portal.orig)
        desti = self.places.index(portal.dest)
        return (origi, desti)
    def get_edges(self):
        return [ self.get_edge(port) for port in self.portals ]
    def get_edge_atts(self):
        r = {}
        for port in self.portals:
            key = self.get_edge(port)
            val = port.att.iteritems()
            r[key] = val
        return r
    def get_vertex_atts(self):
        r = {}
        i = 0
        while i < len(self.places):
            r[i] = self.places[i].att.iteritems()
            i += 1
        return r
    def get_igraph_graph(self):
        return igraph.Graph(edges=self.get_edges(), directed=True,
                            vertex_attrs=self.get_vertex_atts(),
                            edge_attrs=self.get_edge_atts())

class Dimension(GenericGraph):
    pass

class Map(GenericGraph):
    pass