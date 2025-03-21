"""Macro input pattern matching utilities."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from functools import cache
import tokenize
from typing import assert_never

from . import Delimiter, MacroError, Token, TokenTree
from ._utils import SliceView, TupleNewType


class MacroMatchError(MacroError):
    """Exception raised for macro matching errors."""


type MacroMatcherItem = (
    Token
    | DelimitedMacroMatcher
    | MacroMatcherVar
    | MacroMatcherRepeater
    | MacroMatcherUnion
    | MacroMatcherNegativeLookahead
)
type MacroMatcherCapture = Token | TokenTree | list[MacroMatcherCapture]


@dataclass(frozen=True, slots=True)
class MacroMatch:
    """Result of a successful macro match."""

    size: int
    captures: Mapping[str, MacroMatcherCapture]


class MacroMatcher(TupleNewType[MacroMatcherItem]):
    """A macro match pattern."""

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        start_size = len(tokens)
        tokens = SliceView(tokens)

        captures: dict[str, MacroMatcherCapture] = {}

        for item in self:
            if isinstance(item, Token):
                if Delimiter.from_token(item):
                    raise ValueError(
                        'delimiter tokens cannot be matched directly, '
                        'use DelimitedMacroMatcher instead'
                    )
                if len(tokens) < 1 or tokens.popleft() != item:
                    return None
            else:
                match = item.match(tokens)
                if match is None:
                    return None

                tokens = tokens[match.size :]
                captures |= match.captures

        return MacroMatch(size=start_size - len(tokens), captures=captures)

    def full_match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against an entire token sequence."""
        if (match := self.match(tokens)) and match.size == len(tokens):
            return match

        return None


@dataclass(frozen=True, slots=True)
class DelimitedMacroMatcher:
    """A delimited macro match pattern."""

    delimiter: Delimiter
    matcher: MacroMatcher

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        if len(tokens) < 2 or not self.delimiter.matches_open(tokens[0]):
            return None

        tokens = SliceView(tokens)

        # Skip opening delimiter
        tokens.popleft()

        # Find closing delimiter
        depth = 0

        for i, token in enumerate(tokens):
            if self.delimiter.matches_open(token):
                depth += 1
            elif self.delimiter.matches_close(token):
                if depth == 0:
                    break
                depth -= 1
        else:
            # No closing delimiter
            return None

        if inner_match := self.matcher.full_match(tokens[:i]):
            return MacroMatch(size=inner_match.size + 2, captures=inner_match.captures)

        return None


class MacroMatcherVarType(Enum):
    """Capture-variable type."""

    TOKEN = 'token'
    NAME = 'name'
    OP = 'op'
    NUMBER = 'number'
    STRING = 'string'
    TOKEN_TREE = 'tt'
    EMPTY = 'empty'


@dataclass(frozen=True, slots=True)
class MacroMatcherVar:
    """A capture-variable in a macro matcher."""

    name: str
    type: MacroMatcherVarType

    _token_types = {
        MacroMatcherVarType.NAME: tokenize.NAME,
        MacroMatcherVarType.OP: tokenize.OP,
        MacroMatcherVarType.NUMBER: tokenize.NUMBER,
        MacroMatcherVarType.STRING: tokenize.STRING,
    }

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        if len(tokens) < 1:
            return None

        match self.type:
            case MacroMatcherVarType.TOKEN_TREE:
                if len(tokens) < 1:
                    return None

                tokens = SliceView(tokens)

                first_token = tokens.popleft()
                matched_tokens: list[Token] = [first_token]

                if delimiter := Delimiter.from_token(first_token):
                    depth = 0

                    # Match until end delimiter is found
                    while token := tokens.popleft():
                        matched_tokens.append(token)

                        if delimiter.matches_open(token):
                            depth += 1
                        elif delimiter.matches_close(token):
                            if depth == 0:
                                break
                            depth -= 1

                return MacroMatch(
                    size=len(matched_tokens),
                    captures={self.name: TokenTree(*matched_tokens)},
                )
            case _ if Delimiter.from_token(tokens[0]):
                # Delimiters can only be matched by TOKEN_TREE
                return None
            case MacroMatcherVarType.TOKEN:
                return MacroMatch(size=1, captures={self.name: tokens[0]})
            case (
                MacroMatcherVarType.NAME
                | MacroMatcherVarType.OP
                | MacroMatcherVarType.NUMBER
                | MacroMatcherVarType.STRING
            ):
                token = tokens[0]
                if token.type != MacroMatcherVar._token_types[self.type]:
                    return None
                return MacroMatch(size=1, captures={self.name: token})
            case MacroMatcherVarType.EMPTY:
                return MacroMatch(size=0, captures={self.name: TokenTree()})
            case _:
                assert_never(self.type)


