"""Predefined macros."""

from collections.abc import Sequence
import tokenize

from .. import Token, stringify


def stringify_macro(tokens: Sequence[Token]) -> Sequence[Token] | None:
    """Render tokens to a string of source code."""
    return (Token(tokenize.STRING, repr(stringify(tokens))),)


DEFAULT_NAMED_MACROS = {
    'stringify': stringify_macro,
}
