from collections.abc import Sequence
import tokenize
from typing import NamedTuple

from .. import Token


class _ParseResult[T](NamedTuple):
    match_size: int
    value: T


DOLLAR_TOKEN = Token(tokenize.OP, '$')


def _parse_escaped_dollar(
    tokens: Sequence[Token],
) -> _ParseResult[Token] | None:
    """Try to parse an escaped dollar ($) token.

    Syntax:
        `$$`
    """
    if len(tokens) >= 2 and tokens[0] == tokens[1] == DOLLAR_TOKEN:
        return _ParseResult(
            match_size=2,
            value=DOLLAR_TOKEN,
        )
    return None
