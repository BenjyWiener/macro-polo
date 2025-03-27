"""Macro type definitions."""

from abc import abstractmethod
from collections.abc import Sequence
from typing import Protocol

from .. import Token


class Macro(Protocol):
    """Transforms a token sequence."""

    @abstractmethod
    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        This method should return a new token sequence, or `None` if the input sequence
        fails to match.
        """


class PartialMatchMacro(Protocol):
    """Transforms the beginning of a token sequence."""

    @abstractmethod
    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence.

        This method should return a tuple of (token sequence, number of tokens matched).
        """


class ParameterizedMacro(Protocol):
    """Higher-order macro that takes a token sequence and produces a standard macro."""

    @abstractmethod
    def __call__(
        self, parameters_tokens: Sequence[Token]
    ) -> tuple[Sequence[Token], Macro]:
        """Produce a specialized macro using the provided parameters."""
