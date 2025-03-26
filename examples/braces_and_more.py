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
