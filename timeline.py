import functools

from botctime import *

def timelined(ss_attrs=(), setters=()):
    """Make an object remember its state as changes are made. Must be given a 'clock' attribute.

Events can be stored in an 'events' attribute, for non-state change events.
  Events are not used by this decorator, but it provides support for them.
Defines an 'at' method, which returns the state a specific time.
Specify methods that can change states in 'setters'.
  These will then get an 'at' parameter (default to 'None' for current time).
  After running the state change, the new state will be generated and stored.
States are stored in a 'states' attribute. This is lazily sorted on lookup.
  The state object is defined by the 'to_state' function (which looks at the current state).
  This object remembers the current time at creation.
  The returned object is a copy of the current state, referring to timelined objects if relevant.
  Getters in this object must convert timelined referred objects to their 'at' form, referring to the time at creation.
  These objects should be immutable, and must not be modified by any changes to their timelined form.
  If ss_attrs is defined, then the 'to_state' function is created. Otherwise it must be defined.
    The output of this function must define a copy method that allows changing the specific time.
    The automatically created 'to_state' function returns a SnapshotAttrs which is given ss_attrs.
    ss_attrs are then accessed by using 'at' after __getattr__.
    This class copies all attributes from ss_attrs off the main object, after converting to a Snapshot form.
      Objects that already have an 'at' method are not converted to Snapshot form.
        This means that cyclic references are not a problem, since timelined objects are already in snapshot form.
      tuples are converted to SnapshotTuple, which runs 'snapshot(_).at()' on what they return.
        The lazy evaluation of snapshot only in the getter means that cyclic references are not a problem.
      lists, sets and dicts in the object must be timelined. Otherwise, they can be modified without noticing.
        snapshot() will raise an error if it sees a naked set, list or dict for this reason.
        The timelined class's __setattr__ function is changed so that when setting something from ss_attrs, it converts if needed.
          It will error if trying to set it to a new list, set or dict though. That would be wiping the history.
      Other objects are converted to SnapshotStatic, where at() just returns the base value.
  Built in objects don't work with this automatically generated function. These need to define to_state themselves:
    TimelinedList (return a SnapshotTuple of their current state)
    TimelinedDict (return a SnapshotDict of their current state)
    TimelinedSet (return a SnapshotSet of the current state)
    These all need to wrap snapshot(_).at(self.time) around any returning functions
  Static objects like int and str don't get a timelined version. Their timeline is traced in whatever they're an attribute of."""
    def class_wrapper(cls):
        @functools.wraps(cls, updated=())
        class Timeline(cls):
            """A timeline of a player or other object."""
            IS_TIMELINED = True
            def __init__(self, *args, time=None, clock=None, **kwargs):
                self.setup(time, clock)
                self.pause_updates() # Don't want the __init__ to do state changes
                super().__init__(*args, **kwargs)
                self.resume_updates()
                self.state_change(time)
                

            def setup(self, time=None, clock=None):
                self.clock = clock if clock else Clock()
                self.states = []
                self.events = [] # Not actually used by this decorator.
                self._stdirty = False # Lazy sorting
                self._evdirty = False
                self._paused = False

            # Methods specific to this wrapping

            def to_state(self):
                """Current state of this object as a snapshot."""
                if hasattr(super(), "to_state"):
                    return super().to_state()
                return SnapshotAttrs(ss_attrs, self, self.clock.now)

            def __setattr__(self, name, value):
                # Need to stop people setting ss_attrs values to naked lists, sets or dicts
                if name in ss_attrs:
                    # Convert as needed
                    super().__setattr__(name, self._tsafe(value))
                    self.state_change()
                else:
                    super().__setattr__(name, value)

            # State has changed

            def pause_updates(self):
                was = self._paused
                self._paused = True
                return was

            def resume_updates(self):
                self._paused = False

            def state_change(self, time=None):
                if not self._paused:
                    self.set_state(self.to_state(), time=time)

            # Getting state and event objects

            def at(self, time=None):
                """State of this player at a specific time. By default checks current clock time."""
                self._sort()
                time = time if time else self.clock.now
                # Assumption is that this will most often be looking at recent events
                # So look backwards from the last event
                for st_time, state in reversed(self.states):
                    if st_time <= time:
                        if state.time != time:
                            # TODO: memoise by using set_state
                            return state.copy(time=time)
                        return state

            def now(self):
                """Current state in this timeline."""
                return self.at()

            def latest(self):
                """Latest state in this timeline. May be in the future if clock has been rewound."""
                self._sort()
                return self.states[-1][1]

            def last_update(self):
                """Last update to this object."""
                self._sort()
                return self.states[-1][0]

            def states_during(self, start_time, end_time, states_only=True):
                """All states seen between specified times."""
                # TODO: this can't handle attributes having different
                #       times when their state changed; it skips over those
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

            # Manual setters

            def set_state(self, state, time=None):
                """Specify state at a certain time (default is now)."""
                time = time if time else self.clock.now
                # TODO: equality check doesn't quite work, doesn't see changes in nested timeline objects
                # Might work now with the change in at() to copy the state
                #if state == self.at(time):
                #    return
                # TODO: if a state for time already in here, overwrite
                self.states.append((time, state))
                self._stdirty = True

            def add_event(self, event, time=None):
                """Specify an event happening."""
                time = time if time else self.clock.now
                self.events.append((time, event))
                self._evdirty = True

            # Sorting and management

            def _sort(self):
                if self._stdirty:
                    self.states.sort(key=lambda tst: tst[0])
                    self._stdirty = False
                if self._evdirty:
                    self.events.sort(key=lambda tev: tev[0])
                    self._evdirty = False

            def _tsafe(self, value):
                """Timelined version of something."""
                return to_timelined(value, clock=self.clock)

        # Register all setting functions
        for setter in setters:
            def setter_wrap(self, *args, bound_setter_name=setter, **kwargs):
                getattr(super(Timeline, self), bound_setter_name).__call__(*args, **kwargs)
                self.state_change()
            setattr(Timeline, setter, setter_wrap)
        return Timeline
    return class_wrapper




