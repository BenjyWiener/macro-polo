"""Rust-style macros for Python."""

__all__ = [
    'MacroError',
]


class MacroError(Exception):
    """Base class for macro-processing errors."""
