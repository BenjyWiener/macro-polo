"""Utilities for parsing macro matchers from source code."""

from collections.abc import Sequence
from functools import cache
import tokenize
from typing import cast

from .. import Token, TokenTree, lex
from .._utils import SliceView
from ..match import (
    DelimitedMacroMatcher,
    Delimiter,
    MacroMatch,
    MacroMatcher,
    MacroMatcherItem,
    MacroMatcherNegativeLookahead,
    MacroMatcherRepeater,
    MacroMatcherRepeaterMode,
    MacroMatcherVar,
    MacroMatcherVarType,
)
from ._utils import DOLLAR_TOKEN, _parse_escaped_dollar, _ParseResult


@cache
def _get_delimited_macro_matcher_parser(delimiter: Delimiter) -> MacroMatcher:
    return MacroMatcher(
        DelimitedMacroMatcher(
            delimiter=delimiter,
            matcher=MacroMatcher(
                MacroMatcherRepeater(
                    matcher=MacroMatcher(
                        MacroMatcherVar('sub_matcher', MacroMatcherVarType.TOKEN_TREE),
                    ),
                    mode=MacroMatcherRepeaterMode.ZERO_OR_MORE,
                ),
            ),
        ),
    )


def _parse_delimited_macro_matcher(
    tokens: Sequence[Token],
) -> _ParseResult[DelimitedMacroMatcher] | None:
    """Try to parse a delimited macro matcher.

    Syntax:
        `($($sub_matcher:tt)*)`
        `[$($sub_matcher:tt)*]`
        `{$($sub_matcher:tt)*}`
        ...
    """
    if len(tokens) < 2:
        return None

    if not (delimiter := Delimiter.from_token(tokens[0])):
        return None

    parser_matcher = _get_delimited_macro_matcher_parser(delimiter)

    if not (match := parser_matcher.match(tokens)):
        return None

    sub_matcher_capture = cast(list[TokenTree], match.captures['sub_matcher'])
    sub_matcher_source = sum(sub_matcher_capture, ())

    if not (sub_matcher := parse_macro_matcher(sub_matcher_source)):
        return None

    return _ParseResult(
        match_size=match.size,
        value=DelimitedMacroMatcher(
            delimiter=delimiter,
            matcher=sub_matcher,
        ),
    )


_MACRO_MATCHER_VAR_PARSER = MacroMatcher(
    DOLLAR_TOKEN,
    MacroMatcherVar('name', MacroMatcherVarType.NAME),
    Token(tokenize.OP, ':'),
    MacroMatcherVar('type', MacroMatcherVarType.NAME),
)


def _parse_macro_matcher_var(
    tokens: Sequence[Token],
) -> _ParseResult[MacroMatcherVar] | None:
    """Try to parse a macro matcher var.

    Syntax:
        `$$ $name:name : $type:name`
    """
    match _MACRO_MATCHER_VAR_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={
                'name': Token(string=name),
                'type': Token(string=type_string),
            },
        ) if type_string in MacroMatcherVarType:
            return _ParseResult(
                match_size=match_size,
                value=MacroMatcherVar(name, MacroMatcherVarType(type_string)),
            )

    return None


_MACRO_MATCHER_REPEATER_PARSER = MacroMatcher(
    DOLLAR_TOKEN,
    DelimitedMacroMatcher(
        delimiter=Delimiter(
            open_type=tokenize.OP,
            open_string='(',
            close_type=tokenize.OP,
            close_string=')',
        ),
        matcher=MacroMatcher(
            MacroMatcherRepeater(
                matcher=MacroMatcher(
                    MacroMatcherVar('sub_matcher', MacroMatcherVarType.TOKEN_TREE),
                ),
                mode=MacroMatcherRepeaterMode.ZERO_OR_MORE,
            ),
        ),
    ),
    MacroMatcherRepeater(
        matcher=MacroMatcher(
            # Match any token as separator except valid repitition modes
            *(
                MacroMatcherNegativeLookahead(Token(tokenize.OP, mode.value))
                for mode in MacroMatcherRepeaterMode
            ),
            MacroMatcherVar('sep', MacroMatcherVarType.TOKEN),
        ),
        mode=MacroMatcherRepeaterMode.ZERO_OR_ONE,
    ),
    MacroMatcherVar('mode', MacroMatcherVarType.OP),
)


def _parse_macro_matcher_repeater(
    tokens: Sequence[Token],
) -> _ParseResult[MacroMatcherRepeater] | None:
    """Try to parse a macro matcher repeater.

    Syntax:
        `$$ ($($sub_matcher:tt)*) $($sep:token)? $mode:op` where (
            $sep not in (*,+,?)
            $mode in (*,+,?)
        )
    """
    match _MACRO_MATCHER_REPEATER_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={
                'sub_matcher': sub_matcher_capture,
                'sep': sep_capture,
                'mode': Token(string=mode_string),
            },
        ) if mode_string in MacroMatcherRepeaterMode:
            sub_matcher = sum(cast(list[TokenTree], sub_matcher_capture), ())
            sep = cast(Token, sep_capture[0]) if sep_capture else None

            return _ParseResult(
                match_size=match_size,
                value=MacroMatcherRepeater(
                    matcher=parse_macro_matcher(sub_matcher),
                    sep=sep,
                    mode=MacroMatcherRepeaterMode(mode_string),
                ),
            )

    return None


_PARSER_FUNCS = (
    _parse_delimited_macro_matcher,
    _parse_macro_matcher_var,
    _parse_macro_matcher_repeater,
    _parse_escaped_dollar,
)


def parse_macro_matcher(source: str | Sequence[Token]) -> MacroMatcher:
    """Parse a macro matcher from source code or a token stream."""
    if isinstance(source, str):
        source = tuple(lex(source))
    tokens = SliceView(source)

    pattern: list[MacroMatcherItem] = []

    while len(tokens) > 0:
        for parser_func in _PARSER_FUNCS:
            if result := parser_func(tokens):
                tokens = tokens[result.match_size :]
                pattern.append(result.value)
                break
        else:
            pattern.append(tokens.popleft())

    return MacroMatcher(*pattern)
