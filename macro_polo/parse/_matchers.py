"""Utilities for parsing macro matchers from source code."""

from collections.abc import Iterable, Sequence
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
    MacroMatcherUnion,
    MacroMatcherVar,
    MacroMatcherVarType,
)
from ._utils import DOLLAR_TOKEN, _parse_dollar_escape, _ParseResult, _replace_digraphs


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

    sub_matcher = _parse_macro_matcher_internal(sub_matcher_source)

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
                    matcher=_parse_macro_matcher_internal(sub_matcher),
                    sep=sep,
                    mode=MacroMatcherRepeaterMode(mode_string),
                ),
            )

    return None


_MACRO_MATCHER_UNION_PARSER = MacroMatcher(
    DOLLAR_TOKEN,
    DelimitedMacroMatcher(
        delimiter=Delimiter(
            open_type=tokenize.OP,
            open_string='[',
            close_type=tokenize.OP,
            close_string=']',
        ),
        matcher=MacroMatcher(
            MacroMatcherRepeater(
                matcher=MacroMatcher(
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
                                    MacroMatcherVar(
                                        'variant',
                                        MacroMatcherVarType.TOKEN_TREE,
                                    ),
                                ),
                                mode=MacroMatcherRepeaterMode.ZERO_OR_MORE,
                            ),
                        ),
                    ),
                ),
                sep=Token(tokenize.OP, '|'),
                mode=MacroMatcherRepeaterMode.ONE_OR_MORE,
            )
        ),
    ),
)


def _parse_macro_matcher_union(
    tokens: Sequence[Token],
) -> _ParseResult[MacroMatcherUnion] | None:
    """Try to parse a macro matcher union.

    Syntax:
        `$$ [$(($sub_matcher:tt))|+]
    """
    match _MACRO_MATCHER_UNION_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={'variant': list(variant_captures)},
        ):
            variants = (
                parse_macro_matcher(sum(variant_capture, ()))
                for variant_capture in cast(list[list[TokenTree]], variant_captures)
            )

            return _ParseResult(
                match_size=match_size,
                value=MacroMatcherUnion(*variants),
            )

    return None


_MACRO_MATCHER_NEGATIVE_LOOKAHEAD_PARSER = MacroMatcher(
    DOLLAR_TOKEN,
    DelimitedMacroMatcher(
        delimiter=Delimiter(
            open_type=tokenize.OP,
            open_string='[',
            close_type=tokenize.OP,
            close_string=']',
        ),
        matcher=MacroMatcher(
            Token(tokenize.OP, '!'),
            MacroMatcherRepeater(
                matcher=MacroMatcher(
                    MacroMatcherVar('sub_matcher', MacroMatcherVarType.TOKEN_TREE),
                ),
                mode=MacroMatcherRepeaterMode.ZERO_OR_MORE,
            ),
        ),
    ),
)


def _parse_macro_matcher_negagtive_lookahead(
    tokens: Sequence[Token],
) -> _ParseResult[MacroMatcherNegativeLookahead] | None:
    """Try to parse a macro matcher negative lookahead.

    Syntax:
        `$$ [ ! $($sub_matcher:tt)* ]
    """
    match _MACRO_MATCHER_NEGATIVE_LOOKAHEAD_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={'sub_matcher': sub_matcher_capture},
        ):
            sub_matcher = sum(cast(list[TokenTree], sub_matcher_capture), ())

            return _ParseResult(
                match_size=match_size,
                value=MacroMatcherNegativeLookahead(
                    *_parse_macro_matcher_internal(sub_matcher)
                ),
            )

    return None


_PARSER_FUNCS = (
    _parse_delimited_macro_matcher,
    _parse_macro_matcher_var,
    _parse_macro_matcher_repeater,
    _parse_macro_matcher_union,
    _parse_macro_matcher_negagtive_lookahead,
    _parse_dollar_escape,
)


def _parse_macro_matcher_internal(tokens: Sequence[Token]) -> MacroMatcher:
    """Parse a macro matcher from a token sequence.

    Unlike `parse_macro_matcher`, this function does not perform digraph substitution.
    """
    tokens = SliceView(tokens)

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


def parse_macro_matcher(source: str | Iterable[Token]) -> MacroMatcher:
    """Parse a macro matcher from source code or a token stream."""
    if isinstance(source, str):
        source = lex(source)

    tokens = tuple(_replace_digraphs(source))

    return _parse_macro_matcher_internal(tokens)
