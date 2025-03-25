"""High-level macro utilities."""

from abc import abstractmethod
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
import tokenize
from typing import Protocol, cast

from .. import MacroError, Token, TokenTree
from .._utils import SliceView, TupleNewType
from ..match import MacroMatch, MacroMatcher
from ..parse import parse_macro_matcher, parse_macro_transcriber
from ..transcribe import MacroTranscriber


class MacroInvocationError(MacroError):
    """Base class for errors that arrise when invoking a macro."""


class Macro(Protocol):
    """Transforms a token sequence."""

    @abstractmethod
    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        This method should return a new token sequence, or `None` if the input sequence
        fails to match.
        """


class PartialMatchMacro(Protocol):
    """Transforms the beginning of a token sequence."""

    @abstractmethod
    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence.

        This method should return a tuple of (token sequence, number of tokens matched).
        """


class LoopingMacro(TupleNewType[Macro], Macro):
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


class ScanningMacro(TupleNewType[PartialMatchMacro], Macro):
    """A meta-macro that scans input and applies its inner macros as they match.

    This macro will only perform a single pass on the input. It can be combined with
    `LoopingMacro` to recursively expand macros.
    """

    _token_tree_matcher = parse_macro_matcher('$token_tree:tt')

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence."""
        tokens = SliceView(tokens)

        output: list[Token] = []
        changed = False

        while len(tokens) > 0:
            for macro in self:
                new_tokens, match_size = macro(tokens)
                if len(new_tokens) > 0 or match_size > 0:
                    output.extend(new_tokens)
                    tokens = tokens[match_size:]
                    changed = True
                    break
            else:
                match self._token_tree_matcher.match(tokens):
                    case MacroMatch(size=1):
                        output.append(tokens.popleft())
                    case MacroMatch(
                        size=match_size,
                        captures={
                            'token_tree': TokenTree(
                                (open_delim, *inner_tokens, close_delim)
                            )
                        },
                    ):
                        output.append(open_delim)
                        if (transformed_inner := self(inner_tokens)) is not None:
                            output.extend(transformed_inner)
                            changed = True
                        else:
                            output.extend(inner_tokens)
                        output.append(close_delim)
                        tokens = tokens[match_size:]

        if changed:
            return output
        return None


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
class MacroRulesParserMacro(PartialMatchMacro):
    """A macro that parses `macro_rules!` macro definitions.

    Parsed macros are added to the `macros` dict.
    """

    macros: dict[str, Macro] = field(default_factory=dict)

    _macro_rules_declaration_matcher = parse_macro_matcher(
        'macro_rules! $name:name: $> $($rules:tt)+ $<'
    )

    _macro_rules_rules_matcher = parse_macro_matcher(
        '$('
        ' [$($matcher:tt)*]: $['
        '    ($> $($transcriber:tt)* $<)'
        '   |($($[!$^] $transcriber:tt)* $($^)?)'
        ' ]'
        ')+'
    )

    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence."""
        match self._macro_rules_declaration_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name), 'rules': rules_capture},
            ):
                rules_tokens = sum(cast(list[TokenTree], rules_capture), ())

                if name in self.macros:
                    raise MacroError(f'redeclaration of macro {name}')

                match self._macro_rules_rules_matcher.full_match(rules_tokens):
                    case MacroMatch(
                        captures={'matcher': matchers, 'transcriber': transcribers}
                    ):
                        pass
                    case _:
                        raise MacroError(
                            f'syntax error in macro_rules declaration for {name}'
                        )

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

                return (), match_size

        return (), 0


@dataclass(frozen=True, slots=True)
class NamedMacroInvokerMacro(PartialMatchMacro):
    """A macro that processes named macro invocations.

    Macros are defined by the `macros` dict (which can be updated after this class is
    instantiated).
    """

    macros: Mapping[str, Macro] = field(default_factory=dict)

    _function_style_macro_invocation_matcher = parse_macro_matcher(
        '$name:name!$[(($($body:tt)*)) | ([$($body:tt)*]) | ({$($body:tt)*})]'
    )

    _block_style_macro_invocation_matcher = parse_macro_matcher(
        '$name:name!: $> $($body:tt)* $<'
    )

    def _invoke_macro(self, name: str, body: Sequence[Token]) -> Sequence[Token]:
        """Invoke a macro."""
        macro = self.macros.get(name)
        if macro is None:
            raise MacroInvocationError(f'cannot find macro named {name}')

        result = macro(body)
        if result is None:
            raise MacroError(
                f"invoking macro {name}: body didn't match expected pattern"
            )
        return result

    def __call__(self, tokens: Sequence[Token]) -> tuple[Sequence[Token], int]:
        """Transform the beginning of a token sequence."""
        match self._function_style_macro_invocation_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name), 'body': body_capture},
            ):
                result = self._invoke_macro(
                    name, sum(cast(list[TokenTree], body_capture), ())
                )

                return result, match_size

        match self._block_style_macro_invocation_matcher.match(tokens):
            case MacroMatch(
                size=match_size,
                captures={'name': Token(string=name), 'body': body_capture},
            ):
                result = self._invoke_macro(
                    name, sum(cast(list[TokenTree], body_capture), ())
                )

                return (*result, Token(tokenize.NEWLINE, '\n')), match_size

        return (), 0
