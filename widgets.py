# This file is for the controllers for the things that show up on the screen when you play.

class Spot:
    """Controller for the icon that represents a Place.

    Spot(place, x, y, spotgraph=None) => a Spot representing the given
    place; at the given x and y coordinates on the screen; in the
    given graph of Spots. The Spot will be magically connected to the other
    Spots in the same way that the underlying Places are connected."""
    def __init__(self, place, x, y, spotgraph):
        self.place = place
        self.x = x
        self.y = y
        self.spotgraph = spotgraph
    def __repr__(self):
        coords = "(%i,%i)" % (self.x, self.y)
        return "Spot at " + coords + " representing " + str(self.place)
    def __str__(self):
        return repr(self)
                

class SpotGraph:
    places = {}
    spots = []
    edges = []
    edges_to_draw = []
    def add_spot(self, spot):
        self.spots.append(spot)
        self.places[spot.place] = spot
    def add_place(self, place, x, y):
        newspot = Spot(place, x, y, self)
        self.add_spot(newspot)
        self.connect_portals(newspot)
    def are_connected(self, spot1, spot2):
        return ((spot1, spot2) in self.edges) or ((spot2, spot1) in self.edges)
    def neighbors(self, spot1):
        r = []
        for edge in self.edges:
            if edge[0] is spot1:
                r.append(edge[1])
            if edge[1] is spot1:
                r.append(edge[0])
        return r
    def add_edge(self, spot1, spot2):
        self.edges.append((spot1, spot2))
        self.edges_to_draw.append((spot1.x, spot1.y, spot2.x, spot2.y))
    def connect_portals(self, spot):
        print "Connecting portals for " + str(spot) + " with %i candidate portals" % len(spot.place.portals)
        for portal in spot.place.portals:
            ps = self.places.keys()
            if portal.orig in ps and portal.dest in ps:
                self.add_edge(self.places[portal.orig], self.places[portal.dest])
                


class Pawn:
    """Data structure to represent things that move about between
    Spots on the screen.  Mostly these will represent characters or vehicles.

    The constructor takes three arguments: start, graph, and speed.

    start is a Spot. The Pawn will appear there at first.

    graph is a list of Spots. It should contain
    every Place that the Pawn ought to know about. That doesn't
    necessarily mean every Place in the game world, or even every
    Place that the character *represented by* the Pawn should know
    about. Pawns are not concerned with pathfinding, only with moving
    along a prescribed route at a prescribed speed.

    To give such a route to a Pawn, call waypoint. It takes two
    arguments: place and speed. place is the Place to go to next. The
    Pawn actually has no idea whether or not Places are connected to
    one another, so check first to make sure they are, otherwise the
    Pawn will happily wander where there is no Passage. speed is a
    floating point representing the portion of the distance between
    this Place and the previous one on the route that the Pawn should
    cover in a single frame. This should be calculated as the seconds
    of real time that the travel should take, divided by the game's
    screen-updates-per-second."""
    trip_completion = 0.0
    step = 0
    route = None
    def __init__(self, start, spotgraph):
        if isinstance(start, Spot):
            self.curspot = start
        elif isinstance(start, Place):
            self.curspot = spotgraph.places[start]
        self.x = start[0]
        self.y = start[1]
        self.spotgraph = spotgraph
    def curstep(self):
        if self.step >= len(self.route):
            return None
        if self.route is not None:
            return self.route[self.step]
    def curspeed(self):
        return self.curstep()[1]
    def nextspot(self):
        return self.curstep()[0]
    def prevspot(self):
        if self.step == 0:
            return self.curspot
        self.step -= 1
        r = self.curstep()[0]
        self.step += 1
        return r
    def move(self, ts):
        if self.route is None:
            return
        orig = self.prevspot()
        dest = self.nextspot()
        speed = self.curspeed()
        x_total = float(dest.x - orig.x)
        y_total = float(dest.y - orig.y)
        self.trip_completion += speed
        if self.trip_completion >= 1.0:
            # Once I have my own event-handling infrastructure set up,
            # this should fire a "trip completed" event.
            self.trip_completion = 0.0
            self.curspot = dest
            self.x = dest.x
            self.y = dest.y
            self.step += 1
            if self.step >= len(self.route):
                self.step = 0
                self.route = None
            return
        x_traveled = x_total * self.trip_completion
        y_traveled = y_total * self.trip_completion
        self.x = orig.x + x_traveled
        self.y = orig.y + y_traveled
    def cancel_route(self):
        """Canceling the route will let the Pawn reach the next node
        before stopping to await a new waypoint. If you want it
        stranded between two nodes, call delroute instead."""
        self.route = [self.curstep()]
    def delroute(self):
        self.route = None
    def extend_graph(self, spot):
        """Add a new Spot to the graph, where the Place is displayed
        on-screen at the given coordinates. Appropriate for when the
        character learns of a new place they can go to."""
        self.graph.append(spot)
        self.places[spot.place] = spot

