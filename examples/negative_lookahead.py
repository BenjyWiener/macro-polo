# coding: macro_polo
"""A demonstration of using negative lookaheads."""


macro_rules! replace_semicolons_with_newlines_naive:
    [$($($line:tt)*);*]:
        $($($line)*)$^*


# Causes a SyntaxError
#replace_semicolons_with_newlines_naive! { if 1: print(1); if 2: print(2) }


macro_rules! replace_semicolons_with_newlines:
    [$($($[!;] $line:tt)*);*]:
        $($($line)*)$^*

replace_semicolons_with_newlines! { if 1: print(1); if 2: print(2) }
