"""Utilities for defining and exporting procedural macros."""

from collections.abc import Sequence
from functools import partial
import tokenize

from .. import MacroError, Token, lex, stringify
from ..match import MacroMatch
from ..parse import parse_macro_matcher


EXPORTED_MACROS_NAME_TEMPLATE = '__macro_polo_exported_{}_macros__'
EXPORTED_FUNCTION_MACROS_NAME = EXPORTED_MACROS_NAME_TEMPLATE.format('function')
EXPORTED_MODULE_MACROS_NAME = EXPORTED_MACROS_NAME_TEMPLATE.format('module')
EXPORTED_DECORATOR_MACROS_NAME = EXPORTED_MACROS_NAME_TEMPLATE.format('decorator')


_CLASS_OR_FUNC_MATCHER = parse_macro_matcher('$[(class)|(def)] $name:name')


def export_proc_macro(
    parameters: Sequence[Token], tokens: Sequence[Token], export_dict_name: str
) -> Sequence[Token] | None:
    """Decorator-style macro for exporting procedural macros."""
    match parameters:
        case []:
            export_name = None
        case [Token(type=tokenize.STRING, string=export_name)]:
            pass
        case _:
            raise MacroError(
                'export function-style macro: expected name as parameter, '
                f'got {stringify(parameters)!r}'
            )

    match _CLASS_OR_FUNC_MATCHER.match(tokens):
        case MacroMatch(captures={'name': Token(string=name)}):
            pass
        case _:
            first_line = stringify(tokens).splitlines()[0]
            raise MacroError(
                'export function-style macro: expected class or function definition, '
                f'found {first_line!r}'
            )

    if export_name is None:
        export_name = name

    export_tokens = lex(
        f'globals().setdefault({export_dict_name!r}, {{}}).update({export_name}={name})'
    )

    return (*tokens, *export_tokens)


export_function_proc_macro = partial(
    export_proc_macro, export_dict_name=EXPORTED_FUNCTION_MACROS_NAME
)
export_module_proc_macro = partial(
    export_proc_macro, export_dict_name=EXPORTED_MODULE_MACROS_NAME
)
export_decorator_proc_macro = partial(
    export_proc_macro, export_dict_name=EXPORTED_DECORATOR_MACROS_NAME
)
