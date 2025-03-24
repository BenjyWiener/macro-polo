"""Rust-style macros for Python."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cache
import io
from itertools import pairwise
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
    """Create a simplified token stream from source code.

    Some simplifications are applied to make matching easier:
      - Semantically innert tokens, such as NL and COMMENT, are stripped.
      - NEWLINE-INDENT and NEWLINE-DEDENT pairs are reduced to INDENT and DEDENT,
        respectively. (This is reversed by `desimplify`.)
      - INDENT and NEWLINE tokens' strings are normalized.
      - The trailing NEWLINE and ENDMARKER are stripped.
    """
    read_source_line = io.StringIO(source).readline

    # The final token will never appear as the first item in a pair, but that's okay
    # since the last token will be ENDMARKER, which we want to strip anyway.
    token_pairs = pairwise(
        Token(raw_token.type, raw_token.string)
        for raw_token in tokenize.generate_tokens(readline=read_source_line)
        # NL (non-terminating newline) tokens can break up NEWLINE/DEDENT pairs, so we
        # remove them here, along with comments.
        if raw_token.type not in (tokenize.NL, tokenize.COMMENT)
    )

    for token, next_token in token_pairs:
        match token, next_token:
            case Token(type=tokenize.NEWLINE, string=''), _:
                # Omit implicit trailing NEWLINE
                continue
            case (
                Token(type=tokenize.NEWLINE),
                Token(type=tokenize.INDENT | tokenize.DEDENT),
            ):
                # Omit NEWLINEs before INDENTs and DEDENTs to simplify matching
                continue
            case Token(type=tokenize.NEWLINE), _:
                # Normalize NEWLINEs
                yield Token(tokenize.NEWLINE, '\n')
            case Token(type=tokenize.INDENT), _:
                # Normalize INDENTs
                yield Token(tokenize.INDENT, '')
            case _:
                yield token


def desimplify(tokens: Iterable[Token], *, indent: str = '    ') -> Iterator[Token]:
    """Revert simplifications made by `lex`.

    Only reverts simplifications that change semantics.
    """
    indentation_level = 0

    for token in tokens:
        match token:
            case Token(type=tokenize.INDENT):
                indentation_level += 1
                # Insert a NEWLINE before INDENT tokens
                yield Token(tokenize.NEWLINE, '\n')
                # Repair indentation
                yield Token(tokenize.INDENT, indent * indentation_level)
            case Token(type=tokenize.DEDENT):
                indentation_level -= 1
                # Insert a NEWLINE before DEDENT tokens
                yield Token(tokenize.NEWLINE, '\n')
                yield token
            case _:
                yield token


def stringify(tokens: Iterable[Token]) -> str:
    """Construct source code from a token stream."""
    return tokenize.untokenize(desimplify(tokens))
