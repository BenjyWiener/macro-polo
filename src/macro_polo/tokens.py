"""Utilities for working with tokens."""

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from functools import cache
import io
from itertools import pairwise
import tokenize
from typing import NamedTuple

from ._utils import TupleNewType


class Token(NamedTuple):
    """Minimal representation of a token."""

    type: int
    """The token's :mod:`type code <token>`."""

    string: str
    """The string representation of the token."""


class TokenTree(TupleNewType[Token]):
    """A delimited sequence of tokens.

    :type args: Token
    """


@dataclass(frozen=True, slots=True)
class Delimiter:
    """Represents a delimiter which must be kept balanced."""

    open_type: int
    """Type code of the opening token."""

    open_string: str | None
    """String representation of the opening token.

    If ``None``, only :attr:`open_type` is checked.
    """

    close_type: int
    """Type code of the closing token."""

    close_string: str | None
    """String representation of the closing token.

    If ``None``, only :attr:`close_type` is checked.
    """

    @staticmethod
    @cache
    def from_token(token: Token) -> 'Delimiter | None':
        """Attempt to create a :class:`Delimiter` from a :class:`Token`."""
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
    r"""Create a simplified token stream from source code.

    Some simplifications are applied to make matching easier:

    * Semantically innert tokens, such as :data:`~token.NL` and :data:`~token.COMMENT`,
      are stripped.
    * :data:`~token.NEWLINE`\ -:data:`~token.INDENT` and
      :data:`~token.NEWLINE`\ -:data:`~token.DEDENT` pairs are reduced to
      :data:`~token.INDENT` and :data:`~token.DEDENT`, respectively. (This is reversed
      by :func:`desimplify`.)
    * :data:`~token.INDENT` and :data:`~token.NEWLINE` tokens' strings are normalized.
    * The trailing :data:`~token.NEWLINE` and :data:`~token.ENDMARKER` are stripped.
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
    """Revert simplifications made by :func:`lex` and fix indentation.

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
