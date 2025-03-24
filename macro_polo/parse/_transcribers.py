"""Utilities for parsing macro transcribers from source code."""

from collections.abc import Iterable, Sequence
import tokenize
from typing import cast

from .. import Delimiter, Token, TokenTree, lex
from .._utils import SliceView
from ..match import (
    DelimitedMacroMatcher,
    MacroMatch,
    MacroMatcher,
    MacroMatcherNegativeLookahead,
    MacroMatcherRepeater,
    MacroMatcherRepeaterMode,
    MacroMatcherVar,
    MacroMatcherVarType,
)
from ..transcribe import (
    MacroTransciberSubstitution,
    MacroTranscriber,
    MacroTranscriberItem,
    MacroTranscriberRepeater,
)
from ._utils import DOLLAR_TOKEN, _parse_dollar_escape, _ParseResult, _replace_digraphs


_MACRO_TRANSCRIBER_SUBSTITUTION_PARSER = MacroMatcher(
    DOLLAR_TOKEN,
    MacroMatcherVar('name', MacroMatcherVarType.NAME),
)


def _parse_macro_transcriber_substitution(
    tokens: Sequence[Token],
) -> _ParseResult[MacroTransciberSubstitution] | None:
    """Try to parse a macro transcriber substitution.

    Syntax:
        `$$ $name:name`
    """
    match _MACRO_TRANSCRIBER_SUBSTITUTION_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={'name': Token(string=name)},
        ):
            return _ParseResult(
                match_size=match_size,
                value=MacroTransciberSubstitution(name),
            )

    return None


_MACRO_TRANSCRIBER_REPEATER_PARSER = MacroMatcher(
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
                    MacroMatcherVar('sub_transcriber', MacroMatcherVarType.TOKEN_TREE),
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


def _parse_macro_transcriber_repeater(
    tokens: Sequence[Token],
) -> _ParseResult[MacroTranscriberRepeater] | None:
    """Try to parse a macro matcher repeater.

    Syntax:
        `$$ ($($sub_matcher:tt)*) $($sep:token)? $mode:op` where (
            $sep not in (*,+,?)
            $mode in (*,+,?)
        )
    """
    match _MACRO_TRANSCRIBER_REPEATER_PARSER.match(tokens):
        case MacroMatch(
            size=match_size,
            captures={
                'sub_transcriber': sub_transcriber_capture,
                'sep': sep_capture,
                'mode': Token(string=mode_string),
            },
        ) if mode_string in MacroMatcherRepeaterMode:
            sub_transcriber = sum(cast(list[TokenTree], sub_transcriber_capture), ())
            sep = cast(Token, sep_capture[0]) if sep_capture else None

            return _ParseResult(
                match_size=match_size,
                value=MacroTranscriberRepeater(
                    transcriber=parse_macro_transcriber(sub_transcriber),
                    sep=sep,
                ),
            )

    return None


_PARSER_FUNCS = [
    _parse_macro_transcriber_substitution,
    _parse_macro_transcriber_repeater,
    _parse_dollar_escape,
]


def _parse_macro_transcriber_internal(tokens: Sequence[Token]) -> MacroTranscriber:
    """Parse a macro transcriber from a token sequence.

    Unlike `parse_macro_transcriber`, this function does not perform digraph substitution.
    """
    tokens = SliceView(tokens)

    pattern: list[MacroTranscriberItem] = []

    while len(tokens) > 0:
        for parser_func in _PARSER_FUNCS:
            if result := parser_func(tokens):
                tokens = tokens[result.match_size :]
                pattern.append(result.value)
                break
        else:
            pattern.append(tokens.popleft())

    return MacroTranscriber(*pattern)


def parse_macro_transcriber(source: str | Iterable[Token]) -> MacroTranscriber:
    """Parse a macro transcriber from source code or a token stream."""
    if isinstance(source, str):
        source = tuple(lex(source))

    tokens = tuple(_replace_digraphs(source))

    return _parse_macro_transcriber_internal(tokens)
