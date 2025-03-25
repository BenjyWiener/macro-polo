"""Predefined macros."""

from collections.abc import Sequence
import tokenize

from .. import Token, stringify
from . import (
    LoopingMacro,
    Macro,
    MacroRulesParserMacro,
    NamedMacroInvokerMacro,
    ScanningMacro,
)


def stringify_macro(tokens: Sequence[Token]) -> Sequence[Token] | None:
    """Render tokens to a string of source code."""
    return (Token(tokenize.STRING, repr(stringify(tokens))),)


DEFAULT_NAMED_MACROS = {
    'stringify': stringify_macro,
}


def make_default_preprocessor_macro() -> Macro:
    """Create a basic preprocessor macro.

    The returned macro has `macro_rules!` support, as well as some predefined named
    macros.
    """
    named_macros = DEFAULT_NAMED_MACROS.copy()
    return LoopingMacro(
        ScanningMacro(
            MacroRulesParserMacro(named_macros),
            NamedMacroInvokerMacro(named_macros),
        )
    )
