class EventCard:
    """Abstract class for cards representing things that can happen.

EventCards are kept in EventDecks, which are in turn contained by
Characters. When something happens involving one or more characters,
the relevant EventDecks from the participating Characters will be put
together into an AttemptDeck. One card will be drawn from this, called
the attempt card. It will identify what kind of EventDeck should be
taken from the participants and compiled in the same manner into an
OutcomeDeck. From this, the outcome card will be drawn.

The effects of an event are determined by both the attempt card and
the outcome card. An attempt card might specify that only favorable
outcomes should be put into the OutcomeDeck; the attempt card might
therefore count itself for a success card. But further, success cards
may have their own effects irrespective of what particular successful
outcome occurs. This may be used, for instance, to model that kind of
success that strains a person terribly and causes them injury.

"""
    tablename = "eventcard"
    keydecldict = {"character": "text",
                   "deck": "text",
                   "name": "text"}
    valdecldict = {"quality": "text default 'neutral'"}

    def __init__(self):
        if self.__class__ is EventCard:
            raise Exception("Strictly abstract class")


class EventEffect:
    """Abstract class representing any effect that an EventCard
can have.

EventEffects are linked together under a single EventCard, which then
executes the EventEffects whenever the event happens.

    """
    def __init__(self):
        if self.__class__ is EventEffect:
            raise Exception("Strictly abstract")


class EventDeck:
    def __init__(self):
        if self.__class__ is EventDeck:
            raise Exception("Strictly abstract")


class AttemptCard(EventCard):
    # I want two levels of hierarchy organizing event cards: attempt
    # vs. outcome, and then five "quality levels" or something that
    # represent how favorable it is. The middle one is neutral, so if
    # you're making decks that don't really favor anyone, that's the
    # level to use.

    # I also want to be able to combine the effects of various cards
    # so I'll model the effects separately.

    # Though I could use integers for quality, I'll use strings
    # instead, so that the same system may later be used to select for
    # other things.

    # Enforcing the attempt/outcome distinction at the database level
    # seems like a bad idea, since there are lots of other things the
    # deck concept is good for. I'm not even sure having a class for
    # it is the best. Maybe have a type field on the event card table
    # and use that to match attempts and outcomes.
    pass


class OutcomeCard(EventCard):
    pass
