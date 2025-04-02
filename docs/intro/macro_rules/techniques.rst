===================
Advanced Techniques
===================

Tips and tricks for writing complex ``macro_rules``.

.. _macro_rules-counting-with-null:

Counting with ``null``
======================

Let's write a macro that counts the number of token trees in its input.
We'll do this by replacing each token tree with ``1 +`` and then ending it of with a
``0``.

We can write a recursive macro to recursively replace the first token tree, one-by-one:

.. tab:: Source

    .. literalinclude:: _scripts/count_tts_recursive.py

.. tab:: Expanded

    .. expandmacros:: _scripts/count_tts_recursive.py

.. tab:: Output

    .. runscript:: count_tts_recursive.py
        :cwd: _scripts

Alternatively, we can use the ``null`` capture type to "count" the number of ``tt``\ s,
and then emit the same number of ``1 +``\ s, all in one go:

.. tab:: Source

    .. literalinclude:: _scripts/count_tts_with_null.py

.. tab:: Expanded

    .. expandmacros:: _scripts/count_tts_with_null.py

.. tab:: Output

    .. runscript:: count_tts_with_null.py
        :cwd: _scripts

Matching terminators with negative lookahead
============================================

Let's write a macro that replaces ``;``\ s with newlines.

.. tab:: Source

    .. literalinclude:: _scripts/replace_semicolons_with_newlines_naive.py

.. tab:: Expanded

    .. expandmacros:: _scripts/replace_semicolons_with_newlines_naive.py

.. tab:: Output

    .. runscript:: replace_semicolons_with_newlines_naive.py
        :cwd: _scripts

When we try to run this, however, we get a ``SyntaxError``.

If we look at the expanded source code, we notice something strange: the input is left
completely unchanged!

The reason for this is actually quite simple: the ``$line:tt`` capture variable matches
the semicolon, so the the entire input is captured in a single repition (of the outer
repeater). What we really want is for ``$line:tt`` to match anything *except* ``;``,
which we can do with a negative lookahead:

.. tab:: Source

    .. literalinclude:: _scripts/replace_semicolons_with_newlines.py
        :emphasize-lines: 4

.. tab:: Expanded

    .. expandmacros:: _scripts/replace_semicolons_with_newlines.py

.. tab:: Output

    .. runscript:: replace_semicolons_with_newlines.py
        :cwd: _scripts

Notice the addition of ``$[!;]`` before ``$line:tt``.
Now when we run this code, we get the output we expected.
