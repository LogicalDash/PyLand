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
    dest = None
    def __init__(self, destination, avatar=None, weight=0):
        self.weight = weight
        self.avatar = avatar
        self.dest = destination
        self.count = 0
    def __repr__(self):
        return "(" + str(self.orig) + "->" + str(self.dest) + ")"
    def __iter__(self):
        return self
    def __next__(self):
        if count == 0:
            return self.orig
        elif count == 1:
            return self.dest
        else:
            raise StopIteration
        self.count += 1
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
