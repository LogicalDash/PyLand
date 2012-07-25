import place
import portal
import thing
from game import game

levels = {} # A dictionary of Level objects, with their names as keys.
curLevel = None

def getLevel(name):
    return levels[name]

def getLevel():
    return curLevel

def gotoLevel(name):
    curLevel = levels[name]

class Level:
    places = {} # A dictionary of Place objects, with their names as keys.
    portals = []
    mst = [] # Actually just a list of Place objects, but selected
             # such that they comprise the minimum spanning tree for
             # the level.
    name = None

    def __init__(self, name, places, portals, mst):
        self.name = name
        self.places = places
        self.portals = portals
        self.mst = mst

    def loadFromFile(levelfile):
        '''Loads a VectorWorld map. Returns True on success, False on
        failure.'''
        if levelfile is None:
            return False
        line = levelfile.readline()
        if line != 'level for VectorWorld version ' + game.version:
            return False
        while(line != ''):
            line = levelfile.readline()
            token = line.split(" ")
            if token[0] == 'place':
                handlePlaceTokens(token)
            elif token[0] == 'portal':
                handlePortalTokens(token)
            elif token[0] =='name':
                self.name = token[1]
            else:
                print "Unreadable level line: " + line
        if(name is not None):
            levels[name] = Level(name,places,portals,mst)

    def handlePlaceTokens(self, tok):
        # When first declared, places have names and very little else.
        # There might be some flags in here to alert me to the
        # particular category of place that this one belongs to. I'll
        # work out what to do with categories somewhere in the class
        # definition for places, starting with different categories
        # depending on what a place is allowed to contain.
        #
        # Okay, so the first token (barring 'place') is the name, the
        # second is the category, and everything else I'll deal with
        # later...
        #
        # I'd like categories to be optional.
        assert(len(tok)==2 or len(tok)==3)
        if(len(tok)==3):
            places.append(Place(tok[1],tok[2]))
        if(len(tok)==2):
            places.append(Place(tok[1]))
    
    def handlePortalTokens(self,tok):
        # Every portal needs an origin and a destination.  They may
        # also have an avatar and/or a weight.  Actually they always
        # need a weight, but it defaults to zero. For reasons of
        # personal convenience I'll assume the arguments are always in
        # that order.
        assert(len(tok)>=3)
        assert(len(tok)<=5)
        orig = places[tok[1]]
        dest = places[tok[2]]
        if(len(tok)==3):
            portals.append(Portal(orig,dest))
        if(len(tok)==4):
            portals.append(Portal(orig,dest,things[tok[3]]))
        if(len(tok)==5):
            portals.append(Portal(orig,dest,things[tok[3]],int(tok[4])))

    def getmst(self):
        return mst
