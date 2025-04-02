"""Decorator-style macros."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize

from .. import MacroError, Token, stringify
from .._utils import SliceView
from ..match import MacroMatch
from ..parse import parse_macro_matcher, parse_macro_transcriber
from .types import ParameterizedMacro, PartialMatchMacro


def _stringify_invocation(name: str, parameters: Sequence[Token]) -> str:
    return f'@![{name}({stringify(parameters)})]'


class DecoratorMacroError(MacroError):
    """Error during invocation of decorator-style macros."""

    def __init__(self, name: str, parameters: Sequence[Token], msg: str):
        """Create a new DecoratorStyleMacroError."""
        super().__init__(f'invoking {_stringify_invocation(name, parameters)!r}: {msg}')


@dataclass(frozen=True, slots=True)
class DecoratorMacroInvokerMacro(PartialMatchMacro):
    """A macro that processes decorator-style macro invocations.

    The syntax for invoking a decorator-style macro is :samp:`@![{name}({parameters})]`
    or :samp:`@![{name}]` (equivalent to :samp:`@![{name}()]`).

    Decorator-style macro invocations must immediately precede a "block", defined as
    either a single newline-terminated line, or a line followed by an indented block.

    When invoked, the registered macro is called with two arguments:

    1. :samp:`{parameters}` (as a token sequence)
    2. the block immediately following the invocation (as a token sequence).

    When multiple decorator-style macros are stacked, they are invoked from bottom to
    top.

    Macros are defined by :attr:`macros` (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, ParameterizedMacro] = field(default_factory=dict)
    """A mapping of names to decorator macros.

    When a decorator macro is invoked, its name is looked up here.

    This mapping may be shared with other macros, such as a
    :class:`~macro_polo.macros.ImporterMacro`.
    """

    _invocation_matcher = parse_macro_matcher(
        '@![$name:name $( ($($parameters:tt)*) )?] $^'
    )

    _block_matcher = parse_macro_matcher(
        # token sequence terminated by newline, indented block, or EOF
        '$($[!$^] $[!$> $($_:tt)* $<] $line:tt)* $[($^)|($> $($_:tt)* $<)|($[!$_:tt])]'
    )

    _parameters_transcriber = parse_macro_transcriber('$($($parameters)*)*')

    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence."""
        tokens = SliceView(tokens)

        invocations: list[tuple[str, Sequence[Token]]] = []
        invocations_size = 0
        while True:
            match self._invocation_matcher.match(tokens):
                case MacroMatch(
                    size=match_size,
                    captures={'name': Token(string=name)} as captures,
                ):
                    parameters = tuple(
                        self._parameters_transcriber.transcribe(captures)
                    )

                    invocations.append((name, parameters))

                    invocations_size += match_size
                    tokens = tokens[match_size:]
                case _:
                    break

        if not invocations:
            return (), 0

        block_match = self._block_matcher.match(tokens)
        if block_match is None:
            name, parameters = invocations[-1]
            raise DecoratorMacroError(name, parameters, 'expected block')

        initial_block_size = block_match.size

        tokens = list(tokens[:initial_block_size])

        while invocations:
            name, parameters = invocations.pop()

            block_match = self._block_matcher.match(tokens)
            if block_match is None:
                raise DecoratorMacroError(name, parameters, 'expected block')

            block = tokens[: block_match.size]

            macro = self.macros.get(name)
            if macro is None:
                raise DecoratorMacroError(
                    name, parameters, f'cannot find macro named {name!r}'
                )

            result = macro(parameters, block)
            if result is None:
                raise DecoratorMacroError(
                    name, parameters, "block didn't match expected pattern"
                )
            if len(result) < 1 and invocations:
                next_name, next_parameters = invocations[-1]
                raise DecoratorMacroError(
                    next_name,
                    next_parameters,
                    'expected block, but previous macro '
                    f'{_stringify_invocation(name, parameters)!r} produced empty output.',
                )

            if len(result) > 0 and result[-1].type not in (
                tokenize.NEWLINE,
                tokenize.DEDENT,
            ):
                result = (*result, Token(tokenize.NEWLINE, '\n'))

            tokens[: block_match.size] = result

        return tokens, invocations_size + initial_block_size
