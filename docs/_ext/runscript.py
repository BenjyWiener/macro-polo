"""Custom directive for displaying the output of a script."""

from pathlib import Path
import shlex
import subprocess
import sys

from docutils import nodes
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective


class RunScriptDirective(SphinxDirective):
    """Directive for displaying the output of a script."""

    required_arguments = 1  # File path
    optional_arguments = 1  # Shell-quoted command line arguments
    final_argument_whitespace = True
    option_spec = {
        'cwd': Path,
        'display-name': str,
    }

    def run(self) -> list[nodes.Node]:
        """Run this directive."""
        script_path = self.arguments[0]

        if len(self.arguments) > 1:
            args = shlex.split(self.arguments[1])
        else:
            args = []

        cwd: Path = self.options.get('cwd', Path())
        if not cwd.is_absolute() and self.state.document.current_source is not None:
            cwd = Path(self.state.document.current_source).parent / cwd

        if not (cwd / script_path).is_file():
            return [
                nodes.error(
                    '', nodes.paragraph(text=f'File not found: {cwd / script_path}')
                )
            ]

        display_name = self.options.get('display-name', str(script_path))

        result = subprocess.run(
            [sys.executable, script_path, *args],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            encoding=sys.getdefaultencoding(),
            check=False,
        )

        content = (
            f'$ python3 {shlex.quote(display_name)} {shlex.join(args)}\n'
            + result.stdout
        )

        literal = nodes.literal_block(content, content)
        literal['language'] = 'console' if result.returncode == 0 else 'pytb'
        return [literal]


def setup(app: Sphinx) -> None:
    """Set up the extension."""
    app.add_directive('runscript', RunScriptDirective)
