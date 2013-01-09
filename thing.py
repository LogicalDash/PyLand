import place
import level

class Thing:
<<<<<<< HEAD
    loc = None
    def __init__(self, name, desc='', loc=None, attributes=[]):
        self.name = name
        self.desc = desc
        self.attributes = attributes
        if loc is not None:
            if issubclass(loc, place.Place):
                self.loc = loc
            elif type(loc) is str:
                self.loc = level.getLevel().places[loc]
=======
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
>>>>>>> bf4e7d430ded49df77106f136e98448decf831de
