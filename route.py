from place import Place
from thing import Thing
from portal import Portal
#ord, progress, portal
class Route:
    def __init__(self, steplist, thing, dest):
        self.steplist = steplist
        self.prevsteps = []
        self.thing = thing
        self.dest = dest
        self.steplist.sort()
    def getstep(self, i):
        return self.steplist[i]
    def curstep(self):
        return self.getstep(0)
    def curprog(self):
        return self.curstep()[1]
    def curport(self):
        return self.curstep()[2]
    def prevstep(self):
        return self.prevsteps[-1]
    def move(self, prop, stepped=[]):
        """Call this with a float argument to progress the specified
        amount toward the next step. If that makes the current
        progress go to 1.0 or above, I'll move the thing to the new
        place. I will return a list of steps completed with this
        call--plus the step presently in progress on the very end.

        """
        (i, prog, port) = self.curstep()
        newprog = prog + prop
        if newprog >= 1.0:
            newstep = self.curstep()
            del self.steplist[0]
            self.prevsteps.append(newstep)
            stepped.append(newstep)
            newprog -= 1.0
            return self.move(nuprog, stepped)
        elif newprog < 0.0:
            newstep = self.prevsteps[-1]
            del self.prevsteps[-1]
            newprog += 1.0
            newstep[1] = newprog
            self.steplist.insert(0, newstep)
            stepped.append(newstep)
            return self.move(newprog, stepped)
        else:
            stepped.append((i, newprog, port))
            self.steplist[0] = (i, newprog, port)
            return stepped