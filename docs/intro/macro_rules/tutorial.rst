========================
``macro_rules`` Tutorial
========================

``macro_rules`` allow us to define macros in terms of pairs of input and output
patterns, referred to as *matchers* and *transcribers*. Each pair makes up a *rule*, and
a group of rules is, well, a ``macro_rules``.

Our First ``macro_rules``
=========================

Let's dive right in! Create a new script named ``first_macro_rules.py`` and add the
following:

.. tab:: Source

    .. literalinclude:: _scripts/tutorial0_0.py

.. tab:: Expanded

    .. expandmacros:: _scripts/tutorial0_0.py

.. tab:: Output

    .. runscript:: _scripts/tutorial0_0.py
        :display-name: first_macro_rules.py

We defined a macro with a single rule, matching an empty *token sequence*. What if we
try invoking it on a non-empty input?

.. tab:: Source

    .. literalinclude:: _scripts/tutorial0_1.py
        :emphasize-lines: 7

.. tab:: Output

    .. runscript:: _scripts/tutorial0_1.py
        :display-name: first_macro_rules.py

We got a :class:`macro_polo.MacroError`:

.. code-block:: text

    macro_polo.MacroError: invoking function-like macro 'my_macro': body didn't match expected pattern

Let's add a new rule to handle this case:

.. tab:: Source

    .. literalinclude:: _scripts/tutorial0_2.py
        :emphasize-lines: 7-8

.. tab:: Expanded

    .. expandmacros:: _scripts/tutorial0_2.py

.. tab:: Output

    .. runscript:: _scripts/tutorial0_2.py
        :display-name: first_macro_rules.py

Great! But this only handles the specific token ``'hello'``. How can we handle *any*
token?

Capture Variables
-----------------

Capture variables allow us to *capture* tokens of a specific type, binding them to a
name that we can later use in the transcriber. Capture variables have the syntax
``$name:type`` in matchers, and just ``$name`` in transcribers.

Let's modify our rule to accept any ``string`` token:

.. tab:: Source

    .. literalinclude:: _scripts/tutorial0_3.py
        :emphasize-lines: 7-8,10

.. tab:: Expanded

    .. expandmacros:: _scripts/tutorial0_3.py

.. tab:: Output

    .. runscript:: _scripts/tutorial0_3.py
        :display-name: first_macro_rules.py

Nice! But what if we want to accept *any number* of strings?

Repeaters
---------

That brings us to repeaters. Repeaters let us---wait for it---repeat patterns. They come
in three flavors, or repition modes:

- :samp:`$({pattern})?` matches :samp:`{pattern}` ≤1 times
- :samp:`$({pattern})*` matches :samp:`{pattern}` ≥0 times
- :samp:`$({pattern})+` matches :samp:`{pattern}` ≥1 times

Additionally, the latter two accept an optional separator token between the closing
parenthesis and mode indicator.

Let's see an example:

.. tab:: Source

    .. literalinclude:: _scripts/tutorial0_4.py
        :emphasize-lines: 7-8,10

.. tab:: Expanded

    .. expandmacros:: _scripts/tutorial0_4.py

.. tab:: Output

    .. runscript:: _scripts/tutorial0_4.py
        :display-name: first_macro_rules.py
