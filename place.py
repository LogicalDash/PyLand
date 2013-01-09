from portal import Portal

class Place:
    def __init__(self, name, contents=[], atts=[], portals=[]):
        self.name = name
        self.contents = contents
        self.attributes = atts
        self.portals = portals
    def connect_to(self, place):
        port = Portal(self, place)
        if port not in self.portals:
            self.portals.append(port)
    def addthing(self, thing):
        self.contents.append(item)
    def rmthing(self, item):
        self.contents.remove(item)
    def getatts(self):
        return self.attributes
    def getconts(self):
        return self.contents
    def getports(self):
        return self.portals
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
