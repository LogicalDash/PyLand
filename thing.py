import place
import level

class Thing:
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
