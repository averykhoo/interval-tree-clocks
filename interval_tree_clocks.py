from dataclasses import dataclass
from typing import Optional
from typing import Tuple
from typing import Union


@dataclass(frozen=True)
class IDInteger:
    value: int = 1

    def __post_init__(self):
        # type check
        if not isinstance(self.value, int):
            raise TypeError(self.value)

        # only allowed values are 1 and 0, representing the full and empty interval respectively
        if self.value not in {1, 0}:
            raise ValueError(self.value)

    def fork(self) -> Union[Tuple['IDInteger', 'IDInteger'], Tuple['IDTuple', 'IDTuple']]:

        # the full interval splits into two half intervals
        # (1) -> [(1, 0), (0, 1)]
        if self.value:
            return IDTuple(self, IDInteger(0)), IDTuple(IDInteger(0), self)

        # the empty interval cannot be forked
        else:
            # if it was allowed, the empty interval would split into two empty intervals
            # (0) -> [(0), (0)]
            # return self, self
            raise ZeroDivisionError(self)

    def join(self, other: Union['IDInteger', 'IDTuple']) -> Union['IDInteger', 'IDTuple']:
        if not isinstance(other, (IDInteger, IDTuple)):
            raise TypeError(other)

        # a full interval joined to anything returns a full interval
        # (1) + (...) -> (1)
        if self.value:
            return self

        # an empty interval joined to anything returns the other thing
        # (0) + (...) -> (...)
        else:
            return other

    def normalize(self) -> 'IDInteger':
        # already normalized
        # (1) -> (1)
        # (0) -> (0)
        return self

    def __bool__(self) -> bool:
        # (1) -> Truthy
        # (0) -> Falsy
        return bool(self.value)


@dataclass(frozen=True)
class IDTuple:
    left: Union[IDInteger, 'IDTuple']
    right: Union[IDInteger, 'IDTuple']

    def __post_init__(self):
        # type checks
        if not isinstance(self.left, (IDInteger, IDTuple)):
            raise TypeError(self.left)
        if not isinstance(self.right, (IDInteger, IDTuple)):
            raise TypeError(self.right)

        # the empty interval should be represented as IDInteger(0)
        if not self:
            raise TypeError((self.left, self.right))

    def fork(self) -> Tuple[Union[IDInteger, 'IDTuple'], Union[IDInteger, 'IDTuple']]:
        # if both left and right are non-zero, just split
        # (x, y) -> (x, 0), (0, y)
        if self.left and self.right:
            return IDTuple(self.left, IDInteger(0)), IDTuple(IDInteger(0), self.right)

        # if only left is non-zero, fork the left side
        # (x, 0) -> [(x1, 0), (x2, 0)]
        #           where [x1, x2] = x.fork()
        elif self.left:
            left_1, left_2 = self.left.fork()
            return IDTuple(left_1, IDInteger(0)), IDTuple(left_2, IDInteger(0))

        # if only right is non-zero, for the right side
        # (0, y) -> [(0, y1), (0, y2)]
        #           where [y1, y2] = y.fork()
        elif self.right:
            right_1, right_2 = self.right.fork()
            return IDTuple(IDInteger(0), right_1), IDTuple(IDInteger(0), right_2)

        # this should never happen because an empty IDTuple should not exist
        else:
            # if it was allowed, it should behave the same as IDInteger(0).fork()
            # (0, 0) -> [(0), (0)]
            # return IDInteger(0), IDInteger(0)
            raise ZeroDivisionError(self)

    def join(self, other: Union['IDInteger', 'IDTuple']) -> Union[IDInteger, 'IDTuple']:
        # joining to either a full or empty interval
        if isinstance(other, IDInteger):
            # (x, y) + (1) -> (1)
            if other.value:
                return other

            # (x, y) + (0) -> (x, y)
            else:
                return self

        # join left and right halves separately, then normalize
        # (x, y) + (a, b) -> (x + a, y + b)
        elif isinstance(other, IDTuple):
            return IDTuple(self.left.join(other.left), self.right.join(other.right)).normalize()

        # wrong type
        else:
            raise TypeError(other)

    def normalize(self) -> Union[IDInteger, 'IDTuple']:
        # normalize both halves
        left = self.left.normalize()
        right = self.right.normalize()

        # merge into a full or empty interval if both halves are full or empty
        # (0, 0) -> 0
        # (1, 1) -> 1
        if isinstance(left, IDInteger) and isinstance(right, IDInteger):
            if left.value == right.value:
                return left

        # otherwise, return a new IDTuple with both halves normalized
        return IDTuple(left, right)

    def __bool__(self) -> bool:
        # Truthy if either side is Truthy
        # Falsy if and only if both sides are Falsy
        return bool(self.left) or bool(self.right)


