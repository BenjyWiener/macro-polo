# macro-polo

Rust-style macros for Python

`macro-polo` brings Rust-inspired compile-time macros to Python. It's currently in very
early alpha, but even if it ever gets a stable release, you probably shouldn't use it in
any serious project. Even if you find a legitimate use case, the complete lack of
tooling support almost definitely outweighs the benefits. That said, if you do decide to
use it, I'd love to know why!


## Usage

`macro-polo` is modular, and can be extended at multiple levels. See the
[API Documentation](#api-documentation) for more details.

The simplest way to use it is to add a `coding: macro-polo` comment to the top of your
source file (in one of the first two lines). You can then declare and invoke macros
using the [`macro_rules!`](#macro_rules) syntax.

Example ([bijection.py](examples/macro_rules/bijection.py)):

```python
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
```

```
$ python3 examples/bijection.py
names_to_colors  => {'red': (1, 0, 0), 'green': (0, 1, 0), 'blue': (0, 0, 1)}
colors_to_names  => {(1, 0, 0): 'red', (0, 1, 0): 'green', (0, 0, 1): 'blue'}
names_to_colors ['green'] => (0, 1, 0)
colors_to_names [(0 ,0 ,1 )] => 'blue'
```

Viewing the generated code:
```
$ python3 -m macro_polo examples/bijection.py | ruff format -
```
```python
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
```


### Other encodings

If you want to specify a text encoding, you can append it to `macro_polo` after a `-` or
`_`, such as `# coding: macro-polo-utf-16`.


## `macro_rules!`

`macro_rules!` declarations consist of one or more rules, where each rule consists of a
matcher and a transcriber.

When the macro is invoked, it's input is compared to each matcher (in the order in which
they were defined). If the input macthes, the [capture variables](#capture-variables)
are extracted and passed to the transcriber, which creates a new token sequence to
replace the macro invocation.

This is the syntax for defining a `macro_rules!` macro:

<pre>
macro_rules!:
    [<i>matcher</i><sub>0</sub>]:
        <i>transcriber</i><sub>0</sub>

    <i>...</i>

    [<i>matcher</i><sub>n</sub>]:
        <i>transcriber</i><sub>n</sub>
</pre>

`macro_rules` macros can be recursive by transcibing a new invocation to themselves. See
[braces_and_more.py](examples/macro_rules/braces_and_more.py) for an example.


### Matchers

The following constructs are supported in `macro_rules!` matchers:

<table>
<thead>
    <tr>
        <th>Pattern</th>
        <th>Description</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td><code>$<em>name</em>:<em>type</em></code></td>
        <td>
            A <a href="#capture-variables">capture variable</a>.
        </td>
    </tr>
    <tr>
        <td>
            <code>$(<em>pattern</em>)<em>sep</em><sup>?</sup>?</code>
            <br/>
            <code>$(<em>pattern</em>)<em>sep</em><sup>?</sup>*</code>
            <br/>
            <code>$(<em>pattern</em>)<em>sep</em><sup>?</sup>+</code>
        </td>
        <td>
            A pattern repeater. Matches <code><em>pattern</em></code> ≤1
            (<code>?</code>), 0+ (<code>*</code>), or 1+ (<code>+</code>) times.
            <br/>
            If <code><em>sep</em></code> is present, it is a single-token separator
            that must match between each repitition.
            <br/>
            Capture variables inside repeaters become "repeating captures."
        </td>
    </tr>
    <tr>
        <td>
            <code>$[(<em>pattern<sub>0</sub></em>)|<em>...</em>|(<em>pattern<sub>n</sub></em>)]</code>
        </td>
        <td>
            A union of patterns. Patterns are tried sequentially from left to right.
            <br/>
            All pattern variants must contain the same capture variable names at the
            same levels of repitition depth.
            The capture variable types, on the other hand, need not match.
        </td>
    </tr>
    <tr>
        <td>
            <code>$[!<em>pattern</em>]</code>
        </td>
        <td>
            A negative lookahead. Matches zero tokens if <code><em>pattern</em></code>
            <b>fails</b> to match.
            If <code><em>pattern</em></code> <b>does</b> match, the negative lookahead
            will fail.
        </td>
    </tr>
    <tr>
        <td><code>$$</code></td>
        <td>Matches a <code>$</code> token.</td>
    </tr>
    <tr>
        <td><code>$></code></td>
        <td>Matches an <code>INDENT</code> token.</td>
    </tr>
    <tr>
        <td><code>$<</code></td>
        <td>Matches a <code>DEDENT</code> token.</td>
    </tr>
    <tr>
        <td><code>$^</code></td>
        <td>Matches a <code>NEWLINE</code> token.</td>
    </tr>
</tbody>
</table>

All other tokens are matched exactly (ex: `123` matches a `NUMBER` token with string
`'123'`)

#### Capture Variables

Capture variables are patterns that, when matched, bind the matching token(s) to a name
(unless the `name` is `_`).
They can then be used in a transcriber to insert the matched token(s) into the macro
output.

Capture variables consist of a `name` and a `type`. The `name` can be any Python
`NAME` token. The supported `type`s are described in the table below:

<table>
<thead>
    <tr>
        <th><code>type</code></th>
        <th>Description</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td><code>token</code></td>
        <td>
            Matches any single token, except <a href="#delimiters">delimiters</a>.
        </td>
    </tr>
    <tr>
        <td><code>name</code></td>
        <td>
            Matches a <a href="https://docs.python.org/3/library/token.html#token.NAME">
            <code>NAME</code></a> token.
        </td>
    </tr>
    <tr>
        <td><code>op</code></td>
        <td>
            Matches an <a href="https://docs.python.org/3/library/token.html#token.OP">
            <code>OP</code></a> token, except
            <a href="#delimiters">delimiters</a>.
        </td>
    </tr>
    <tr>
        <td><code>number</code></td>
        <td>
            Matches a <a href="https://docs.python.org/3/library/token.html#token.NUMBER">
            <code>NUMBER</code></a> token.
        </td>
    </tr>
    <tr>
        <td><code>string</code></td>
        <td>
            Matches a <a href="https://docs.python.org/3/library/token.html#token.STRING">
            <code>STRING</code></a> token.
        </td>
    </tr>
    <tr>
        <td><code>tt</code></td>
        <td>
            Matches a "token tree": either a single non-<a href="#delimiters">delimiter</a>
            token, or a pair of (balanced) delimiters and all of the tokens between them.
        </td>
    </tr>
    <tr>
        <td><code>null</code></td>
        <td>
            Always matches zero tokens. Useful for <a href="#counting-with-null">
            counting repitions</a>, or for filling in missing capture variables in union
            variants.
        </td>
    </tr>
</tbody>
</table>


### Transcribers

The following constructs are supported in `macro_rules!` transcribers:

<table>
<thead>
    <tr>
        <th>Pattern</th>
        <th>Description</th>
    </tr>
</thead>
<tbody>
    <tr>
        <td><code>$<em>name</em></code></td>
        <td>
            A <a href="#capture-variables">capture variable</a> substitution.
            Expands to the token(s) bound to <code><em>name</em></code>.
            <br/>
            If the corresponding capture variable appears within a repeater, the
            substitution must also be in a repeater at the same or greater nesting depth.
        </td>
    </tr>
    <tr>
        <td>
            <code>$(<em>pattern</em>)<em>sep</em><sup>?</sup>*</code>
        </td>
        <td>
            A pattern repeater. There must be at least one repeating substitution in
            <em>pattern</em>, which determines how many times the pattern will be
            expanded. If <em>pattern</em> contains multiple repeating substitutions,
            they must repeat the same number of times (at the current nesting depth).
            <br/>
            If <code><em>sep</em></code> is present, it is a single-token separator
            that will be expanded before each repitition after the first.
        </td>
    <tr>
        <td><code>$$</code></td>
        <td>Expands to a <code>$</code> token.</td>
    </tr>
    <tr>
        <td><code>$></code></td>
        <td>Expands to an <code>INDENT</code> token.</td>
    </tr>
    <tr>
        <td><code>$<</code></td>
        <td>Expands to a <code>DEDENT</code> token.</td>
    </tr>
    <tr>
        <td><code>$^</code></td>
        <td>Expands to a <code>NEWLINE</code> token.</td>
    </tr>
</tbody>
</table>

All other tokens are left unchanged.


### Delimiters

Delimiters are pairs of tokens that enclose other tokens, and must always be balanced.

There are five types of delimiters:

- Parentheses (`(`, `)`)
- Brackets (`[`, `]`)
- Curly braces (`{`, `}`)
- Indent/dedent
- f-strings

Note that f-strings come in *many* forms: `f'...'`, `rf"""..."""`, `Fr'''...'''`, ....

<details>
<summary>
Advanced Techniques
</summary>

- #### Counting with `null`

    Let's write a macro that counts the number of token trees in its input.
    We'll do this by replacing each token tree with `1 +` and then ending it of with a `0`.

    We can write a recursive macro to recursively replace the first token tree, one-by-one:

    ```python
    macro_rules! count_tts_recursive:
        [$t:tt $($rest:tt)*]:
            1 + count_tts_recursive!($($rest)*)

        []: 0
    ```

    Alternatively, we can use the `null` capture type to "count" the number of `tt`s, and
    then emit the same number of `1 +`s, all in one go:

    ```python
    macro_rules! count_tts_with_null:
        [$($_:tt $counter:null)*]:
            $($counter 1 +)* 0
    ```


- #### Matching terminators with negative lookahead

    Let's write a macro that replaces `;`s with newlines.

    ```python
    # coding: macro-polo

    macro_rules! replace_semicolons_with_newlines_naive:
        [$($($line:tt)*);*]:
            $($($line)*)$^*

    replace_semicolons_with_newlines_naive! { if 1: print(1); if 2: print(2) }
    ```

    When we try to run this, however, we get a `SyntaxError`.

    If we use run `macro_polo` directly to check the code being emitted, we see something
    strange:
    ```
    $ python3 -m macro_polo negative_lookahead_naive.py
    if 1 :print (1 );if 2 :print (2 )
    ```
    The input is left completely unchanged!

    The reason for this is actually quite simple: the `$line:tt` capture variable **matches
    the semicolon**, so the the entire input is captured in a single repition (of the outer
    repeater). What we really want is for `$line:tt` to match anything *except* `;`, which
    we can do with a negative lookahead:

    ```python
    # coding: macro-polo

    macro_rules! replace_semicolons_with_newlines:
        [$($($[!;] $line:tt)*);*]:
            $($($line)*)$^*

    replace_semicolons_with_newlines! { if 1: print(1); if 2: print(2) }
    ```

    Notice the addition of `$[!;]` before `$line:tt`.
    Now when we run this code, we get the output we expected:
    ```
    $ python3 examples/negative_lookahead.py
    1
    2
    ```
</details>


## Procedural Macros

For more complex macros, you can define a macro as a Python function that takes a
sequence of tokens as input and returns a new sequence of tokens as output. These are
referred to as "procedural macros" or "proc macros".

There are three types of procedural macros:

1. **function-style:**
    > _signature:_ `(tokens: Sequence[Token]) -> Sequence[Token]`

    Invoked the same way as `macro_rules` macros:

    `name!(input)`, `name![input]`, `name!{input}`, or

    ```
    name!:
        input
    ```

    When invoked, the function is called with the token sequence passed as input.

2. **module-level:**
    > _signature:_ `(parameters: Sequence[Token], tokens: Sequence[Token]) -> Sequence[Token]`

    Invoked with `![name(parameters)]` or `![name]` (equivalent to `![name()]`).
    Module-level macro invocations must come before all other code (with the exception
    of a docstring), and must each appear on their own line.

    When invoked, `parameters` is the token sequence following `name`, excluding the
    outer parentheses. `tokens` is the tokenized module starting from the line
    immediately following the invocation.

3. **decorator-style:**
    > _signature:_ `(parameters: Sequence[Token], tokens: Sequence[Token]) -> Sequence[Token]`

    Invoked with `@![name(parameters)]` or `@![name]` (equivalent to `@![name()]`).
    Decorator-style macro invocations must immediately precede a "block", defined as
    either a single newline-terminated line, or a line followed by an indented block.

    When invoked, `parameters` is the token sequence following `name`, excluding the
    outer parentheses. `tokens` is the tokenized block immediately following the
    invocation.


### Exporting and Importing Proc Macros

An important thing to know about proc macros is that they cannot be invoked in the same
module in which they are defined.

Instead, you use one of the three predefined decorator macros `function_macro`,
`module_macro`, and `decorator_macro` to mark a macro for export. You can then import it
using the predefined `import` module macro.

All three export macros take an optional `name` parameter as an alternative name to use
when exporting the macro. By default the name of the function is used.

Example [braces.py](examples/proc_macros/braces.py):

```python
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
        match tokens[i:i+2]:
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
```

We can then import and invoke our `braces` macro:

```python
# coding: macro-polo
"""An example of using the `import` macro and invoking a module macro."""
![import(braces)]
![braces]


for i in range(5) {:
    print('i =', i);
    if i % 2 == 0 {:
        print(i, 'is divisible by 2')
    :}
:}
```

```
$ python3 examples/proc_macros.py/uses_braces.py
i = 0
0 is divisible by 2
i = 1
i = 2
2 is divisible by 2
i = 3
i = 4
4 is divisible by 2
```

Practically, you'll probably want to use `macro_polo`'s lower-level machinary, instead
of re-implementing matching and transcribing.

### The `import` macro

We saw an example of importing a macro from another module. By default the `import`
macro will import all macros (including `macro_rules` macros) from the target module. If
you want to import specific macros, you can use the alternative `![import(x, y from z)]`
syntax.

One quirk of the `import` macro is that `macro_rules` imports are transitive (if module
`b` imports a `macro_rules` macro from module `a`, and then module `c` imports `b`, the
`macro_rules` macro from `a` will be imported into `c`). Proc macros, however, are _not_
transitive.


## API Documentation

WIP
