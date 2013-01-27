from database import Database

class State:
    """
    Class to hold the state of the game, specifically not including the state of the interface.
    """
    def __init__(dbfile):
        self.db = Database(dbfile)
        if not self.db.initialized():
            self.db.init()
