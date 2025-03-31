# coding: macro-polo
"""Add `if` and `for` support to dict literals."""


macro_rules! power_dict:
    [@ [if $($[!:] $cond:tt)+: $($item:tt)+] $($tail:tt)*]:
        **({$($item)*} if ($($cond)*) else {}), power_dict!(@ $($tail)*)

    [@ [for $($[!:] $for_stmt:tt)+: $($item:tt)+] $($tail:tt)*]:
        **{$($item)* for $($for_stmt)*}, power_dict!(@ $($tail)*)

    [@ [$($item:tt)+] $($tail:tt)*]:
        $($item)*, power_dict!(@ $($tail)*)

    [@]:

    [$($($[!,] $items:tt)+),* $(,)?]:
        { power_dict!(@ $([$($items)*])*) }


if __name__ == '__main__':
    from pprint import pprint

    pprint(power_dict! {
        0: 1,
        if 1 == 2:
            1: 2,
        if 2 == 2:
            2: 2,
        for word in ('cat', 'bird', 'horse'):
            word: word[::-1],
        for i in range(4) for j in range(4) if i < j:
            (i, j): i * j,
    })
