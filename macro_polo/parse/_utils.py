from collections.abc import Iterable, Sequence
import tokenize
from typing import NamedTuple

from .. import Token


class _ParseResult[T](NamedTuple):
    match_size: int
    value: T


DOLLAR_TOKEN = Token(tokenize.OP, '$')


_ESCAPES = {
    DOLLAR_TOKEN: DOLLAR_TOKEN,
}


def _parse_dollar_escape(
    tokens: Sequence[Token],
) -> _ParseResult[Token] | None:
    """Try to parse an escaped dollar ($) token.

    Syntax:
        `$$` (=> `$`)
    """
    if len(tokens) >= 2 and tokens[0] == tokens[1] == DOLLAR_TOKEN:
        return _ParseResult(match_size=2, value=DOLLAR_TOKEN)
    return None


_DOLLAR_DIGRAPHS = {
    Token(tokenize.OP, '^'): Token(tokenize.NEWLINE, '\n'),
    Token(tokenize.OP, '>'): Token(tokenize.INDENT, ''),
    Token(tokenize.OP, '<'): Token(tokenize.DEDENT, ''),
    Token(tokenize.NAME, 'pass'): Token(tokenize.DEDENT, ''),
}


def _replace_digraphs(tokens: Iterable[Token]):
    """Replace digraph alternatives in a token stream with their cononical equivalents.

    This allows matching against indented blocks in patterns where the Python tokenizer
    wouldn't normally emit INDENT/DEDENT tokens (such as within repitions, where the
    parentheses would strip indenation).
    """
    last_token_was_dollar = False
    for token in tokens:
        if last_token_was_dollar:
            match token:
                case Token(tokenize.OP, '^'):
                    yield Token(tokenize.NEWLINE, '\n')
                case Token(tokenize.OP, '>'):
                    yield Token(tokenize.INDENT, '')
                case Token(tokenize.OP, '<'):
                    yield Token(tokenize.DEDENT, '')
                case Token(tokenize.NAME, 'pass'):
                    pass
                case _:
                    # Leave unchanged.
                    # This also prevents the second $ in a $$ sequence from being treated as
                    # a potential digraph prefix.
                    yield DOLLAR_TOKEN
                    yield token
            last_token_was_dollar = False
        elif token == DOLLAR_TOKEN:
            last_token_was_dollar = True
        else:
            yield token
