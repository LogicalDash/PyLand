from saveload import Saveable


class Thing(Saveable):
    coldecls = {"thing":
                {"dimension": "text",
                 "name": "text"},
                "location":
                {"dimension": "text",
                 "thing": "text",
                 "place": "text"},
                "containment":
                {"dimension": "text",
                 "contained": "text",
                 "container": "text"}}
    primarykeys = {"thing": ("dimension", "name"),
                   "location": ("dimension", "thing"),
                   "containment": ("dimension", "contained")}
    foreignkeys = {"thing":
                   {"dimension": ("dimension", "name")},
                   "location":
                   {"dimension": ("dimension", "name"),
                    "dimension, thing": ("thing", "dimension, name"),
                    "dimension, place": ("place", "dimension, name")},
                   "containment":
                   {"dimension": ("dimension", "name"),
                    "dimension, contained": ("thing", "dimension, name"),
                    "dimension, container": ("thing", "dimension, name")}}
    checks = {"containment": ["contained<>container"]}

    def __init__(self, db, rowdict):
        Saveable.__init__(db, rowdict)
        self.dimension = rowdict["dimension"]
        self.name = rowdict["name"]
        self.location = None
        self.contents = []
        self.permissions = []
        self.forbiddions = []
        self.permit_inspections = []
        self.forbid_inspections = []
        self.key = [
            rowdict[keyname] for keyname in self.keydecldict.iterkeys()]
        self.val = [
            rowdict[valname] for valname in self.valdecldict.iterkeys()]

    def __str__(self):
        return "(%s, %s)" % (self.dimension, self.name)

    def __iter__(self):
        return (self.dimension, self.name)

    def __repr__(self):
        if self.location is None:
            loc = "nowhere"
        else:
            loc = str(self.location)
        return self.name + "@" + loc

    def add_item(self, it):
        if it in self.cont:
            return False
        elif self.permitted(it):
            self.cont.append(it)
            return True
        elif self.forbidden(it):
            return False
        elif self.can_contain(it):
            self.cont.append(it)
            return True
        else:
            return False

    def permit_item(self, it):
        self.forbiddions.remove(it)
        self.permissions.append(it)

    def forbid_item(self, it):
        self.permissions.remove(it)
        self.forbiddions.append(it)


class ThingKind:
    """A category to which a Thing may belong. Any Thing may belong to any
number of ThingKinds."""
    tablename = "thing_kind"
    keydecldict = {"name": "text"}


class ThingKindMember:
    tablename = "thing_kind_member"
    keydecldict = {"thing": "text",
                   "kind": "text"}
# TODO: methods of Thing to get instances of those classes and inspect
# items who want to enter to make sure they pass.
#
# TODO: subclasses of thing to differentiate between things and other things
