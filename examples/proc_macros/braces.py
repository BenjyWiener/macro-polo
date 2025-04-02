# coding: macro-polo
"""An example of a module proc macro that adds braces-support to Python."""

import token

from macro_polo import Token


@![module_macro]
def braces(parameters, tokens):
    """Add braces support to a Python module.

    The following sequences are replaced:
    - `{:` becomes `:` followed by INDENT
    - `:}` becomes DEDENT
    - `;` becomes NEWLINE
    """
    output = []
    i = 0
    while i < len(tokens):
        match tokens[i : i + 2]:
            case Token(token.OP, '{'), Token(token.OP, ':'):
                output.append(Token(token.OP, ':'))
                output.append(Token(token.INDENT, ''))
                i += 2
            case Token(token.OP, ':'), Token(token.OP, '}'):
                output.append(Token(token.DEDENT, ''))
                i += 2
            case Token(token.OP, ';'), _:
                output.append(Token(token.NEWLINE, '\n'))
                i += 1
            case _:
                output.append(tokens[i])
                i += 1

    return output
