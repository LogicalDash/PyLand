import igraph


class Journey:
    """Series of steps taken by a Thing to get to a Place.

    Journey(traveller, destination, steps) => journey

    Journey is the class for keeping track of a path that a traveller
    wants to take across one of the game maps. It is stateful: it
    tracks where the traveller is, and how far it's gotten along the
    edge through which it's travelling. Each step of the journey is a
    portal in the steps supplied on creation. The list should consist
    of Portals in the precise order that they are to be travelled
    through.

    Each Journey has a progress attribute. It is a float, at least 0.0
    and less than 1.0. When the traveller moves some distance along
    the current Portal, call move(prop), where prop is a float, of the
    same kind as progress, representing the proportion of the length
    of the Portal that the traveller has travelled. progress will be
    updated, and if it meets or exceeds 1.0, the current Portal will
    become the previous Portal, and the next Portal will become the
    current Portal. progress will then be decremented by 1.0.

    You probably shouldn't move the traveller through more than 1.0 of
    a Portal at a time, but Journey handles that case anyhow.

    """

    def __init__(self, thing, dest, steplist):
        self.steplist = steplist
        self.curstep = 0
        self.thing = thing
        self.dest = dest
        self.progress = 0.0

    def steps(self):
        """Get the number of steps in the Journey.

        steps() => int

        Returns the number of Portals the traveller ever passed
        through or ever will on this Journey.

        """
        return len(self.steplist)

    def stepsleft(self):
        """Get the number of steps remaining until the end of the Journey.

        stepsleft() => int

        Returns the number of Portals left to be travelled through,
        including the one the traveller is in right now.

        """
        return len(self.steplist) - self.curstep

    def getstep(self, i):
        """Get the ith next Portal in the journey.

        getstep(i) => Portal

        getstep(0) returns the portal the traveller is presently
        travelling through. getstep(1) returns the one it wil travel
        through after that, etc. getstep(-1) returns the step before
        this one, getstep(-2) the one before that, etc.

        If i is out of range, returns None.

        """
        if i >= 0 and i < len(self.steplist):
            return self.steplist[i+self.curstep]
        else:
            return None

    def move(self, prop):
        """Move the specified amount through the current portal.

        move(prop) => Portal

        Increments the current progress, and then adjusts the next and
        previous portals as needed.  Returns the Portal the traveller
        is now travelling through. prop may be negative.

        If the traveller moves past the end (or start) of the path,
        returns None.

        """
        self.progress += prop
        while self.progress >= 1.0:
            self.curstep += 1
            self.progress -= 1.0
        while self.progress < 0.0:
            self.curstep -= 1
            self.progress += 1.0
        return self.getstep(0)


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
    def __init__(self, name, origin, destination, attributes={}):
        if origin.dimension is not destination.dimension:
            raise Exception("No interdimensional portals")
        self.name = name
        self.dest = destination
        self.orig = origin
        self.att = attributes

    def __repr__(self):
        return "(" + str(self.orig) + "->" + str(self.dest) + ")"

    def __eq__(self, other):
        return self.name == other.name

    def get_weight(self):
        return self.weight

    def get_avatar(self):
        return self.avatar

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
    def __init__(self, dimension, name, contents=[], portals=[]):
        self.name = name
        self.dimension = dimension
        self.contents = contents
        self.portals = portals

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


class Dimension:
    def __init__(self, name, places=[], portals=[]):
        self.name = name
        self.places = places
        self.portals = portals
        self.igg = None

    def add_place(self, place):
        self.places.append(place)

    def add_portal(self, portal):
        self.portals.append(portal)

    def get_edge(self, portal):
        origi = self.places.index(portal.orig)
        desti = self.places.index(portal.dest)
        return (origi, desti)

    def get_edges(self):
        return [self.get_edge(port) for port in self.portals]

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
        if self.igg is None:
            self.igg =  igraph.Graph(edges=self.get_edges(), directed=True,
                                     vertex_attrs=self.get_vertex_atts(),
                                     edge_attrs=self.get_edge_atts())
        return self.igg
