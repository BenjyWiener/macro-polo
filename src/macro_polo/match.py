"""Macro input pattern matching utilities."""

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from functools import cache
import tokenize
from typing import Literal, assert_never

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
type MacroMatcherCapture = (
    Token | TokenTree | list[MacroMatcherCapture] | MacroMatcherEmptyCapture
)


@dataclass(frozen=True, slots=True)
class MacroMatch:
    """Result of a successful macro match."""

    size: int
    captures: Mapping[str, MacroMatcherCapture]


@dataclass(frozen=True, slots=True)
class MacroMatcherEmptyCapture:
    """An empty macro capture.

    Preserves nesting depth information, primarily to enable better transcription error
    messages.
    """

    depth: int

    def __bool__(self) -> Literal[False]:
        return False

    def __iter__(self) -> Iterator[Token]:
        yield from ()


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
    NULL = 'null'


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
        match self.type:
            case MacroMatcherVarType.NULL:
                return MacroMatch(
                    size=0,
                    captures={self.name: TokenTree()} if self.name != '_' else {},
                )
            case _ if len(tokens) < 1:
                return None
            case MacroMatcherVarType.TOKEN_TREE:
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
                    captures=(
                        {self.name: TokenTree(*matched_tokens)}
                        if self.name != '_'
                        else {}
                    ),
                )
            case _ if Delimiter.from_token(tokens[0]):
                # Delimiters can only be matched by TOKEN_TREE
                return None
            case MacroMatcherVarType.TOKEN:
                return MacroMatch(
                    size=1,
                    captures={self.name: tokens[0]} if self.name != '_' else {},
                )
            case (
                MacroMatcherVarType.NAME
                | MacroMatcherVarType.OP
                | MacroMatcherVarType.NUMBER
                | MacroMatcherVarType.STRING
            ):
                token = tokens[0]
                if token.type != MacroMatcherVar._token_types[self.type]:
                    return None
                return MacroMatch(
                    size=1, captures={self.name: token} if self.name != '_' else {}
                )
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
    def base_captures(self) -> Mapping[str, MacroMatcherEmptyCapture]:
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
            match_sep = not first and self.sep

            if match_sep:
                if len(tokens) < 1 or tokens[0] != self.sep:
                    break

            match = self.matcher.match(tokens[1:] if match_sep else tokens)

            if match is None:
                if first and self.mode is MacroMatcherRepeaterMode.ONE_OR_MORE:
                    return None
                break

            # Only pop sep if self.matcher matches, to prevent consuming trailing
            # separators.
            if match_sep:
                tokens.popleft()

            tokens = tokens[match.size :]

            for name, capture in match.captures.items():
                captures.setdefault(name, []).append(capture)

            if self.mode is MacroMatcherRepeaterMode.ZERO_OR_ONE:
                break

            first = False

        if not captures:
            return MacroMatch(
                size=start_size - len(tokens), captures=self.base_captures
            )

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
) -> dict[str, MacroMatcherEmptyCapture]:
    """Get a set of empty captures for the given pattern.

    The return value is the expected result of matching against this pattern, wrapped in
    a zero-or-one repeater, with zero matches.
    In other words, a dict containing an empty list for each capture variable, at the
    appropriate nesting level.
    """
    captures: dict[str, MacroMatcherEmptyCapture] = {}

    for item in matcher:
        match item:
            case Token() | MacroMatcherNegativeLookahead():
                pass
            case DelimitedMacroMatcher():
                captures.update(_base_captures_from_matcher(item.matcher))
            case MacroMatcherVar():
                captures[item.name] = MacroMatcherEmptyCapture(0)
            case MacroMatcherRepeater():
                for name, base_capture in item.base_captures.items():
                    captures[name] = MacroMatcherEmptyCapture(base_capture.depth + 1)
            case MacroMatcherUnion():
                captures.update(_base_captures_from_matcher(item[0]))
            case _:
                assert_never(item)

    return captures
