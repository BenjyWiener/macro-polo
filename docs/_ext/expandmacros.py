"""Custom directive for expanding macros in and then formatting a script."""

from pathlib import Path
import subprocess
import sys

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


class ExpandMacrosDirective(SphinxDirective):
    """Directive for expanding macros in and then formatting a script."""

    required_arguments = 1  # File path
    optional_arguments = 0
    final_argument_whitespace = True

    def run(self) -> list[nodes.Node]:
        """Run this directive."""
        script_path = Path(self.arguments[0])
        if self.state.document.current_source is not None:
            script_path = Path(self.state.document.current_source).parent / script_path

        if not script_path.is_file():
            return [
                nodes.error('', nodes.paragraph(text=f'File not found: {script_path}'))
            ]

        try:
            sys.path.insert(0, str(script_path.parent))
            expanded = script_path.read_text('macro-polo')
        finally:
            sys.path.remove(str(script_path.parent))

        ruff_config_path = Path(__file__).parent / 'post-expansion-ruff.toml'
        try:
            formatted = subprocess.check_output(
                ['ruff', 'format', f'--config={ruff_config_path}', '-'],
                input=expanded,
                encoding=sys.getdefaultencoding(),
            )
        except subprocess.CalledProcessError:
            formatted = expanded

        content = formatted.lstrip('\n')

        literal = nodes.literal_block(content, content)
        literal['language'] = 'python'
        return [literal]


def setup(app: Sphinx) -> None:
    """Set up the extension."""
    app.add_directive('expandmacros', ExpandMacrosDirective)
