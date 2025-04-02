"""Function-like macros."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize

from .. import MacroError, Token
from ..match import MacroMatch
from ..parse import parse_macro_matcher, parse_macro_transcriber
from .types import Macro, PartialMatchMacro


@dataclass(frozen=True, slots=True)
class FunctionMacroInvokerMacro(PartialMatchMacro):
    """A macro that processes function-like macro invocations.

    The syntax for invoking a function-style macro is:

    .. parsed-literal::

        *macro_name*!(*input tokens*)

    or

    .. parsed-literal::

        *macro_name*![*input tokens*]

    or

    .. parsed-literal::

        *macro_name*!{*input tokens*}

    or

    .. parsed-literal::

        *macro_name*!:
            *input*
            *tokens*

    .. important::

        Due to the way Python's tokenizer works, indentation and newlines are only preserved
        by the last (block) style.

    When invoked, the registered macro is called with a single argument, the token
    sequence passed as input.

    Macros are defined by :attr:`macros` (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, Macro] = field(default_factory=dict)
    """A mapping of names to function macros.

    When a function macro is invoked, its name is looked up here.

    This mapping may be shared with other macros, such as a
    :class:`~macro_polo.macros.ImporterMacro`.
    """

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
