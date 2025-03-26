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

The simplest way to use it is to add a `coding: macro_polo` comment to the top of your
source file (in one of the first two lines). You can then declare and invoke macros
using the [`macro_rules!`](#macro_rules) syntax.

Example ([bijection.py](examples/bijection.py)):

```python
# coding: macro_polo
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

A more complex example, with multiple recursive match arms
([braces_and_more.py](examples/braces_and_more.py)):

```python
# coding: macro_polo
"""A demonstration of recursive `macro_rules!`."""


macro_rules! braces_and_more:
    # Replace braces with indentation, using `${ ... }` to prevent conflicts with
    # other uses of curly braces, such as dicts and sets.
    # Note: due to the way Python's tokenizer works, semicolons are necessary within
    # braced blocks. We replace them with newlines (using `$^`).
    [$${
        # This part matches 0 or more groups of non-semicolon token trees
        $(
            # This matches 0 or more non-semicolon token trees
            $($[!;] $inner:tt)*
        );*
    } $($rest:tt)*]:
        braces_and_more!:
            :
                $($($inner)*)$^*
        braces_and_more!($($rest)*)

    # Allow using names from other modules without explicitly importing them.
    # Example: `os.path::join` becomes `__import__('os.path').path.join`
    [$module:name$(.$submodules:name)*::$member:name $($rest:tt)*]:
        __import__(
            # Call stringify! on each name individually to avoid problematic spaces
            stringify!($module) $('.' stringify!($submodules))*
        )$(.$submodules)*.$member braces_and_more!($($rest)*)

    # Allow using $NAME to access environment variables
    [$$ $var:name $($rest:tt)*]:
        __import__('os').environ[stringify!($var)] braces_and_more!($($rest)*)

    # Allow using $NUMBER to access command line arguments
    [$$ $index:number $($rest:tt)*]:
        __import__('sys').argv[$index] braces_and_more!($($rest)*)

    # Recurse into nested structures (except f-strings)
    [($($inner:tt)*) $($rest:tt)*]:
      (braces_and_more!($($inner)*)) braces_and_more!($($rest)*)

    [[$($inner:tt)*] $($rest:tt)*]:
      [braces_and_more!($($inner)*)] braces_and_more!($($rest)*)

    [{$($inner:tt)*} $($rest:tt)*]:
      {braces_and_more!($($inner)*)} braces_and_more!($($rest)*)

    # The special sequences `$>` and `$<` expand to INDENT and DEDENT respectively.
    [$> $($inner:tt)* $< $($rest:tt)*]:
      $> braces_and_more!($($inner)*) $< braces_and_more!($($rest)*)

    # Handle other tokens by leaving them unchanged
    [$t:tt $($rest:tt)*]:
        $t braces_and_more!($($rest)*)

    # Handle empty input
    []:


braces_and_more!:
    for child in pathlib::Path($1).iterdir() ${
        if child.is_file() ${
            size = child.stat().st_size;
            print(f'{child.name} is {size} bytes');
        }
    }
```

```
$ python3 examples/braces_and_more.py examples
negative_lookahead.py is 452 bytes
nqueens.py is 9049 bytes
bijection.py is 648 bytes
braces_and_more.py is 2423 bytes
counting_with_null.py is 381 bytes
```

Viewing the generated code:
```
$ python3 -m macro_polo examples/braces_and_more.py | ruff format -
```
```python
"""A demonstration of recursive `macro_rules!`."""

for child in __import__('pathlib').Path(__import__('sys').argv[1]).iterdir():
    if child.is_file():
        size = child.stat().st_size
        print(f'{child.name} is {size} bytes')
```


### Other encodings

If you want to specify a text encoding, you can append it to `macro_polo` after a `-` or
`_`, such as `# coding: macro_polo-utf-16`.


## `macro_rules!`

`macro_rules!` declarations consist of one or more rules, where each rule consists of a
matcher and a transcriber.

When the macro is invoked, it's input is compared to each matcher (in the order in which
they were defined). If the input macthes, the [capture variables](#capture-variables)
are extracted and passed to the transcriber, which creates a new token sequence to
replace the macro invocation.


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
            <strong>fails</strong> to match.
            If <code><em>pattern</em></code> <strong>does</strong> match, the negative
            lookahead will fail.
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

Capture variables are patterns that, when matches, bind the matching token(s) to a name
(unless the *`name`* is `_`).
They can then be used in a transcriber to insert the matched token(s) into the macro
output.

Capture variables consist of a *`name`* and a *`type`*. The *`name`* can be any Python
`NAME` token. The supported *`type`*s are described in the table below:

<table>
<thead>
    <tr>
        <th><code><em>type</em></code></th>
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


### Advanced Techniques

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
    # coding: macro_polo

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
    # coding: macro_polo

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

## API Documentation

WIP


<style>
code {
    text-wrap-mode: nowrap;
}
</style>
