"""Utility functions and types."""

from collections.abc import Iterator, Sequence
from typing import Self, overload


class TupleNewType[T](tuple[T, ...]):
    """Helper class for creating subclasses of tuple."""

    def __new__(cls, *args: T) -> Self:
        return super().__new__(cls, args)

    def __repr__(self) -> str:
        return self.__class__.__name__ + super().__repr__()

    def __rich_repr__(self) -> Iterator[tuple[None, T]]:
        for item in self:
            yield (None, item)


class SliceView[T](Sequence[T]):
    """A view-like wrapper for slices of sequences.

    Assumes the underlying sequence does not change.
    """

    def __init__(self, seq: Sequence[T], *, offset: int = 0, size: int = -1):
        if offset < 0:
            offset += len(seq)

        if size < 0:
            size = len(seq) - offset

        if len(seq) < offset + size:
            raise ValueError('SliceView bounds out of range')

        if isinstance(seq, SliceView):
            offset += seq.offset
            seq = seq._seq

        self._seq: Sequence[T] = seq
        self.offset: int = offset
        self.size: int = size

    def __len__(self):
        return self.size

    def _compute_index(self, index: int) -> int:
        """Convert an index into self into a (positive) index into self._seq."""
        if index >= 0:
            return self.offset + index
        return self.offset + self.size + index

    @overload
    def __getitem__(self, key: int) -> T: ...

    @overload
    def __getitem__(self, key: slice) -> 'SliceView[T]': ...

    def __getitem__(self, key: int | slice) -> 'T | SliceView[T]':
        if isinstance(key, int):
            computed_index = self._compute_index(key)

            if not (self.offset <= computed_index < self.offset + self.size):
                raise IndexError('SliceView index of range')

            return self._seq[computed_index]

        if key.step is not None:
            raise ValueError('SliceView does not support slice-indexing with step')

        last_index = self._compute_index(-1)

        if key.start is None:
            new_offset = self.offset
        else:
            new_offset = self._compute_index(key.start)
            # Clamp `new_offset` to [self.offset, last_index + 1]
            new_offset = max(self.offset, min(new_offset, last_index + 1))

        if key.stop is None:
            stop = last_index + 1
        else:
            stop = self._compute_index(key.stop)
            # Clamp `stop` to [new_offset, last_index + 1]
            stop = max(new_offset, min(stop, last_index + 1))

        return SliceView(
            self._seq,
            offset=new_offset,
            size=stop - new_offset,
        )

    def pop(self) -> T:
        """Pop and return the last element.

        Does not affect the underlying sequence.
        """
        if self.size == 0:
            raise IndexError('pop from an empty SliceView')

        value = self[-1]
        self.size -= 1
        return value

    def popleft(self) -> T:
        """Pop and return the first element.

        Does not affect the underlying sequence.
        """
        if self.size == 0:
            raise IndexError('pop from an empty SliceView')

        value = self[0]
        self.offset += 1
        self.size -= 1
        return value
