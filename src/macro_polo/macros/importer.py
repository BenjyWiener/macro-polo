"""Macro importing utilities."""

from collections.abc import Sequence
from dataclasses import dataclass, field
import importlib.util
from typing import cast

from .. import MacroError, Token, lex, stringify
from ..match import MacroMatch
from ..parse import parse_macro_matcher
from .macro_rules import MacroRulesParserMacro
from .module import ModuleMacroInvokerMacro
from .super import MultiMacro, ScanningMacro
from .types import Macro, ParameterizedMacro


@dataclass(frozen=True, slots=True)
class _ScrapedMacros:
    function_macros: dict[str, Macro] = field(default_factory=dict)


def _scrape_macros(module_path: str) -> _ScrapedMacros:
    module_spec = importlib.util.find_spec(module_path)
    if module_spec is None:
        raise ModuleNotFoundError(f'No module named {module_path!r}')
    if module_spec.origin is None:
        raise MacroError(f'error importing {module_path}: module spec has no origin')

    with open(module_spec.origin, 'r') as source_file:
        tokens = tuple(lex(source_file.read()))

    scraped_macros = _ScrapedMacros()

    import_macro = ImporterMacro(scraped_macros.function_macros)

    scraper_macro = MultiMacro(
        ModuleMacroInvokerMacro({'import': import_macro}),
        ScanningMacro(
            MacroRulesParserMacro(scraped_macros.function_macros),
        ),
    )

    scraper_macro(tokens)

    return scraped_macros


@dataclass(frozen=True, slots=True)
class ImporterMacro(ParameterizedMacro):
    """Imports macros from other modules.

    Imported macros are added to the `function_macros` dict.
    """

    function_macros: dict[str, Macro] = field(default_factory=dict)

    _parameters_matcher = parse_macro_matcher(
        '$($($members:name),+ from)? $($components:name).+'
    )

    def __call__(
        self, parameters: Sequence[Token], tokens: Sequence[Token]
    ) -> Sequence[Token] | None:
        """Import macros from the given module.

        `parameters` should be a valid module path (a dot-separated list of names).
        """
        match self._parameters_matcher.full_match(parameters):
            case MacroMatch(
                captures={
                    'components': [*component_tokens],
                    'members': [[*member_tokens]],
                }
            ):
                members = {token.string for token in cast(list[Token], member_tokens)}
            case MacroMatch(
                captures={
                    'components': [*component_tokens],
                }
            ):
                members = None
            case _:
                raise MacroError(
                    'import: expected module path or list of names and module path, '
                    f'got {stringify(parameters)!r}'
                )

        module_path = '.'.join(
            token.string for token in cast(list[Token], component_tokens)
        )

        scraped_macros = _scrape_macros(module_path)

        if members is not None:
            if missing := next(
                (
                    member
                    for member in members
                    if member not in scraped_macros.function_macros
                ),
                None,
            ):
                raise MacroError(f'import: no macro named {missing!r} in {module_path}')

            self.function_macros.update(
                {
                    name: macro
                    for name, macro in scraped_macros.function_macros.items()
                    if name in members
                }
            )
        else:
            self.function_macros.update(scraped_macros.function_macros)

        return tokens
