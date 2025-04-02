# coding: macro-polo

macro_rules! replace_semicolons_with_newlines_naive:
    [$($($line:tt)*);*]:
        $($($line)*)$^*

replace_semicolons_with_newlines_naive! { if 1: print(1); if 2: print(2) }
