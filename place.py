from portal import Portal

class Place:
    portals = []
    contents = []
    def __init__(self, name):
        self.name = name
    def connect_to(self, place):
        if place not in [portal.dest for portal in self.portals]:
            self.portals.append(Portal(self, place))
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
