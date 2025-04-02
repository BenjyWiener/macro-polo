"""Module-level macros."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize

from .. import MacroError, Token, stringify
from .._utils import SliceView
from ..match import MacroMatch
from ..parse import parse_macro_matcher, parse_macro_transcriber
from .types import Macro, ParameterizedMacro


def _stringify_invocation(name: str, parameters: Sequence[Token]) -> str:
    return f'![{name}({stringify(parameters)})]'


class ModuleMacroError(MacroError):
    """Errors during invocation of module-level macros."""

    def __init__(self, name: str, parameters: Sequence[Token], msg: str):
        """Create a new ModuleMacroError."""
        super().__init__(f'invoking {_stringify_invocation(name, parameters)!r}: {msg}')


@dataclass(frozen=True, slots=True)
class ModuleMacroInvokerMacro(Macro):
    """A macro that processes module-level macro invocations.

    The syntax for invoking a module-level macro is :samp:`![{name}({parameters})]` or
    :samp:`![{name}]` (equivalent to :samp:`![{name}()]`).

    Module-level macro invocations must come before all other code (with the exception
    of a docstring), and must each appear on their own line.

    When invoked, the registered macro is called with two arguments:

    1. :samp:`{parameters}` (as a token sequence)
    2. the remainder of the module starting from the line immediately following the
        invocation (as a token sequence).

    Macros are defined by :attr:`macros` (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, ParameterizedMacro] = field(default_factory=dict)
    """A mapping of names to module macros.

    When a module macro is invoked, its name is looked up here.

    This mapping may be shared with other macros, such as a
    :class:`~macro_polo.macros.ImporterMacro`.
    """

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
                        raise ModuleMacroError(
                            name, parameters, f'cannot find macro named {name!r}'
                        )

                    result = macro(parameters, tokens[match_size:])
                    if result is None:
                        raise ModuleMacroError(
                            name, parameters, "module didn't match expected pattern"
                        )
                    tokens = result if result is not None else tokens[match_size:]

                    changed = True
                case _:
                    raise MacroError(
                        'processing module-level macros: an unknown error occurred'
                    )

        if changed:
            return (*docstring, *tokens) if docstring else tokens
        return None
