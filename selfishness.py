class selfishness:
    def __init__(self, name, identity):
        self.name = name
        self.identity = identity

    def findSelf(self):
        print "%s has discovered it was %s all along!" % (self.name, self.identity)

    def giveHelp(self, other):
        print "%s is helping %s discover itself." % (self.name, other.name)
        selfishness.findSelf(other)

you = selfishness("hooker", "heart of gold")
me = selfishness("detective", "heart of coal")
        
        
