"""Custom codec to format source code with Ruff."""

import codecs
from collections.abc import Buffer
from functools import partial
import sys
import traceback


ENCODING_NAME = 'pretty'


def _decode(data: Buffer, errors: str = 'strict', *, encoding: str) -> tuple[str, int]:
    try:
        import subprocess

        decoder = codecs.getdecoder(encoding)
        source, consumed = decoder(data, errors)

        formatted = '\n' + subprocess.check_output(
            ['ruff', 'format', '-'],
            input=source,
            encoding=sys.getdefaultencoding(),
        )

        return formatted, consumed
    except:
        traceback.print_exc()
        raise


class _IncrementalPrettyDecoder(codecs.BufferedIncrementalDecoder):
    def __init__(self, errors: str = 'strict', *, encoding: str):
        super().__init__(errors)
        self._encoding = encoding

    def _buffer_decode(
        self, input: Buffer, errors: str, final: bool
    ) -> tuple[str, int]:
        if not final:
            return '', 0

        return _decode(input, errors, encoding=self._encoding)


def _search_hook(encoding: str):
    if encoding.startswith(ENCODING_NAME):
        real_encoding = (
            encoding.removeprefix(ENCODING_NAME).lstrip('_') or sys.getdefaultencoding()
        )

        return codecs.CodecInfo(
            encode=codecs.getencoder(real_encoding),
            decode=partial(_decode, encoding=real_encoding),
            incrementaldecoder=partial(
                _IncrementalPrettyDecoder, encoding=real_encoding
            ),
            name=encoding,
        )

    return None


def register() -> None:
    """Register the pretty codec."""
    codecs.register(_search_hook)
