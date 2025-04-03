"""High-level macro utilities."""

from .decorator import DecoratorMacroError, DecoratorMacroInvokerMacro
from .function import FunctionMacroInvokerMacro
from .importer import ImporterMacro
from .macro_rules import MacroRule, MacroRules, MacroRulesParserMacro
from .module import ModuleMacroError, ModuleMacroInvokerMacro
from .super import LoopingMacro, MultiMacro, ScanningMacro
from .types import Macro, ParameterizedMacro, PartialMatchMacro


__all__ = [
    # types
    'Macro',
    'ParameterizedMacro',
    'PartialMatchMacro',
    # super
    'LoopingMacro',
    'MultiMacro',
    'ScanningMacro',
    # importer
    'ImporterMacro',
    # function
    'FunctionMacroInvokerMacro',
    # macro_rules
    'MacroRule',
    'MacroRules',
    'MacroRulesParserMacro',
    # module
    'ModuleMacroError',
    'ModuleMacroInvokerMacro',
    # decorator
    'DecoratorMacroError',
    'DecoratorMacroInvokerMacro',
]
