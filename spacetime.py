import igraph
from saveload import SaveableMetaclass


__metaclass__ = SaveableMetaclass


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
    coldecls = {"journey":
                {"dimension": "text",
                 "thing": "text",
                 "curstep": "integer",
                 "progress": "float"},
                "journeystep":
                {"dimension": "text",
                 "thing": "text",
                 "idx": "integer",
                 "portal": "text"}}
    primarykeys = {"journey": ("dimension", "thing"),
                   "journeystep": ("dimension", "thing", "idx")}
    fkeydict = {"journey":
                {"dimension, thing": ("thing", "dimension, name")},
                "journeystep":
                {"dimension, thing": ("thing", "dimension, name"),
                 "dimension, portal": ("portal", "dimension, name")}}
    checks = {"journey": ["progress>=0.0", "progress<1.0"]}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.thing = db.thingdict[rowdict["dimension"]][rowdict["thing"]]
        self.curstep = rowdict["curstep"]
        self.progress = rowdict["progress"]
        self.steplist = []

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
        return self.steplist[i+self.curstep]

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
        if self.curstep > len(self.steplist):
            return None
        else:
            return self.getstep(0)

    def set_step(self, port, idx):
        while idx >= len(self.steplist):
            self.steplist.append(None)
        self.steplist[idx] = port


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
    coldecls = {"portal":
                {"dimension": "text",
                 "name": "text",
                 "from_place": "text",
                 "to_place": "text"}}
    primarykeys = {"portal": ("dimension", "name")}
    foreignkeys = {"portal":
                   {"dimension, name": ("item", "dimension, name"),
                    "dimension, from_place": ("place", "dimension, name"),
                    "dimension, to_place": ("place", "dimension, name")}}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.name = rowdict["name"]
        self.hsh = hash(self.dimension + self.name)
        self.dest = db.placedict[self.dimension][rowdict["to_place"]]
        self.orig = db.placedict[self.dimension][rowdict["from_place"]]

    def __hash__(self):
        return self.hsh

    def get_weight(self):
        return self.weight

    def get_avatar(self):
        return self.avatar

    def is_passable_now(self):
        return True

    def admits(self, traveler):
        return True

    def is_now_passable_by(self, traveler):
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
    coldecls = {"place":
                {"dimension": "text",
                 "name": "text"}}
    primarykeys = {"place": ("dimension", "name")}

    def __init__(self, db, rowdict):
        self.db = db
        self.rowdict = rowdict
        self.name = self.rowdict["name"]
        self.dimension = self.rowdict["dimension"]
        self.contents = []
        self.portals = []

    def __eq__(self, other):
        if not isinstance(other, Place):
            return False
        else:
            # The name is the key in the database. Must be unique.
            return self.name == other.name


class Dimension:
    coldecls = {"dimension":
                {"name": "text"}}
    primarykeys = {"dimension": ("name",)}

    def __init__(self, db, rowdict):
        self.name = rowdict["name"]
        self.places = []
        self.portals = []

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
        return igraph.Graph(edges=self.get_edges(), directed=True,
                            vertex_attrs=self.get_vertex_atts(),
                            edge_attrs=self.get_edge_atts())

    def get_igraph_layout(self, layout_type):
        return self.get_igraph_graph().layout(layout=layout_type)


