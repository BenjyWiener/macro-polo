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
