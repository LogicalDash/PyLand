import copy

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
    
    weight = 0
    avatar = None
    destination = None
    origin = None
 def __init__(self, origin, destination, avatar=None, weight=0):
     self.weight = weight
     self.avatar = avatar
     self.destination = destination
     self.origin = origin
    
     def getWeight(self):
         return weight
     def getAvatar(self):
        return avatar
     def isPassableNow(self):
         return True
     def admits(self, traveler):
         return True
     def isPassableBy(self, traveler):
         return self.isPassableNow() and self.admits(traveler)
     def getDest(self):
         return self.destination
     def getOrig(self):
         return self.origin
     def getEnds(self):
         return [self.origin, self.destination]
     def touches(self, place):
         return self.origin is place or self.destination is place
     def findNeighboringPortals(self):
         return self.origin.portals + self.destination.portals

class PortalTree:
    children = []

    def __init__(self, portal):
        self.portal = portal
    def append(self, portal):
        self.children.append(PortalTree(portal))
    def getOrig(self):
        return self.portal.origin
    def getDest(self):
        return self.portal.destination
    def getEnds(self):
        return [self.portal.origin, self.portal.destination]
    def remove(self, o):
        try:
            idx = children.index(o)
            del children[idx]
            return True
        except:
            for child in children:
                if child.remove(o):
                    return True
        return False
    def getFringeCore(self, fringe):
        if self.children is []:
            fringe.append(self)
        else:
            for child in self.children:
                child.getFringeCore(fringe)
    def getFringe(self):
        fringe = []
        self.getFringeCore(fringe)
        return fringe
    def getPlacesInTreeCore(self, placesInTree):
        placesInTree += self.getEnds()
        for child in self.children:
            child.getPlacesInTreeCore(placesInTree)
    def getPlacesInTree(self):
        placesInTree = []
        self.getPlacesInTreeCore(placesInTree)
        return placesInTree
    def touchesPortal(self, portal):
        return self.touchesPlace(portal.origin) \
            or self.touchesPlace(portal.destination)
    def touchesPlace(self, place):
        return place in self.places
    def containsPortal(self, o):
        if o in children:
            return True
        for c in children:
            if c.containsPortal(p):
                return True
        return False
    def isParent(self, child):
        return child in self.children
    def findParent(self, o):
        res = None
        if self.isParent(o):
            return self
        for child in self.children:
            res = child.findParent(o)
            if res is not None:
                return res
        return None
    def coreFindParents(self, o, res):
        if o in self.children:
            res.append(self)
        for child in self.children:
            child.coreFindParents(o, res)
    def findParents(self, o):
        res = []
        self.coreFindParents(o, res)
        return res
    def coreFindPortalsFrom(self, p, res):
        if self.getOrig() is p:
            res.append(self)
        for child in self.children:
            child.coreFindPortalsFrom(p, res)
    def findPortalsFrom(self, p):
        res = []
        self.coreFindPortalsFrom(p, res)
        return res
    def findPortalTo(self, p):
        # really, findPortalsFrom should only ever return one result,
        # when the portal network in question is a minimum spanning
        # tree.
        return self.findPortalsFrom(p)[0]
    def coreFindPortalsTo(self, p, res):
        if self.touchesPlace(p):
            res.append(self)
        for child in self.children:
            child.coreFindPortalsTo(p, res)
    def findPortalsTo(self, p):
        res = []
        self.coreFindPortalsTo(p, res)
        return res
    def replaceChild(self, o, q):
        assert(o in self.children)
        assert(q not in self.children)
        self.children.remove(o)
        self.children.append(q)
    def addLightestNeighborToChildren(self):
        neighbors = self.portal.findNeighboringPortals()
        for n in neighbors:
            if PortalTree(neighbor) in children:
                neighbors.remove(n)
        lightest = neighbors[0]
        for portal in neighbors[1:]:
            if portal.getWeight() < lightest.getWeight():
                lightest = portal
        self.children.append(lightest)
        return self.children[-1]
    

def makemst(places):
    unvisited = copy.copy(places)
    visited = []
    edgesIn = []
    edgesOut = []
    for place in places:
        edgesOut += place.portals
    mst = PortalTree(edgesOut[0])
    edgesIn.append(edgesOut[0])
    del edgesOut[0]
    visited += edgesIn[0].getEnds()
    unvisited.remove(visited[0])
    unvisited.remove(visited[1])
    while unvisited is not []:
        e = None
        for edge in edgesOut:
            if edge.getDest() in visited:
                e = edge
        visited.append(e.getOrig())
        unvisited.remove(e.getOrig())
        edgesIn.append(e)
        edgesOut.remove(e)
        mst.findPortalTo(e.getDest()).append(e)
        tweakAround(mst, e, edgesIn, edgesOut)
    return mst

       
def tweakAround(mst, e, edgesIn, edgesOut):
    # I can only tweak edges at the fringes.
    fringe = mst.getFringe()
    # For the moment, I'm only tweaking the ones that can connect to
    # the origin of e.

    # Actually, the ones whose origins have portals that go to the
    # origin of e.
    # To tweak an edge with respect to e:
    # Find its origin.
    # Find the portal from there to e's origin.
    # Is that portal lighter than the edge being tweaked?
    # If so, replace the edge being tweaked with the lighter one.
    for edge in fringe:
        candidates = []
        for port in edge.getOrig().portals:
            if port.getDest() is e.getOrig():
                candidates.append(port)
        for candidate in candidates:
            if candidate.getWeight() < port.getWeight():
                newbie = PortalTree(candidate)
                e.append(newbie)
                e.remove(port)
                edgesOut.append(port)
                edgesOut.remove(newbie)
                edgesIn.append(newbie)
                edgesIn.remove(port)
