==========
macro-polo
==========

*Explore new syntax!*

|licence| |version| |pyversions| |docs|

.. |licence| image:: https://img.shields.io/badge/license-MIT-green
    :target: https://pypi.python.org/pypi/macro-polo

.. |version| image:: https://img.shields.io/pypi/v/macro-polo.svg
    :target: https://pypi.python.org/pypi/macro-polo

.. |pyversions| image:: https://img.shields.io/pypi/pyversions/macro-polo.svg
    :target: https://pypi.python.org/pypi/macro-polo

.. |docs| image:: https://img.shields.io/readthedocs/macro-polo.svg
   :target: https://macro-polo.readthedocs.io

macro-polo brings Rust-inspired macros to Python, as well as a a full API for building
custom Python preprocessors.

Enabling macros in your project is as simple as installing ``macro-polo`` and adding
``coding: macro-polo`` to the top of your modules:

.. tab:: Source

   .. literalinclude:: ../examples/macro_rules/power_dict.py

.. tab:: Expanded

   .. expandmacros:: ../examples/macro_rules/power_dict.py

.. tab:: Output

   .. runscript:: examples/macro_rules/power_dict.py
      :cwd: ..


Getting Started
===============

Interested? Check out :doc:`intro/index` to start exploring.

.. warning::

   macro-polo is currently in very early alpha, but even if it ever gets a stable
   release, you probably shouldn't use it in any serious project. Even if you find a
   legitimate use case, the complete lack of tooling support almost definitely outweighs
   the benefits. That said, if you do decide to use it, I'd love to know why!


.. toctree::
   :maxdepth: 2
   :hidden:

   intro/index
   reference/index
