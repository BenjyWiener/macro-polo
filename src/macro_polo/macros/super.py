"""Super-macros that apply other macros to their input."""

from collections.abc import Sequence

from .. import Token, TokenTree
from .._utils import SliceView, TupleNewType
from ..match import MacroMatch
from ..parse import parse_macro_matcher
from .types import Macro, PartialMatchMacro


class MultiMacro(TupleNewType[Macro], Macro):
    """A super-macro that applies each of its inner macros in sequence.

    :type args: Macro
    """

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        Applies each macro in ``self`` in sequence.
        """
        changed = False

        for macro in self:
            if (new_tokens := macro(tokens)) is not None:
                tokens = new_tokens
                changed = True

        if changed:
            return tokens
        return None


class LoopingMacro(TupleNewType[Macro], Macro):
    """A super-macro that repeatedely applies its inner macros until none match.

    :type args: Macro
    """

    def __call__(self, tokens: Sequence[Token]) -> Sequence[Token] | None:
        """Transform a token sequence.

        Tries each macro in sequence, starting over after each match.
        Stops once none of the macros match.
        """
        changed = False

        while True:
            for macro in self:
                if (new_tokens := macro(tokens)) is not None:
                    tokens = new_tokens
                    changed = True
                    break
            else:
                break

        if changed:
            return tokens
        return None


class ScanningMacro(TupleNewType[PartialMatchMacro], Macro):
    """A super-macro that scans input and applies its inner macros as they match.

    This macro will only perform a single pass on the input. It can be combined with
    :class:`LoopingMacro` to recursively expand macros.

    :type args: PartialMatchMacro
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
