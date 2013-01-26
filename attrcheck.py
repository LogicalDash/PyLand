class BoolCheck:
    def __init__(self):
        """This is an abstract class."""
        if self.__class__ is BoolCheck:
            raise TypeError, ("BoolCheck is abstract. Perhaps you want "
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
        if list is None:
            return TrueCheck()
        self.list = l
    def check(self, n):
        return n in self.list

class CompoundCheck(BoolCheck):
    def __init__(self, checks, checkclass=BoolCheck):
        self.checks = [ c for c in checks if issubclass(c.__class__, checkclass) ]
    def check(self, n):
        for c in self.checks:
            if not c.check(n):
                return False
        return True

class AttrCheck(CompoundCheck):
    def __init__(self, typ=None, vals=[], lower=None, upper=None):
        checks = []
        # Slowness may result if typs or vals have redundancies. I'd
        # like to check for that.
        if typ is not None:
            checks.append(TypeCheck(typ))
        if len(vals) > 0:
            checks.append(ListCheck(vals))
        if lower is not None:
            checks.append(LowerBoundCheck(lower))
        if upper is not None:
            checks.append(UpperBoundCheck(upper))
        self.checks = checks
