"""Custom codec to enable automatic preprocessing."""

import codecs
from collections.abc import Buffer
from functools import partial
import sys
import traceback


ENCODING_NAME = 'macro_polo'


def _decode(data: Buffer, errors: str = 'strict', *, encoding: str) -> tuple[str, int]:
    try:
        from . import lex, stringify
        from .macros.predefined import make_default_preprocessor_macro

        macro = make_default_preprocessor_macro()

        decoder = codecs.getdecoder(encoding)
        source, consumed = decoder(data, errors)

        tokens = tuple(lex(source))

        result = stringify(macro(tokens) or tokens)
        if result:
            # First line will be stripped, since it's assumed to be the 'coding: ...'
            # directive.
            result = '\n' + result
        return result, consumed
    except:
        traceback.print_exc()
        raise


class _IncrementalMacroDecoder(codecs.BufferedIncrementalDecoder):
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
                _IncrementalMacroDecoder, encoding=real_encoding
            ),
            name=encoding,
        )

    return None


def register() -> None:
    """Register the macro_polo codec."""
    codecs.register(_search_hook)
