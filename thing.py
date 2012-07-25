import place
import level

things = {}

class Thing:
    loc = None
    def __init__(self, name, desc='', loc=None):
        self.name = name
        self.desc = desc
        if loc is not None:
            if issubclass(loc, place.Place):
                self.loc = loc
            else:
                assert(type(loc) == str)
                self.loc = level.getLevel().places[loc]
        things[name] = self
