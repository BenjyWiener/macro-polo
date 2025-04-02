"""Declarative ``macro_rules`` macros."""

from collections.abc import Sequence
from dataclasses import dataclass, field

from .. import MacroError, Token, TupleNewType
from ..match import MacroMatch, MacroMatcher
from ..parse import parse_macro_matcher, parse_macro_transcriber
from ..transcribe import MacroTranscriber
from .types import Macro, PartialMatchMacro


@dataclass(frozen=True, slots=True)
class MacroRule:
    """A macro matcher/macro transcriber pair."""

    matcher: MacroMatcher
    """The rule's matcher"""

    transcriber: MacroTranscriber
    """The rule's transcriber"""


class MacroRules(TupleNewType[MacroRule], Macro):
    r"""A sequence of ``MacroRule``\ s.

    :type args: MacroRule
    """

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence."""
        for rule in self:
            if match := rule.matcher.full_match(tokens):
                return tuple(rule.transcriber.transcribe(match.captures))
        return None


@dataclass(frozen=True, slots=True)
class MacroRulesParserMacro(PartialMatchMacro):
    """A macro that parses ``macro_rules`` macro definitions.

    Parsed macros are added to :attr:`macros`.
    """

    macros: dict[str, Macro] = field(default_factory=dict)
    """Parsed ``macro_rules`` macros will be added to this dict.

    It may be shared with other macros, such as a
    :class:`~macro_polo.macros.FunctionMacroInvokerMacro`.
    """

    _macro_rules_declaration_matcher = parse_macro_matcher(
        'macro_rules! $name:name: $> $($rules:tt)+ $<'
    )

    _macro_rules_rules_matcher = parse_macro_matcher(
        '$('
        ' [$($matcher:tt)*]: $['
        '   ($> $($transcriber:tt)* $<)'
        '  |($($[!$^] $transcriber:tt)* $($^)?)'
        ' ]'
        ')+'
    )

    _raw_rules_transcriber = parse_macro_transcriber('$($rules)*')
    _raw_matcher_transcriber = parse_macro_transcriber('$($matcher)*')
    _raw_transcriber_transcriber = parse_macro_transcriber('$($transcriber)*')

    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence."""
        match self._macro_rules_declaration_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name)} as captures,
            ):
                rules_tokens = tuple(self._raw_rules_transcriber.transcribe(captures))

                if name in self.macros:
                    raise MacroError(f'redeclaration of macro {name}')

                match self._macro_rules_rules_matcher.full_match(rules_tokens):
                    case MacroMatch(
                        captures={
                            'matcher': list(matcher_captures),
                            'transcriber': list(transcriber_captures),
                        }
                    ):
                        pass
                    case _:
                        raise MacroError(
                            f'syntax error in macro_rules declaration for {name!r}'
                        )

                matchers = (
                    parse_macro_matcher(
                        self._raw_matcher_transcriber.transcribe({'matcher': matcher})
                    )
                    for matcher in matcher_captures
                )

                transcribers = (
                    parse_macro_transcriber(
                        self._raw_transcriber_transcriber.transcribe(
                            {'transcriber': transcriber}
                        )
                    )
                    for transcriber in transcriber_captures
                )

                self.macros[name] = MacroRules(
                    *(
                        MacroRule(
                            matcher,
                            transcriber,
                        )
                        for matcher, transcriber in zip(matchers, transcribers)
                    )
                )

                return (), match_size

        return (), 0
