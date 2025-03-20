"""High-level macro utilities."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol, cast

from pymacros.parse._transcribers import parse_macro_transcriber

from . import MacroError, Token, TokenTree
from ._utils import SliceView, TupleNewType
from .match import MacroMatch, MacroMatcher
from .parse import parse_macro_matcher
from .transcribe import MacroTranscriber


class MacroInvocationError(MacroError):
    """Base class for errors that arrise when invoking a macro."""


class Macro(Protocol):
    """Transforms a token sequence."""

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        This method should return a new token sequence, or `None` if the input sequence
        fails to match.
        """


@dataclass(frozen=True, slots=True)
class MacroRule:
    """A macro matcher/macro transcriber pair."""

    matcher: MacroMatcher
    transcriber: MacroTranscriber


class MacroRules(TupleNewType[MacroRule], Macro):
    """A sequence of `MacroRule`s."""

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence."""
        for rule in self:
            if match := rule.matcher.full_match(tokens):
                return tuple(rule.transcriber.transcribe(match))
        return None


@dataclass(frozen=True, slots=True)
class MacroRulesMacro(Macro):
    """A macro that processes `MacroRules` definitions and invocations.

    Additional predefined macros can be added by passing or populating `macros`.
    """

    macros: dict[str, Macro] = field(default_factory=dict)

    _macro_invocation_matchers = (
        parse_macro_matcher('$name:name!($($body:tt)*)'),
        parse_macro_matcher('$name:name![$($body:tt)*]'),
        parse_macro_matcher('$name:name!{$($body:tt)*}'),
        parse_macro_matcher('$name:name!: $> $($body:tt)* $<'),
    )

    _macro_rules_matcher = parse_macro_matcher(
        'macro_rules! $name:name:'
        ' $> $( [$($matcher:tt)*]: $> $($transcriber:tt)* $< )+ $<'
    )

    def _try_match_macro_invocation(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Try to match a macro invocation."""
        for matcher in MacroRulesMacro._macro_invocation_matchers:
            if match := matcher.match(tokens):
                return match
        return None

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence."""
        tokens = SliceView(tokens)

        output: list[Token] = []
        changed = False

        while len(tokens) > 0:
            match self._try_match_macro_invocation(tokens):
                case MacroMatch(
                    size=match_size,
                    captures={'name': Token(string=name), 'body': body_capture},
                ):
                    macro = self.macros.get(name)
                    if macro is None:
                        raise MacroInvocationError(f'cannot find macro named {name}')

                    body = sum(cast(list[TokenTree], body_capture), ())

                    result = macro(body)
                    if result is None:
                        raise MacroError(
                            "macro invocation body didn't match expected pattern"
                        )

                    output.extend(result)
                    tokens = tokens[match_size:]
                    changed = True
                    continue

            match self._macro_rules_matcher.match(tokens):
                case MacroMatch(
                    size=match_size,
                    captures={
                        'name': Token(string=name),
                        'matcher': list(matchers),
                        'transcriber': list(transcribers),
                    },
                ):
                    raw_rules = zip(
                        cast(list[list[TokenTree]], matchers),
                        cast(list[list[TokenTree]], transcribers),
                    )

                    self.macros[name] = MacroRules(
                        *(
                            MacroRule(
                                parse_macro_matcher(sum(raw_matcher, ())),
                                parse_macro_transcriber(sum(raw_transcriber, ())),
                            )
                            for raw_matcher, raw_transcriber in raw_rules
                        )
                    )

                    tokens = tokens[match_size:]
                    changed = True
                    continue

            output.append(tokens.popleft())

        if changed:
            return output
        return None


class SuperMacro(TupleNewType[Macro], Macro):
    """A meta-macro that applies its inner macros until none of them match."""

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        Tries each macro in order, starting over after each match.
        Stops once none of the macros match.
        """
        changed = False

        while True:
            for macro in self:
                if new_tokens := macro(tokens):
                    tokens = new_tokens
                    changed = True
                    break
            else:
                break

        if changed:
            return tokens
        return None
