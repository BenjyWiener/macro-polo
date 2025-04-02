"""Predefined macros."""

from collections.abc import Sequence
import sys
import tokenize

from .. import Token, stringify
from . import (
    DecoratorMacroInvokerMacro,
    FunctionMacroInvokerMacro,
    ImporterMacro,
    LoopingMacro,
    Macro,
    MacroRulesParserMacro,
    ModuleMacroInvokerMacro,
    MultiMacro,
    ParameterizedMacro,
    ScanningMacro,
)
from .proc import (
    export_decorator_proc_macro,
    export_function_proc_macro,
    export_module_proc_macro,
)


def stringify_macro(tokens: Sequence[Token]) -> Sequence[Token] | None:
    """Render tokens to a string of source code."""
    if len(tokens) == 1:
        # Special case for single tokens, avoids extraneous white space
        return (Token(tokenize.STRING, repr(tokens[0].string)),)

    return (Token(tokenize.STRING, repr(stringify(tokens))),)


def debug_macro(tokens: Sequence[Token]) -> Sequence[Token] | None:
    """Stringify and print `tokens` to stderr during macro expansion."""
    print(stringify(tokens), file=sys.stderr)
    return ()


DEFAULT_FUNCTION_MACROS = {
    'stringify': stringify_macro,
    'debug': debug_macro,
}


def make_default_preprocessor_macro() -> Macro:
    """Create a basic preprocessor macro.

    The returned macro has ``macro_rules`` support, as well as some predefined named
    macros.
    """
    function_macros = DEFAULT_FUNCTION_MACROS.copy()
    module_macros: dict[str, ParameterizedMacro] = {}
    decorator_macros: dict[str, ParameterizedMacro] = {
        'function_macro': export_function_proc_macro,
        'module_macro': export_module_proc_macro,
        'decorator_macro': export_decorator_proc_macro,
    }

    module_macros['import'] = ImporterMacro(
        function_macros,
        module_macros,
        decorator_macros,
    )

    return MultiMacro(
        ModuleMacroInvokerMacro(module_macros),
        LoopingMacro(
            ScanningMacro(
                DecoratorMacroInvokerMacro(decorator_macros),
                MacroRulesParserMacro(function_macros),
                FunctionMacroInvokerMacro(function_macros),
            )
        ),
    )
