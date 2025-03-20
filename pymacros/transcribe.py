"""Macro transcription utilities."""

from collections.abc import Iterator
from dataclasses import dataclass

from . import MacroError, Token, TokenTree
from ._utils import TupleNewType
from .match import MacroMatch


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
            if isinstance(item, MacroTransciberSubstitution):
                try:
                    capture = match.captures[item.name]
                except KeyError:
                    raise MacroTranscriptionError(
                        f'no macro variable named {item.name!r}'
                    ) from None

                for index in repitition_path:
                    if not isinstance(capture, list):
                        break
                    capture = capture[index]

                if isinstance(capture, list):
                    raise MacroTranscriptionError(
                        f'macro variable {item.name!r} still repeating at this depth'
                    )

                if isinstance(capture, Token):
                    yield capture
                elif isinstance(capture, TokenTree):
                    yield from capture
            if isinstance(item, MacroTranscriberRepeater):
                yield from item.transcribe(match, repitition_path)


@dataclass(frozen=True, slots=True)
class MacroTranscriberRepeater:
    """A repeated sub-transcriber."""

    transcriber: MacroTranscriber
    sep: Token | None = None

    def _calc_repititions(
        self,
        match: MacroMatch,
        repitition_path: tuple[int, ...],
    ) -> int:
        for item in self.transcriber:
            if isinstance(item, MacroTransciberSubstitution):
                try:
                    capture = match.captures[item.name]
                except KeyError:
                    raise MacroTranscriptionError(
                        f'no macro variable named {item.name!r}'
                    ) from None

                for index in repitition_path:
                    if not isinstance(capture, list):
                        break
                    capture = capture[index]
                else:
                    if isinstance(capture, list):
                        return len(capture)

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
