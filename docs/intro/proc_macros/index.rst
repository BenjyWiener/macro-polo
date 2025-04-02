=================
Procedural Macros
=================

For more complex macros, you can define a macro as a Python function that takes a
sequence of tokens as input and returns a new sequence of tokens as output. These are
referred to as "procedural macros" or "proc macros".

Types of Proc Macros
====================

There are three types of procedural macros:

.. glossary::

    function-style macro
        Implements the :protocol:`~macro_polo.macros.types.Macro` protocol.

        Invoked as:

        .. parsed-literal::

            *macro_name*!(*input tokens*)

        or

        .. parsed-literal::

            *macro_name*![*input tokens*]

        or

        .. parsed-literal::

            *macro_name*!{*input tokens*}

        or

        .. parsed-literal::

            *macro_name*!:
                *input*
                *tokens*

        .. important::

            Due to the way Python's tokenizer works, indentation and newlines are only preserved
            by the last (block) style.

        When invoked, the registered macro is called with a single argument, the token
        sequence passed as input.

        .. note::

            ``macro_rules`` are function-style macros.

    module-level macro
        Implements the :protocol:`~macro_polo.macros.types.ParameterizedMacro` protocol.

        Invoked with :samp:`![{name}({parameters})]` or :samp:`![{name}]` (equivalent to
        :samp:`![{name}()]`).

        Module-level macro invocations must come before all other code (with the exception
        of a docstring), and must each appear on their own line.

        When invoked, the registered macro is called with two arguments:

        1. :samp:`{parameters}` (as a token sequence)
        2. the remainder of the module starting from the line immediately following the
           invocation (as a token sequence).

    decorator-style macro
        Implements the :protocol:`~macro_polo.macros.types.ParameterizedMacro` protocol.

        Invoked with :samp:`@![{name}({parameters})]` or :samp:`@![{name}]` (equivalent to
        :samp:`@![{name}()]`).

        Decorator-style macro invocations must immediately precede a "block", defined as
        either a single newline-terminated line, or a line followed by an indented block.

        When invoked, the registered macro is called with two arguments:

        1. :samp:`{parameters}` (as a token sequence)
        2. the block immediately following the invocation (as a token sequence).

        When multiple decorator-style macros are stacked, they are invoked from bottom to
        top.


Exporting Proc Macros
=====================

.. important::

    Proc macros cannot be invoked in the same module in which they are defined.

To make a function usable as a macro, you use one of the three predefined decorator
macros ``function_macro``, ``module_macro``, and ``decorator_macro`` to mark a macro for
export. You can then import it using the predefined ``import`` module macro.

All three export macros take an optional ``name`` parameter as an alternative name to
use when exporting the macro. By default the name of the function is used.

Example:

.. literalinclude:: ../../../examples/proc_macros/braces.py

We can then import and invoke our ``braces`` macro:

.. tab:: Source

    .. literalinclude:: ../../../examples/proc_macros/uses_braces.py

.. tab:: Expanded

    .. expandmacros:: ../../../examples/proc_macros/uses_braces.py

.. tab:: Output

    .. runscript:: examples/proc_macros/uses_braces.py
        :cwd: ../../..

Practically, you'll probably want to use macro_polo's lower-level machinary, instead
of re-implementing things like matching, transcribing, and scanning.

.. seealso::

    :doc:`../importing`
        More information about the ``import`` macro.

    :mod:`macro_polo.match`
        Pattern matching utilities.

    :mod:`macro_polo.transcribe`
        Token transcribing utilities.

    :mod:`macro_polo.parse`
        Utilities for parsing :class:`~macro_polo.match.MacroMatcher`\ s and
        :class:`~macro_polo.transcribe.MacroTranscriber`\ s from ``macro_rules``-like
        syntax.

    :mod:`macro_polo.macros.super`
        Utilities for composing macros.
