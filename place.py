from portal import Portal

class Place:
    portals = []
    contents = []
    hazing = []
    def __init__(self, name=None, display_name=None):
        self.name = name
        self.display_name=display_name
    def connect_to(self, place):
        if place not in [portal.dest for portal in self.portals]:
            self.portals.append(Portal(self, place))
    def additem(self, item):
        # mightn't the item be in the database though?
        for test in hazing:
            if not test(item):
                return
        self.contents.append(item)
    def rmitem(self, item):
        self.contents.remove(item)
    def __repr__(self):
        return self.name
    def __str__(self):
        return self.name
