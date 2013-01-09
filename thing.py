import place
import level

class Thing:
    def __init__(self, name, loc, attributes):
        self.name = name
        self.location = loc
        self.attribute = dict(attributes)
    def __repr__(self):
        if self.location is None:
            loc = "nowhere"
        else:
            loc = str(self.location)
        return self.name + "@" + loc + str(self.attribute)
    def __getitem__(self, i):
        return self.attribute[i]