class MacroMatcherRepeaterMode(Enum):
    """Matcher repeat mode."""

    ZERO_OR_ONE = '?'
    ZERO_OR_MORE = '*'
    ONE_OR_MORE = '+'


@dataclass(frozen=True, slots=True)
class MacroMatcherRepeater:
    """A repeated sub-matcher."""

    matcher: MacroMatcher
    mode: MacroMatcherRepeaterMode
    sep: Token | None = None

    @property
    def base_captures(self) -> Mapping[str, MacroMatcherCapture]:
        """Get a set of empty captures for this matcher.

        This is used to provide empty capture lists for matchers that match zero
        times, allowing transcribers to handle empty captures properly.
        """
        return _base_captures_from_matcher(self.matcher)

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        start_size = len(tokens)
        tokens = SliceView(tokens)

        captures: dict[str, list[MacroMatcherCapture]] = {}

        first = True
        while True:
            if not first:
                if self.sep:
                    if len(tokens) >= 1 and tokens[0] == self.sep:
                        tokens.popleft()
                    else:
                        break

            match = self.matcher.match(tokens)

            if match is None:
                if first and self.mode is MacroMatcherRepeaterMode.ONE_OR_MORE:
                    return None
                break

            tokens = tokens[match.size :]

            for name, capture in match.captures.items():
                captures.setdefault(name, []).append(capture)

            if self.mode is MacroMatcherRepeaterMode.ZERO_OR_ONE:
                break

            first = False

        if not captures:
            return MacroMatch(size=0, captures=self.base_captures)

        return MacroMatch(size=start_size - len(tokens), captures=captures)


class MacroMatcherUnion(TupleNewType[MacroMatcher]):
    """A union of macro matchers.

    The first sub-matcher to match is used.
    """

    def __new__(cls, *args):
        """Create a new `MacroMatcherUnion`."""
        self = super().__new__(cls, *args)

        if len(args) < 1:
            raise MacroError('Union must have at least one variant.')

        captures = _base_captures_from_matcher(self[0])
        for matcher in self:
            if _base_captures_from_matcher(matcher) != captures:
                raise MacroError(
                    'All union variants must have identical capture variables at '
                    'equiavelent nesting depths.'
                )

        return self

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        for matcher in self:
            if match := matcher.match(tokens):
                return match
        return None


class MacroMatcherNegativeLookahead(TupleNewType[MacroMatcherItem]):
    """A negative lookahead macro match.

    Matches zero tokens if `MacroMatcher` would fail to match, and fails to match if
    `MacroMatcher` would successfully match.
    """

    @property
    @cache
    def _matcher(self) -> MacroMatcher:
        return MacroMatcher(*self)

    def match(self, tokens: Sequence[Token]) -> MacroMatch | None:
        """Attempt to match against a token sequence."""
        if self._matcher.match(tokens):
            return None
        return MacroMatch(size=0, captures={})


@cache
def _base_captures_from_matcher(
    matcher: MacroMatcher,
) -> dict[str, MacroMatcherCapture]:
    """Get a set of empty captures for the given pattern.

    The return value is the expected result of matching against this pattern, wrapped in
    a zero-or-one repeater, with zero matches.
    In other words, a dict containing an empty list for each capture variable, at the
    appropriate nesting level.
    """
    captures: dict[str, MacroMatcherCapture] = {}

    for item in matcher:
        match item:
            case Token() | MacroMatcherNegativeLookahead():
                pass
            case DelimitedMacroMatcher():
                captures.update(_base_captures_from_matcher(item.matcher))
            case MacroMatcherVar():
                captures[item.name] = []
            case MacroMatcherRepeater():
                for name, base_capture in item.base_captures.items():
                    captures[name] = [base_capture]
            case MacroMatcherUnion():
                captures.update(_base_captures_from_matcher(item[0]))
            case _:
                assert_never(item)

    return captures
