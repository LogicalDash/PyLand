class Character:
    """An incorporeal object connecting corporeal ones together across
dimensions, indicating that they represent one thing and have that
thing's attributes.

Every item in LiSE's world model must be part of a Character, though
it may be the only member of that Character. Where items can only have
generic attributes appropriate to the dimension they occupy,
Characters have all the attributes of the items that make them up, and
possibly many more. There are no particular restrictions on what
manner of attribute a Character can have, so long as it is not used by
the physics of any dimension.

Characters may contain EventDecks. These may represent skills the
character has, in which case every EventCard in the EventDeck
represents something can happen upon using the skill, regardless of
what it's used on or where. "Success" and "failure" are appropriate
EventCards in this case, though there may be finer distinctions to be
made between various kinds of success and failure with a given skill.

However, the EventCards that go in a Character's EventDeck to
represent a skill should never represent anything particular to any
use-case of the skill. Those EventCards should instead be in the
EventDeck of those other Characters--perhaps people, perhaps places,
perhaps tools--that the skill may be used on, with, or for. All of
those Characters' relevant EventDecks will be used in constructing a
new one, called the OutcomeDeck, and the outcome of the event will be
drawn from that.

Otherwise, Characters can be treated much like three-dimensional
dictionaries, wherein you may look up the Character's attributes. The
key is composed of the dimension an item of this character is in, the
item's name, and the name of the attribute.

"""
    def __init__(self, name, items=[], attrs=[]):
        self.name = name
        self.items = items
        self.attdict = {}
        for row in attrs:
            (dim, thing, att, val) = row
            if dim not in self.attdict:
                self.attdict[dim] = {}
            if thing not in self.attdict[dim]:
                self.attdict[dim][thing] = {}
            self.attdict[dim][thing][att] = val


class BoolCheck:
    def __init__(self):
        """This is an abstract class."""
        if self.__class__ is BoolCheck:
            raise TypeError("BoolCheck is abstract. Perhaps you want "
                            "AttrCheck.")

    def check(self, n):
        """Override this!"""
        pass


class TrueCheck(BoolCheck):
    """For when you need a BoolCheck object but don't want to test
    anything."""
    def check(self, n):
        return True


class LowerBoundCheck(BoolCheck):
    def __init__(self, bound):
        if bound is None:
            return TrueCheck()
        self.bound = bound

    def check(self, n):
        return self.bound <= n


class UpperBoundCheck(BoolCheck):
    def __init__(self, bound):
        if bound is None:
            return TrueCheck()
        self.bound = bound

    def check(self, n):
        return self.bound >= n


class TypeCheck(BoolCheck):
    def __init__(self, typ):
        if typ is None:
            return TrueCheck()
        elif type(typ) is type:
            self.typ = typ
        elif typ == 'str':
            self.typ = str
        elif typ == 'bool':
            self.typ = bool
        elif typ == 'int':
            self.typ = int
        elif typ == 'float':
            self.typ = float
        else:
            raise TypeError("Type not recognized: %s" % repr(typ))

    def check(self, n):
        return type(n) is self.typ


class ListCheck(BoolCheck):
    def __init__(self, l):
        if l is None:
            return TrueCheck()
        self.lst = l

    def check(self, n):
        return n in self.lst


class CompoundCheck(BoolCheck):
    def __init__(self, checks, checkclass=BoolCheck):
        self.checks = [c for c in checks if
                       issubclass(c.__class__, checkclass)]

    def check(self, n):
        for c in self.checks:
            if not c.check(n):
                return False
        return True


class AttrCheck(CompoundCheck):
    table_schema = ("CREATE TABLE attribute "
                    "(name text primary key, "
                    "type text, "
                    "lower, "
                    "upper);")

    def __init__(self, name, typ=None, vals=[], lower=None, upper=None):
        # Slowness may result if typs or vals have redundancies. I'd
        # like to check for that.
        self.name = name
        self.typcheck = TrueCheck()
        self.lstcheck = TrueCheck()
        self.locheck = TrueCheck()
        self.hicheck = TrueCheck()
        if typ is not None:
            self.typcheck = TypeCheck(typ)
        if len(vals) > 0:
            self.lstcheck = ListCheck(vals)
        if lower is not None:
            self.locheck = LowerBoundCheck(lower)
        if upper is not None:
            self.hicheck = UpperBoundCheck(upper)

    def check(self, n):
        if self.lstcheck.check(n):
            return True
        else:
            return (self.typcheck.check(n) and
                    self.locheck.check(n) and
                    self.hicheck.check(n))


classes = [AttrCheck]
table_schemata = [clas.table_schema for clas in classes]
