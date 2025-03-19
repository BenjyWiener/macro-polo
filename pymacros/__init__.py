"""Rust-style macros for Python."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cache
import io
import tokenize
from typing import NamedTuple

from ._utils import TupleNewType


__version__ = '0.1.0'


class MacroError(Exception):
    """Base class for macro-processing errors."""


class TranscriptionError(MacroError):
    """Exception raised for macro transcription errors."""


class Token(NamedTuple):
    """Minimal representation of a token."""

    type: int
    string: str


class TokenTree(TupleNewType[Token]):
    """A delimited sequence of tokens."""


@dataclass(frozen=True, slots=True)
class Delimiter:
    """Represents a delimiter which must be kept balanced."""

    open_type: int
    open_string: str | None
    close_type: int
    close_string: str | None

    @staticmethod
    @cache
    def from_token(token: Token) -> 'Delimiter | None':
        """Attempt to create a `Delimiter` from a `Token`."""
        match token:
            case Token(type=tokenize.OP, string='('):
                return Delimiter(*token, tokenize.OP, ')')
            case Token(type=tokenize.OP, string='['):
                return Delimiter(*token, tokenize.OP, ']')
            case Token(type=tokenize.OP, string='{'):
                return Delimiter(*token, tokenize.OP, '}')
            case Token(type=tokenize.INDENT):
                return Delimiter(tokenize.INDENT, None, tokenize.DEDENT, None)
            case Token(type=tokenize.FSTRING_START):
                return Delimiter(
                    tokenize.FSTRING_START, None, tokenize.FSTRING_END, None
                )

        return None

    def matches_open(self, token: Token) -> bool:
        """Check if the given token matches the delimiter's open token."""
        return token.type == self.open_type and (
            self.open_string is None or token.string == self.open_string
        )

    def matches_close(self, token: Token) -> bool:
        """Check if the given token matches the delimiter's close token."""
        return token.type == self.close_type and (
            self.close_string is None or token.string == self.close_string
        )


def lex(source: str) -> Iterator[Token]:
    """Create a normalized token stream from source code."""
    read_source_line = io.StringIO(source).readline
    for raw_token in tokenize.generate_tokens(readline=read_source_line):
        if raw_token.type == tokenize.ENDMARKER:
            continue
        if raw_token.type == tokenize.NEWLINE and raw_token.string == '':
            # Omit implicit trailing newline
            continue
        yield Token(raw_token.type, raw_token.string)


def stringify(tokens: Iterable[Token]) -> str:
    """Construct source code from a token stream."""
    return tokenize.untokenize(tokens)