@dataclass(frozen=True, eq=False)
class Event:
    base: int = 0
    top_left: Optional['Event'] = None
    top_right: Optional['Event'] = None

    def __post_init__(self):
        # check base >= 0
        if not isinstance(self.base, int):
            raise TypeError(self.base)
        if self.base < 0:
            raise ValueError(self.base)

        # check that top left is not an empty Event
        if self.top_left is not None:
            if not isinstance(self.top_left, Event):
                raise TypeError(self.top_left)
            if not self.top_left:
                raise ValueError(self.top_left)  # should be None

        # check that top right is not an empty Event
        if self.top_right is not None:
            if not isinstance(self.top_right, Event):
                raise TypeError(self.top_right)
            if not self.top_right:
                raise ValueError(self.top_right)  # should be None

    @property
    def left(self):
        _self_top_left = self.top_left or Event()
        return _self_top_left.replace(base=_self_top_left.base + self.base)

    @property
    def right(self):
        _self_top_right = self.top_right or Event()
        return _self_top_right.replace(base=_self_top_right.base + self.base)

    @property
    def height(self):
        if self.top_left is None and self.top_right is None:
            return self.base
        elif self.top_left is None:
            return self.base + self.right.height
        elif self.top_right is None:
            return self.base + self.left.height
        else:
            return self.base + max(self.top_left.height, self.top_right.height)

    def __bool__(self):
        if not self.base:
            if self.top_left is None or not self.top_left:
                if self.top_right is None or not self.top_right:
                    return False
        return True

    def __eq__(self, other: 'Event'):
        if not isinstance(other, Event):
            raise TypeError(other)

        _self = self.normalize()
        _other = other.normalize()

        if _self.base != _other.base:
            return False
        if _self.top_left != _other.top_left:
            return False
        if _self.top_right != _other.top_right:
            return False
        return True

    def __le__(self, other: 'Event'):
        if not isinstance(other, Event):
            raise TypeError(other)

        _self = self.normalize()
        _other = other.normalize()

        if (_self.top_left or _self) > (_other.top_left or _other):
            return False
        if (_self.top_right or _self) > (_other.top_right or _other):
            return False
        return True

    def fill(self, interval: Union[IDInteger, IDTuple]):
        raise NotImplementedError

    def grow(self, interval: Union[IDInteger, IDTuple]):
        raise NotImplementedError

    def join(self, other: 'Event'):
        if not isinstance(other, Event):
            raise TypeError(other)

        if not self:
            return other
        elif not other:
            return self
        elif self.base < other.base:
            return other.join(self)

        if self.top_left and other.top_left:
            top_left = self.top_left.join(other.top_left.truncate_from_bottom(self.base - other.base))
        elif self.top_left:
            top_left = self.top_left
        elif other.top_left:
            top_left = other.top_left.truncate_from_bottom(self.base - other.base)
        else:
            top_left = None

        if self.top_right and other.top_right:
            top_right = self.top_right.join(other.top_right.truncate_from_bottom(self.base - other.base))
        elif other.top_right:
            top_right = other.top_right.truncate_from_bottom(self.base - other.base)
        elif self.top_right:
            top_right = self.top_right
        else:
            top_right = None

        return Event(self.base, top_left or None, top_right or None)

    def truncate_from_bottom(self,
                             distance: Optional[int] = None,
                             ) -> 'Event':
        base = self.base - distance
        top_left = self.top_left
        top_right = self.top_right

        # you can depress the base below zero to lower the top parts
        if base < 0:
            if top_left is not None:
                top_left = top_left.replace(base=top_left.base + base)
            if top_right is not None:
                top_right = top_right.replace(base=top_right.base + base)
            base = 0
        return Event(base, top_left or None, top_right or None)

    def replace(self,
                base: Optional[int] = None,
                top_left: Optional[Union[int, 'Event']] = None,
                top_right: Optional[Union[int, 'Event']] = None,
                ) -> 'Event':
        if base is None:
            base = self.base
        if top_left is None:
            top_left = self.top_left
        if top_right is None:
            top_right = self.top_right

        return Event(base, top_left or None, top_right or None)

    def normalize(self) -> 'Event':
        # already normalized
        if self.top_left is None and self.top_right is None:
            return self

        # normalize top left
        elif self.top_left is not None and self.top_right is None:
            return Event(self.base, self.top_left.normalize(), None)

        # normalize top right
        elif self.top_left is None:
            return Event(self.base, None, self.top_right.normalize())

        # normalize both recursively
        else:
            top_left = self.top_left.normalize()
            top_right = self.top_right.normalize()
            denominator = min(top_left.base, top_right.base)

            # move denominator to base
            base = self.base + denominator
            top_left = top_left.replace(base=top_left.base - denominator)
            top_right = top_right.replace(base=top_right.base - denominator)

            # replace with None if it's an empty event
            return Event(base, top_left or None, top_right or None)
