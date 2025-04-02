================
Importing Macros
================

It's often useful to be able to use a macro from more than one module.
:doc:`Proc macros <proc_macros/index>` can only be invoked in a different module.

Enter the ``import`` macro.

``import`` is a :term:`module-level macro` that allows you to use macros defined in
another module. It has two forms:

:samp:`![import({module})]`
    Import all macros defined in :samp:`{module}`.

:samp:`![import ({name1}, {name2}, {...} from {module})]`
    Import only the specified macros from :samp:`{module}`.

.. note::

    One quirk of the ``import`` macro is that ``macro_rules`` imports are transitive (if
    module ``b`` imports a ``macro_rules`` macro from module ``a``, and then module ``c``
    imports ``b``, the ``macro_rules`` macro from ``a`` will be imported into ``c``).
    Proc macro imports, however, are *not* transitive.
