"""Module-level macros."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize

from .. import MacroError, Token
from .._utils import SliceView
from ..match import MacroMatch
from ..parse import parse_macro_matcher, parse_macro_transcriber
from .types import Macro, ParameterizedMacro


@dataclass(frozen=True, slots=True)
class ModuleMacroInvokerMacro(Macro):
    """A macro that processes module-level macro invocations.

    Module-level macros must appear at the top of the module before any other code, with
    the exception of an optional docstring.

    Macros are defined by the `macros` mapping (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, ParameterizedMacro] = field(default_factory=dict)

    _invocation_matcher = parse_macro_matcher(
        '![$name:name $( ($($parameters:tt)*) )?] $^'
    )

    _parameters_transcriber = parse_macro_transcriber('$($($parameters)*)*')

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence."""
        tokens = SliceView(tokens)

        changed = False

        # Ignore docstring + newline
        match tokens[:2]:
            case [Token(type=tokenize.STRING), Token(type=tokenize.NEWLINE)]:
                docstring, tokens = tokens[:2], tokens[2:]
            case _:
                docstring = None

        while match := self._invocation_matcher.match(tokens):
            match match:
                case MacroMatch(
                    size=match_size,
                    captures={'name': Token(string=name)} as captures,
                ):
                    parameters = tuple(
                        self._parameters_transcriber.transcribe(captures)
                    )

                    macro = self.macros.get(name)
                    if macro is None:
                        raise MacroError(
                            'invoking module-level macro: '
                            f'cannot find macro named {name!r}'
                        )

                    tokens = (
                        macro(parameters, tokens[match_size:]) or tokens[match_size:]
                    )

                    changed = True
                case _:
                    raise MacroError(
                        'processing module-level macros: an unknown error occurred'
                    )

        if changed:
            return (*docstring, *tokens) if docstring else tokens
        return None