# Special snapshot and timelined objects

# Not exposing the value except through at() should be fine, as this should only be found through containing objects
class SnapshotStatic(object):
    TIMELINED = True
    def __init__(self, value, time):
        self.value = value
        self.time = time
    def at(self, time=None):
        return self.value
    def copy(self, time=None):
        return SnapshotStatic(self.value, time=time if time else self.time)

# Overriding tuple to get all the nice things.
# TODO: any other methods to override?
class SnapshotTuple(tuple):
    TIMELINED = True
    def __new__(cls, iterable=(), time=None):
        assert time
        ret = tuple.__new__(cls, iterable)
        ret.time = time
        return ret
    def at(self, time=None):
        if time and time != self.time:
            return self.copy(time)
        return self
    def __getitem__(self, i):
        return ssat(super().__getitem__(i), self.time)
    def __iter__(self):
        for item in super().__iter__():
            yield ssat(item, self.time)
    def copy(self, time=None):
        # Can't just pass self in as that will go through snapshot().at()
        # So take the real values
        return SnapshotTuple([super(SnapshotTuple, self).__getitem__(i) for i in range(len(self))], time=time if time else self.time)
    def __str__(self):
        return str(tuple(self))

# Mimics a class with attributes, passing values through snapshot and at before returning them
class SnapshotAttrs(object):
    TIMELINED = True
    def __init__(self, attrs, backer, time=None):
        assert time
        for attr in attrs:
            setattr(self, attr, getattr(backer, attr, None))
        self.attrs = set(attrs)
        self.time = time
    def at(self, time=None):
        if time and time != self.time:
            return self.copy(time)
        return self
    def __getattribute__(self, name):
        normal = super().__getattribute__(name)
        if name in self.attrs:
            return ssat(normal, self.time)
        return normal
    def copy(self, time=None):
        # Can't just set self as backer; would go through snapshot().at()
        # Can't just remember backer; that's been changed
        # So create it empty and then populate
        ret = SnapshotAttrs((), self, time=time if time else self.time)
        ret.attrs = set(self.attrs)
        for attr in self.attrs:
            setattr(ret, attr, super().__getattribute__(name))
        return ret
    def __str__(self):
        return str({attr:getattr(self, attr, None) for attr in self.attrs})

# Used for TimelinedDict, but not otherwise exposed
# TODO: Making read-only after creation
# TODO: Other 'getter' methods
class SnapshotDict(dict):
    TIMELINED = True
    def __new__(cls, *args, time=None, **kwargs):
        assert time
        ret = dict.__new__(cls, *args, **kwargs)
        ret.time = time
        return ret
    def at(self, time=None):
        if time and time != self.time:
            return self.copy(time)
        return self
    def __getitem__(self, name):
        return ssat(super().__getitem__(name), self.time)
    def copy(self, time=None):
        # Can't just get each item, need to go direct
        ret = SnapshotDict({}, time=time if time else self.time)
        for key in self.keys():
            ret[key] = super().__getitem__(key)
        return ret
    def __str__(self):
        return str(dict(self))

