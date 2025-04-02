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

macro-polo brings Rust-inspired compile-time macros to Python. It's currently in very
early alpha, but even if it ever gets a stable release, you probably shouldn't use it in
any serious project. Even if you find a legitimate use case, the complete lack of
tooling support almost definitely outweighs the benefits. That said, if you do decide to
use it, I'd love to know why!

Installation
============

::

    pip install macro-polo

Usage
=====

macro-polo is modular, and can be extended at multiple levels. See the API Reference for
more details.

The simplest way to use it is to add a ``coding: macro-polo`` comment to the top of your
source file (in one of the first two lines). You can then declare and invoke macros
using the ``macro_rules!`` syntax.

Example (examples/macro_rules/bijection.py):

.. code-block:: python

    # coding: macro-polo
    """A basic demonstration of `macro_rules!`."""


    macro_rules! bijection:
        [$($key:tt: $val:tt),* $(,)?]:
            (
                {$($key: $val),*},
                {$($val: $key),*}
            )


    macro_rules! debug_print:
        [$($expr:tt)*]:
            print(
                stringify!($($expr)*), '=>', repr($($expr)*),
                file=__import__('sys').stderr,
            )


    names_to_colors, colors_to_names = bijection! {
        'red': (1, 0, 0),
        'green': (0, 1, 0),
        'blue': (0, 0, 1),
    }


    debug_print!(names_to_colors)
    debug_print!(colors_to_names)

    debug_print!(names_to_colors['green'])
    debug_print!(colors_to_names[(0, 0, 1)])

.. code-block:: console

    $ python3 examples/bijection.py
    names_to_colors  => {'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1)}
    colors_to_names  => {(1, 0, 0): 'red', (0, 1, 0): 'green', (0, 0, 1): 'blue'}
    names_to_colors ['green'] => (0, 1, 0)
    colors_to_names [(0 ,0 ,1 )] => 'blue'

Viewing the generated code:

.. code-block:: console

    $ python3 -m macro_polo examples/bijection.py | ruff format -

.. code-block:: python

    names_to_colors, colors_to_names = (
        {'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1)},
        {(1, 0, 0): 'red', (0, 1, 0): 'green', (0, 0, 1): 'blue'},
    )
    print(
        'names_to_colors',
        '=>',
        repr(names_to_colors),
        file=__import__('sys').stderr,
    )
    print(
        'colors_to_names',
        '=>',
        repr(colors_to_names),
        file=__import__('sys').stderr,
    )
    print(
        "names_to_colors ['green']",
        '=>',
        repr(names_to_colors['green']),
        file=__import__('sys').stderr,
    )
    print(
        'colors_to_names [(0 ,0 ,1 )]',
        '=>',
        repr(colors_to_names[(0, 0, 1)]),
        file=__import__('sys').stderr,
    )

Interested?
===========

Check out the `full documentation <https://macro-polo.readthedocs.io>`_ and
`tutorial <https://macro-polo.readthedocs.io/en/latest/intro/index.html>`_.
