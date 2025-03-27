"""Macro importing utilities."""

from collections.abc import Sequence
from dataclasses import dataclass, field
import importlib.util

from .. import MacroError, Token, lex, stringify
from ..parse import parse_macro_matcher
from .macro_rules import MacroRulesParserMacro
from .module import ModuleMacroInvokerMacro
from .super import MultiMacro, ScanningMacro
from .types import Macro, ParameterizedMacro


@dataclass(frozen=True, slots=True)
class ImporterMacro(ParameterizedMacro):
    """Imports macros from other modules.

    Imported macros are added to the `function_macros` dict.
    """

    function_macros: dict[str, Macro] = field(default_factory=dict)

    _parameters_matcher = parse_macro_matcher('$($_:name).+')

    def _scrape_macros(self, module_path: str) -> None:
        module_spec = importlib.util.find_spec(module_path)
        if module_spec is None:
            raise ModuleNotFoundError(f'No module named {module_path!r}')
        if module_spec.origin is None:
            raise MacroError(
                f'error importing {module_path}: module spec has no origin'
            )

        with open(module_spec.origin, 'r') as source_file:
            tokens = tuple(lex(source_file.read()))

        scraper_macro = MultiMacro(
            ModuleMacroInvokerMacro({'import': self}),
            ScanningMacro(
                MacroRulesParserMacro(self.function_macros),
            ),
        )

        scraper_macro(tokens)

    def __call__(
        self, parameters: Sequence[Token], tokens: Sequence[Token]
    ) -> Sequence[Token] | None:
        """Import macros from the given module.

        `parameters` should be a valid module path (a dot-separated list of names).
        """
        if not self._parameters_matcher.match(parameters):
            raise MacroError(
                f'import: expected module path, got {stringify(parameters)}'
            )

        module_path = stringify(parameters).replace(' ', '')

        self._scrape_macros(module_path)

        return None
