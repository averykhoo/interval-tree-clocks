from dataclasses import dataclass
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
