"""Macro transcription utilities."""

from collections.abc import Iterator
from dataclasses import dataclass

from . import MacroError, Token, TokenTree
from ._utils import TupleNewType
from .match import MacroMatch, MacroMatcherEmptyCapture


class MacroTranscriptionError(MacroError):
    """Exception raised for macro transcription errors."""


type MacroTranscriberItem = (
    Token | MacroTransciberSubstitution | MacroTranscriberRepeater
)


@dataclass(frozen=True, slots=True)
class MacroTransciberSubstitution:
    """A variable substitution in a transcriber."""

    name: str


class MacroTranscriber(TupleNewType[MacroTranscriberItem]):
    """Transcribes a macro match to an output token stream."""

    def transcribe(
        self, match: MacroMatch, repitition_path: tuple[int, ...] = ()
    ) -> Iterator[Token]:
        """Transcribe the given match to an output token stream."""
        for item in self:
            if isinstance(item, Token):
                yield item
            elif isinstance(item, MacroTransciberSubstitution):
                try:
                    capture = match.captures[item.name]
                except KeyError:
                    raise MacroTranscriptionError(
                        f'no macro variable named {item.name!r}'
                    ) from None

                for index in repitition_path:
                    if isinstance(capture, list):
                        capture = capture[index]
                    elif (
                        isinstance(capture, MacroMatcherEmptyCapture)
                        and capture.depth > 0
                    ):
                        capture = MacroMatcherEmptyCapture(depth=capture.depth - 1)
                    else:
                        break

                if isinstance(capture, list) or (
                    isinstance(item, MacroMatcherEmptyCapture) and item.depth > 0
                ):
                    raise MacroTranscriptionError(
                        f'macro variable {item.name!r} still repeating at this depth'
                    )

                if isinstance(capture, Token):
                    yield capture
                elif isinstance(capture, TokenTree):
                    yield from capture
            elif isinstance(item, MacroTranscriberRepeater):
                yield from item.transcribe(match, repitition_path)


@dataclass(frozen=True, slots=True)
class MacroTranscriberRepeater:
    """A repeated sub-transcriber."""

    transcriber: MacroTranscriber
    sep: Token | None = None

    def _substitutions(self) -> Iterator[str]:
        for item in self.transcriber:
            if isinstance(item, MacroTransciberSubstitution):
                yield item.name
            elif isinstance(item, MacroTranscriberRepeater):
                yield from item._substitutions()

    def _calc_repititions(
        self,
        match: MacroMatch,
        repitition_path: tuple[int, ...],
    ) -> int:
        """Calculate how many times to repeat for the given match."""
        for name in self._substitutions():
            try:
                capture = match.captures[name]
            except KeyError:
                raise MacroTranscriptionError(
                    f'no macro variable named {name!r}'
                ) from None

            for index in repitition_path:
                if not isinstance(capture, list):
                    break
                capture = capture[index]
            else:
                if isinstance(capture, list):
                    return len(capture)

            if isinstance(capture, MacroMatcherEmptyCapture):
                return 0

        raise MacroTranscriptionError('no variables repeat at this depth')

    def transcribe(
        self, match: MacroMatch, repitition_path: tuple[int, ...] = ()
    ) -> Iterator[Token]:
        """Transcribe the given match to an output token stream."""
        for i in range(self._calc_repititions(match, repitition_path)):
            if i > 0 and self.sep:
                yield self.sep

            yield from self.transcriber.transcribe(
                match,
                repitition_path + (i,),
            )
