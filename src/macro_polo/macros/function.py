"""Function-like macros."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize
from typing import cast

from .. import MacroError, Token, TokenTree
from ..match import MacroMatch
from ..parse import parse_macro_matcher, parse_macro_transcriber
from .types import Macro, PartialMatchMacro


@dataclass(frozen=True, slots=True)
class FunctionMacroInvokerMacro(PartialMatchMacro):
    """A macro that processes function-like macro invocations.

    Macros are defined by the `macros` mapping (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, Macro] = field(default_factory=dict)

    _function_style_macro_invocation_matcher = parse_macro_matcher(
        '$name:name!$[(($($body:tt)*)) | ([$($body:tt)*]) | ({$($body:tt)*})]'
    )

    _block_style_macro_invocation_matcher = parse_macro_matcher(
        '$name:name!: $> $($body:tt)* $<'
    )

    _body_transcriber = parse_macro_transcriber('$($body)*')

    def _invoke_macro(self, name: str, body: Sequence[Token]) -> Sequence[Token]:
        """Invoke a macro."""
        macro = self.macros.get(name)
        if macro is None:
            raise MacroError(
                f'invoking function-like macro: cannot find macro named {name!r}'
            )

        result = macro(body)
        if result is None:
            raise MacroError(
                f'invoking function-like macro {name!r}: '
                "body didn't match expected pattern"
            )
        return result

    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence."""
        match self._function_style_macro_invocation_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name)} as captures,
            ):
                body = tuple(self._body_transcriber.transcribe(captures))
                result = self._invoke_macro(name, body)

                return result, match_size

        match self._block_style_macro_invocation_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name)} as captures,
            ):
                body = tuple(self._body_transcriber.transcribe(captures))
                result = self._invoke_macro(name, body)

                return (*result, Token(tokenize.NEWLINE, '\n')), match_size

        return (), 0
