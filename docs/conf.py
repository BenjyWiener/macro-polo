"""Configuration file for the Sphinx documentation builder."""

from pathlib import Path
import sys


# -- Path setup --------------------------------------------------------------

sys.path.append(str(Path('_ext').resolve()))

# -- Project information -----------------------------------------------------

project = 'macro-polo'
copyright = '2025, Benjy Wiener'
author = 'Benjy Wiener'

# -- General configuration ---------------------------------------------------

extensions = [
    'expandmacros',
    'runscript',
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx_inline_tabs',
    'sphinx_toolbox.more_autodoc.autoprotocol',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

autodoc_typehints = 'description'
autodoc_class_signature = 'separated'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

highlight_language = 'python'
pygments_style = 'staroffice'
pygments_dark_style = 'github-dark'

suppress_warnings = [
    'misc.highlighting_failure',  # code with macros is not valid Python syntax
]

# -- Options for HTML output -------------------------------------------------

html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    'light_css_variables': {
        'color-brand-primary': '#813a29',
        'color-foreground-secondary': '#813a29',
        'color-background-primary': '#f6eedc',
        'color-background-secondary': '#fffcf1',
        'color-background-border': '#e6d8d4',
        'color-admonition-background': 'var(--color-background-secondary)',
        'color-inline-code-background': '#00000018',
        'font-stack--headings': 'Georgia, serif',
    },
    'sidebar_hide_name': True,
}
html_logo = '_static/macro-polo-with-text.png'
html_favicon = '_static/favicon.ico'
