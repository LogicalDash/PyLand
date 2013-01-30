from portal import Portal

class Place:
    def __init__(self, name, atts=[], contents=[], portals=[], entrytests=[]):
        self.name = name
        self.att = dict(atts)
        self.contents = contents
        self.portals = portals
        self.entrytests = []
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
        # for key in self.att.keys():
        #     if self[key] != other[key]:
        #         return False
        # accounted_for = []
        # for item in self.contents:
        #     if item not in other.contents:
        #         return False
        #     else:
        #         accounted_for.append(item)
        # for item in other.contents:
        #     if item not in accounted_for:
        #         if item not in self.contents:
        #             return False
