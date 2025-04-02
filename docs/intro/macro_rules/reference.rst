=========================
``macro_rules`` Reference
=========================

.. seealso::

    :mod:`macro_polo.macros.macro_rules`
        API reference for the ``macro_rules`` macros and declaration parser.

    :mod:`macro_polo.match`
        API reference for the pattern matching machinary used by ``macro_rules``.

    :mod:`macro_polo.transcribe`
        API reference for the output transcribing machinary used by ``macro_rules``.

``macro_rules!`` declarations consist of one or more rules, where each rule consists of
a matcher and a transcriber.

When the macro is invoked, its input is compared to each matcher (in the order in which
they were defined). If the input macthes, the
:ref:`capture variables <macro_rules-capture-variables>` are extracted and passed to the
transcriber, which creates a new token sequence to replace the macro invocation.

This is the syntax for defining a ``macro_rules!`` macro:

.. parsed-literal::

    macro_rules! *macro_name*:
        [*matcher*:sub:`0`]:
            *transcriber*:sub:`0`
        *...*
        [*matcher*:sub:`0`]:
            *transcriber*:sub:`n`

Matchers
========

The following constructs are supported in ``macro_rules!`` matchers:

    Capture Variable
        :samp:`${name}:{type}`

        A :ref:`capture variable <macro_rules-capture-variables>`.

    Repeater
        :samp:`$({pattern})?`
        | :samp:`$({pattern})*`
        | :samp:`$({pattern}){sep}*`
        | :samp:`$({pattern})+`
        | :samp:`$({pattern}){sep}+`

        A pattern repeater. Matches :samp:`{pattern}` ≤1
        (``?``), ≥0 (``*``), or ≥1 (``+``) times.

        If :samp:`{sep}` is present, it is a single-token separator that must match
        between each repitition.

        Capture variables inside repeaters become "repeating captures."

    Union
        :samp:`$[({pattern})|{...}|({pattern})]`

        A union of patterns. Patterns are tried sequentially from left to right.

        All pattern variants must contain the same capture variable names at the same
        levels of repitition depth. The capture variable types, on the other hand, need
        not match.

    Negative Lookahead
        :samp:`$[!{pattern}]`

        A negative lookahead. Matches zero tokens if :samp:`{pattern}` **fails** to
        match. If :samp:`{pattern}` **does** match, the negative lookahead will fail.

    Escape Sequences
        ``$$``
            Matches a single ``$`` token.

        ``$>``
            Matches an :data:`~token.INDENT` token.

        ``$<``
            Matches a :data:`~token.DEDENT` token.

        ``$^``
            Matches a :data:`~token.NEWLINE` token.

    All other tokens are matched exactly (ex: ``123`` matches a :data:`~token.NUMBER`
    token with string ``'123'``).

.. _macro_rules-capture-variables:

Capture Variables
-----------------

Capture variables are patterns that, when matched, bind the matching token(s) to a name
(unless that name is ``_``).
They can then be used in a transcriber to insert the matched token(s) into the macro
output.

Capture variables consist of a :samp:`{name}` and a :samp:`{type}`. The :samp:`{name}`
can be any :data:`~token.NAME` token. The supported :samp:`{type}`\ s are described
below:

    ``token``
        Matches any single token, except :ref:`delimiters <macro_rules-delimiters>`.

    ``name``
        Matches a :data:`~token.NAME` token.

    ``op``
        Matches a :data:`~token.OP` token, except :ref:`delimiters <macro_rules-delimiters>`.

    ``number``
        Matches a :data:`~token.NUMBER` token.

    ``string``
        Matches a :data:`~token.STRING` token.

    ``tt``
        Matches a "token tree": either a single non-:ref:`delimiter <macro_rules-delimiters>`
        token, or a pair of (balanced) delimiters and all of the tokens between them.

    ``null``
        Always matches zero tokens. Useful for
        :ref:`counting repitions <macro_rules-counting-with-null>`, or for filling in
        missing capture variables in union variants.

Transcribers
============

The following constructs are supported in ``macro_rules!`` transcribers:

    Capture Variable Substitution
        :samp:`${name}`

        A :ref:`capture variable <macro_rules-capture-variables>`.

        Transcribes the token(s) bound to :samp:`{name}`.

        If the corresponding capture variable appears within a repeater, the
        substitution must also be in a repeater at the same or greater nesting depth.

    Repeater
        :samp:`$({pattern})*`
        | :samp:`$({pattern}){sep}*`

        A pattern repeater. There must be at least one repeating substitution in
        :samp:`{pattern}`, which determines how many times the pattern will be
        transcribed. If :samp:`{pattern}` contains multiple repeating substitutions,
        they must repeat the same number of times (at the current nesting depth).

        If :samp:`{sep}` is present, it is a single-token separator that will be
        transcribed before each repitition after the first.

    Escape Sequences
        ``$$``
            Transcribes a single ``$`` token.

        ``$>``
            Transcribes an :data:`~token.INDENT` token.

        ``$<``
            Transcribes a :data:`~token.DEDENT` token.

        ``$^``
            Transcribes a :data:`~token.NEWLINE` token.

    All other tokens are transcribed unchanged.

.. _macro_rules-delimiters:

Delimiters
----------

Delimiters are pairs of tokens that enclose other tokens, and must always be balanced.

There are five types of delimiters:

- Parentheses (``(``, ``)``)
- Brackets (``[``, ``]``)
- Curly braces (``{``, ``}``)
- Indent/dedent
- f-strings

Note that f-strings come in *many* forms:
``f'...'``, ``rf"""..."""``, ``Fr'''...'''``, ....

Invoking
========

``macro_rules`` macros have four invocation styles:

.. parsed-literal::

    *macro_name*!(*input tokens*)

.. parsed-literal::

    *macro_name*![*input tokens*]

.. parsed-literal::

    *macro_name*!{*input tokens*}

.. parsed-literal::

    *macro_name*!:
        *input*
        *tokens*

.. important::

    Due to the way Python's tokenizer works, indentation and newlines are only preserved
    by the last (block) style.