# Similar to SnapshotDict
class SnapshotSet(set):
    TIMELINED = True
    def __new__(cls, *args, time=None, **kwargs):
        assert time
        ret = set.__new__(cls, *args, **kwargs)
        ret.time = time
        return ret
    def at(self, time=None):
        if time and time != self.time:
            return self.copy(time)
        return self
    def pop(self):
        return ssat(super().pop(), self.time)
    def __iter__(self):
        for item in super().__iter__():
            yield ssat(item, self.time)
    def copy(self, time=None):
        # Need to look at real items
        ret = SnapshotSet((), time=time if time else self.time)
        for item in super().__iter__():
            ret.add(item)
        return ret
    def __str__(self):
        return str(set(self))

# No SnapshotList; no need to use that instead of SnapshotTuple.

# Timelined forms of list, set and dict, since they can't use the default to_state method created by the decorator
# Also, since they use __new__ instead of __init__, they must do setup work
# TODO: All setter methods and timelining of anything added

@timelined(setters=("__setitem__","append","extend","pop","remove","sort",))
# TODO: __delitem__, __iadd__, __imul__, insert
# TODO: Work out which things need to be set to make sure everything goes through _tsafe
class TimelinedList(list):
    def __new__(cls, iterable=(), time=None, clock=None):
        clock = clock if clock else Clock()
        ret = list.__new__(cls, [to_timelined(value, time=time, clock=clock) for value in iterable])
        return ret
    def to_state(self):
        return SnapshotTuple(self, time=self.clock.now)
    def __setitem__(self, i, value):
        super().__setitem__(i, self._tsafe(value))
    def append(self, value):
        super().append(self._tsafe(value))
    def extend(self, iterable):
        super().extend([self._tsafe(value) for value in iterable])

@timelined(setters=("__setitem__","update","pop","clear",))
# TODO: __delitem__, __ior__, editing items/keys, setdefault
class TimelinedDict(dict):
    def __new__(cls, *args, time=None, clock=None, **kwargs):
        # TODO: timelined internal values
        ret = dict.__new__(cls, *args, **kwargs)
        return ret
    def to_state(self):
        return SnapshotDict(self, time=self.clock.now)

@timelined(setters=("add","clear","difference_update","discard","intersection_update",
                    "pop","remove","symmetric_difference_update","update",))
# TODO: __iand__, __ior__, __isub__, __ixor__
class TimelinedSet(set):
    def __new__(cls, *args, time=None, clock=None, **kwargs):
        # TODO: timelined internal values
        ret = set.__new__(cls, *args, **kwargs)
        return ret
    def to_state(self):
        return SnapshotSet(self, time=self.clock.now)


# Utility and generic functions

def is_timelined(obj):
    """Is an object timelined?"""
    return getattr(obj, "IS_TIMELINED", False)

def to_timelined(obj, time=None, clock=None):
    """A timelined version of this object."""
    if is_timelined(obj):
        return obj
    if type(obj) is list:
        return TimelinedList(obj, time=time, clock=clock)
    if type(obj) is set:
        return TimelinedSet(obj, time=time, clock=clock)
    if type(obj) is dict:
        return TimelinedDict(obj, time=time, clock=clock)
    # TODO: Warn about non-int/str/tuple objects getting this far
    # Things here should be static
    return obj

def snapshot(obj, time):
    """The snapshotted form of this object at this time.

A snapshotted object defines an at() method that returns a static or snapshotted object.
To avoid cyclic reference problems, timelined objects get returned as is.
  References to these objects will already be passed through an at() method."""
    if is_timelined(obj):
        return obj
    if type(obj) is tuple:
        return SnapshotTuple(obj, time)
    if type(obj) in (list, set, dict):
        raise ValueError("Cannot snapshot a base list, set or dict; must use Timelined versions.")
    else:
        return SnapshotStatic(obj, time)

def ssat(obj, time):
    """Equivalent to snapshot(obj, time).at(time)."""
    if is_timelined(obj):
        return obj.at(time)
    if type(obj) is tuple:
        return SnapshotTuple(obj, time)
    if type(obj) in (list, set, dict):
        raise ValueError("Cannot snapshot a base list, set or dict; must use Timelined versions.")
    else:
        return obj # SnapshotStatic.at(time) would just send this back


if __name__ == "__main__":
    C = Clock()
    print("make")
    k = TimelinedList((8,),clock=C)
    C.tick()
    print("append")
    k.append([2,3,4])
    C.tick()
    print("subedit")
    k[1].append(4)
    m = k.at(BOTCTime(0,1,0))

    print(m)
