"""Expand macros in a source file."""

import argparse
from pathlib import Path
import sys
from typing import cast

from . import lex, stringify
from .macros.predefined import make_default_preprocessor_macro


arg_parser = argparse.ArgumentParser(description='Expand macros in a source file')
arg_parser.add_argument(
    'file',
    type=Path,
    nargs='?',
    default=None,
    help='Path to a Python source file to process (defaults to stdin)',
)

args = arg_parser.parse_args()

source = (
    cast(Path, args.file).read_text() if args.file is not None else sys.stdin.read()
)

tokens = tuple(lex(source))

macro = make_default_preprocessor_macro()

output = macro(tokens)

print(stringify(output if output is not None else tokens))
