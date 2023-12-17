from botctime import day, night

class Timeline:
    """A timeline of a player or other object."""
    def __init__(self, start_state):
        self.states = [(night(1), start_state)]
        self.events = []
        self.stdirty = False # Do lazy sorting
        self.evdirty = False

    def at(self, time):
        """State of this player at a specific time."""
        self._sort()
        # Assumption is that this will most often be looking at recent events
        # So look backwards from the last event
        for st_time, state in reversed(self.states):
            if st_time <= time:
                return state

    def now(self):
        """Latest state in this timeline."""
        self._sort()
        return self.states[-1][1]

    def states_during(self, start_time, end_time, states_only=True):
        """All states seen between specified times."""
        self._sort()
        ret = [self.at(start_time)] if states_only else [(start_time, self.at(start_time))]
        for time, state in self.states:
            if time > start_time and time <= end_time:
                ret.append(state if states_only else (time, state))
        return ret

    def events_during(self, start_time, end_time, events_only=True):
        """All events seen between specified times."""
        self._sort()
        ret = []
        for time, event in self.events:
            if time >= start_time and time <= end_time:
                ret.append(event if events_only else (time, event))
        return ret

    def set_state(self, time, state):
        """Specify state at a certain time. Does nothing if same as state at that point."""
        if state == self.at(time):
            return
        self.states.append((time, state))
        self.stdirty = True

    def add_event(self, time, event):
        """Specify an event happening."""
        self.events.append((time, event))
        self.evdirty = True

    def _sort(self):
        if self.stdirty:
            self.states.sort(key=lambda tst: tst[0])
            self.stdirty = False
        if self.evdirty:
            self.events.sort(key=lambda tev: tev[0])
            self.evdirty = False
