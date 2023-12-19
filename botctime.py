

# Time is represented as a combination of day/night number plus point in day/night order
#  Day/night is referred to as 'hours'
#  Point in day/night is referred to as 'minutes'
#  Sub-point is referred to as 'seconds'

# To keep with BOTC standards, nights and days are 1-indexed
# Night n is '2(n-1)', day n is '2(n-1)+1'

# Day ordering is:
#  0: Dawn; declaration of deaths etc
#  1: Midday; public statements etc and nominations
#  2: After execution; declaration of deaths etc
# Night ordering is:
#  0: Dusk; when wearing off happens, different to (day, 2)
#  1-n: Each character's action. Character classes define their number here
#  [No point for 'end of night'; that's dawn]
#  TODO: Consider adding a point for this if useful, with '-1' working for it
#        Probably would have a MAX_MINUTE or something

# Sub-ordering is used for reactive / multipart events. E.g., barber swaps

DAWN = 0
MIDDAY = 1
POST_EX = 2
DUSK = 0

def day(n, minute=DAWN, second=0):
    return BOTCTime(2*(n-1)+1, minute, second)

def night(n, minute=DUSK, second=0):
    return BOTCTime(2*(n-1), minute, second)

class BOTCTime:
    """Time classwith internal representation as a tuple."""
    def __init__(self, hour=0, minute=0, second=0):
        self.t = (hour, minute, second)

    @property
    def h(self):
        return self.t[0]

    @property
    def m(self):
        return self.t[1]

    @property
    def s(self):
        return self.t[2]

    @property
    def day(self):
        return self.h % 2 == 1

    @property
    def night(self):
        return self.h % 2 == 0

    @property
    def n(self):
        return (self.h // 2) + 1

    def __eq__(self, other):
        assert isinstance(other, BOTCTime)
        return self.t == other.t

    def __lt__(self, other):
        assert isinstance(other, BOTCTime)
        return self.t < other.t

    def __gt__(self, other):
        assert isinstance(other, BOTCTime)
        return self.t > other.t

    def __le__(self, other):
        assert isinstance(other, BOTCTime)
        return self.t <= other.t

    def __ge__(self, other):
        assert isinstance(other, BOTCTime)
        return self.t >= other.t

    def __add__(self, other):
        if isinstance(other, BOTCTime):
            return BOTCTime(self.h + other.h, self.m + other.m, self.s + other.s)
        assert isinstance(other, tuple) and len(other) == 3
        return BOTCTime(self.h + other[0], self.m + other[1], self.s + other[2])

    def __str__(self):
        if self.day:
            return "Day {} ({}:{})".format(self.n, self.m, self.s)
        else:
            return "Night {} ({}:{})".format(self.n, self.m, self.s)

    def __repr__(self):
        return str(self)


class Clock:
    def __init__(self, start_time=None):
        self.now = start_time if start_time else night(1)
        self.moments = [self.now]

    def tick(self, hour=0, minute=1, second=0):
        """Add a certain amount of time to the clock."""
        # TODO: Handling wrapping round when reaching max minutes?
        self.now = self.now + (hour, minute, second)
        self.moments.append(self.now)

    def previous(self, hour=False, minute=False, second=True, start=False):
        """A previous moment before the current one.

By default returns the last moment that was seen before now.
Can choose to look at the previous minute or hour.
  If so, by default returns the last moment in that minute or hour. Can change to first."""
        # Account for the clock being changed back. Keep moving back
        # TODO: account for the above. Currently only does default behaviour.
        prev_moment = None
        for moment in reversed(self.moments):
            if moment >= self.now:
                continue
            return moment
        # Reached the first moment without finding anything
        # Could error instead of just passing back the start time
        return moment

    def last_night(self):
        """The time periods that were in last night."""
        raise NotImplementedError()

    def last_day(self):
        """The time periods that were in last day."""
        raise NotImplementedError()
