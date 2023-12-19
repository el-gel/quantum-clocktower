import functools

def unaries(methods):
    """Turn these method calls into unary calls to return MultiValues."""
    def method_wrapper(cls):
        @functools.wraps(cls, updated=())
        class UnaryWrap(cls):
            pass
        for method in methods:
            # Late binding closures means we need bound_method
            def mwrap(self, *args, bound_method=method, **kwargs):
                return MultiValue([getattr(x, bound_method).__call__(*args, **kwargs) for x in self], rem_dups=True)
            setattr(UnaryWrap, method, mwrap)
        return UnaryWrap
    return method_wrapper

def binaries(methods):
    """Turn these method calls into binary calls to return MultiValues. Second value can be a MultiValue or single valued."""
    def method_wrapper(cls):
        @functools.wraps(cls, updated=())
        class BinaryWrap(cls):
            pass
        for method in methods:
            # Late binding closures means we need bound_method
            def mwrap(self, other, *args, bound_method=method, **kwargs):
                if isinstance(other, MultiValue):
                    return MultiValue([getattr(x, bound_method).__call__(y, *args, **kwargs) for x in self for y in other], rem_dups=True)
                else:
                    return MultiValue([getattr(x, bound_method).__call__(other, *args, **kwargs) for x in self], rem_dups=True)
            setattr(BinaryWrap, method, mwrap)
        return BinaryWrap
    return method_wrapper

@unaries(("__ceil__","__float__","__floor__","__int__","__invert__",
          "__neg__","__pos__","__round__","__trunc__",))
@binaries(("__add__","__eq__","__floordiv__","__ge__","__gt__","__le__","__lshift__","__lt__",
           "__mod__","__mul__","__ne__","__pow__","__radd__","__rand__","__rdiv__","__rfloordiv__",
           "__rlshift__","__rmod__","__rmul__","__ror__","__rpow__","__rrshift__","__rshift__",
           "__rsub__","__rtruediv__","__rxor__","__sub__","__truediv__","__xor__","__contains__",))
# Methods optimised in class: __or__, __and__
# Methods deliberately not included: __bool__ (better to force usage any() or all(), else bugs)
# Methods with special function: __getattribute__ (tries to get from values if not in self)
class MultiValue(tuple):
    """Multiple options, with attributes and operations transparently passed through to values.

Does not make any guarantees about orderings or sizes of derived properties- duplicates are removed."""
    def __new__(cls, iterable=(), rem_dups=False):
        """Pass in rem_dups=True if there might be duplicates in the values."""
        if rem_dups:
            no_dups = []
            for val in iterable:
                if val in no_dups:
                    continue
                no_dups.append(val)
            return tuple.__new__(cls, no_dups)
        return tuple.__new__(cls, iterable)
    

    # Conversion functions

    def to_bool(self, truth_fn=bool):
        """Return a MultiValue of the boolean values of these options.

truth_fn: Optional function for deciding truthiness; e.g., >= 2"""
        out = set()
        for val in self:
            if truth_fn(val):
                out.add(True)
                if False in out:
                    break
            else:
                out.add(False)
                if True in out:
                    break
        return MultiValue(out)

    # Specially handled pass-throughs

    def __getattribute__(self, name):
        if hasattr(self, name):
            return super().__getattribute__(name)
        return MultiValue([getattr(val, name) for val in self.values], rem_dups=True)

    # Optimised or removed __ operations

    def __bool__(self):
        # Not going to turn to single valued if only one option. Otherwise, will allow annoying bugs.
        raise NotImplementedError("Must use any or all to get single valued boolean. Use to_bool to get a boolean MultiValue.")

    def __or__(self, other):
        """A MultiValue of all possible boolean | combinations"""
        if isinstance(other, MultiValue):
            if len(other) == 0:
                return MultiValue()
            # Minor optimisation over using self and other to_bool
            # Hunt through other only after finding a False in self
            out = set()
            foundF = False
            for val in self:
                if val:
                    out.add(True)
                    if foundF:
                        break
                elif not foundF:
                    foundF = True
                    # Now check bool values of other
                    if True in out:
                        # Already got a True in self, so only care about False in other
                        if not all(other):
                            out.add(False)
                        # Hit all truth options now
                        return MultiValue(out)
                    else:
                        # Looking for both True and False, so use to_bool
                        out.update(other.to_bool())
                        if True in out:
                            # Now seen everything - otherwise, allow hunt for True in self
                            return MultiValue(out)
            return MultiValue(out)
        else:
            # Treat other as single valued
            # If True, then always True (assuming any options in self)
            # else same as self's boolean values
            if other and len(self):
                return MultiValue([True])
            else:
                return self.to_bool()

    def __and__(self, other):
        """A MultiValue of all possible boolean & combinations"""
        if isinstance(other, MultiValue):
            if len(other) == 0:
                return MultiValue()
            # Minor optimisation over using self and other to_bool
            # Hunt through other only after finding a True in self
            out = set()
            foundT = False
            for val in self:
                if not val:
                    out.add(False)
                    if foundT:
                        break
                elif not foundT:
                    foundT = True
                    # Now check bool values of other
                    if False in out:
                        # Already got a False in self, so only care about True in other
                        if any(other):
                            out.add(True)
                        # Hit all truth options now
                        return MultiValue(out)
                    else:
                        # Looking for both True and False, so use to_bool
                        out.update(other.to_bool())
                        if False in out:
                            # Now seen everything - otherwise, allow hunt for False in self
                            return MultiValue(out)
            return MultiValue(out)
        else:
            # Treat other as single valued
            # If False, then always False (assuming any options in self)
            # else same as self's boolean values
            if (not other) and len(self):
                return MultiValue([False])
            else:
                return self.to_bool()

mv = MultiValue

a = mv(range(10))
b = mv(range(-5,5))
