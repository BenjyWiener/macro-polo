# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import sys
from pathlib import Path

# -- Path setup --------------------------------------------------------------

sys.path.append(str(Path('_ext').resolve()))

# -- Project information -----------------------------------------------------

project = 'macro-polo'
copyright = '2025, Benjy Wiener'
author = 'Benjy Wiener'

# -- General configuration ---------------------------------------------------

extensions = [
    'runscript',
    'sphinx.ext.autodoc',
    'sphinx_inline_tabs',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

highlight_language = 'python'
pygments_style = 'staroffice'

suppress_warnings = [
    'misc.highlighting_failure',  # code with macros is not valid Python syntax
]

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#813a29",
        "color-foreground-secondary": "#813a29",
        "color-background-primary": "#f6eedc",
        "color-background-secondary": "#fffcf1",
        "font-stack--headings": "Georgia, serif",
    },
}

# -- Register custom codec ---------------------------------------------------

import pretty_codec
pretty_codec.register()
