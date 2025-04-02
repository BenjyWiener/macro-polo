===============================
The ``macro-polo`` custom codec
===============================

``macro-polo`` comes with a custom encoding, making it super simple to enable macros in
your module. Just add a ``coding`` directive in one the first two lines of your file:

.. code-block:: python

    # coding: macro-polo

That's it! When you execute or import the file with Python, it will automatically be
passed through ``macro-polo``'s preprocessor.

Other Encodings
===============

If you also need to specify a text encoding, you can simply append it to the
``macro-polo`` encoding after a ``-`` or ``_``:

.. code-block:: python

    # coding: macro-polo-utf-16

Next Steps
==========

Now that you've got everything set up, head over to :doc:`macro_rules/index` to learn how to
write your first macro.