class Thing:
    coldecls = {"thing":
                {"dimension": "text",
                 "name": "text"},
                "location":
                {"dimension": "text",
                 "thing": "text",
                 "place": "text"},
                "containment":
                {"dimension": "text",
                 "contained": "text",
                 "container": "text"},
                "thing_kind":
                {"name": "text"},
                "thing_kind_link":
                {"thing": "text",
                 "kind": "text"}}
    primarykeys = {"thing": ("dimension", "name"),
                   "location": ("dimension", "thing"),
                   "containment": ("dimension", "contained"),
                   "thing_kind": ("name",),
                   "thing_kind_link": ("thing", "kind")}
    foreignkeys = {"thing":
                   {"dimension": ("dimension", "name")},
                   "location":
                   {"dimension": ("dimension", "name"),
                    "dimension, thing": ("thing", "dimension, name"),
                    "dimension, place": ("place", "dimension, name")},
                   "containment":
                   {"dimension": ("dimension", "name"),
                    "dimension, contained": ("thing", "dimension, name"),
                    "dimension, container": ("thing", "dimension, name")},
                   "thing_kind_link":
                   {"thing": ("thing", "name"),
                    "kind": ("thing_kind", "name")}}
    checks = {"containment": ["contained<>container"]}

    def __init__(self, db, rowdict):
        self.dimension = rowdict["dimension"]
        self.name = rowdict["name"]
        self.location = None
        self.contents = []
        self.permissions = []
        self.forbiddions = []
        self.permit_inspections = []
        self.forbid_inspections = []


    def __str__(self):
        return "(%s, %s)" % (self.dimension, self.name)

    def __iter__(self):
        return (self.dimension, self.name)

    def __repr__(self):
        if self.location is None:
            loc = "nowhere"
        else:
            loc = str(self.location)
        return self.name + "@" + loc

    def add_item(self, it):
        if it in self.cont:
            return False
        elif self.permitted(it):
            self.cont.append(it)
            return True
        elif self.forbidden(it):
            return False
        elif self.can_contain(it):
            self.cont.append(it)
            return True
        else:
            return False

    def permit_item(self, it):
        self.forbiddions.remove(it)
        self.permissions.append(it)

    def forbid_item(self, it):
        self.permissions.remove(it)
        self.forbiddions.append(it)


class ThingKind:
    """A category to which a Thing may belong. Any Thing may belong to any
number of ThingKinds."""
    tablename = "thing_kind"
    keydecldict = {"name": "text"}


class ThingKindMember:
    tablename = "thing_kind_member"
    keydecldict = {"thing": "text",
                   "kind": "text"}
# TODO: methods of Thing to get instances of those classes and inspect
# items who want to enter to make sure they pass.
#
# TODO: subclasses of thing to differentiate between things and other things


class Event:
    """Abstract class for things that can happen. Normally represented as
cards.

Events are kept in EventDecks, which are in turn contained by
Characters. When something happens involving one or more characters,
the relevant EventDecks from the participating Characters will be put
together into an AttemptDeck. One card will be drawn from this, called
the attempt card. It will identify what kind of EventDeck should be
taken from the participants and compiled in the same manner into an
OutcomeDeck. From this, the outcome card will be drawn.

The effects of an event are determined by both the attempt card and
the outcome card. An attempt card might specify that only favorable
outcomes should be put into the OutcomeDeck; the attempt card might
therefore count itself for a success card. But further, success cards
may have their own effects irrespective of what particular successful
outcome occurs. This may be used, for instance, to model that kind of
success that strains a person terribly and causes them injury.

    """
    coldecls = {"event":
                {"name": "text",
                 "type": "text"},
                "event_effect":
                {"name": "text",
                 "func": "text"},
                "event_effect_link":
                {"event": "text",
                 "effect": "text"},
                "event_req_thing":
                {"event": "text",
                 "dimension": "text",
                 "thing": "text"},
                "event_req_thing_kind":
                {"event": "text",
                 "kind": "text"}}
    primarykeys = {"event": ("name",),
                   "event_effect": ("name", "func"),
                   "event_effect_link": ("event", "effect"),
                   "event_req_thing": ("event", "thing"),
                   "event_req_thing_kind": ("event", "kind")}
    foreignkeys = {"event_effect_link":
                   {"event": ("event", "name"),
                    "effect": ("effect", "name")},
                   "event_req_thing":
                   {"event": ("event", "name"),
                    "dimension, thing": ("thing", "dimension, name")},
                   "event_req_thing_kind":
                   {"event": ("event", "name"),
                    "kind": ("thing_kind", "name")}}

    def __init__(self):
        if self.__class__ is Event:
            raise Exception("Strictly abstract class")
