# coding: macro_polo
"""A demonstration of using the `null` capture type to count."""


macro_rules! count_tts_recursive:
    [$t:tt $($rest:tt)*]:
        1 + count_tts_recursive!($($rest)*)

    []: 0


macro_rules! count_tts_with_null:
    [$($_:tt $counter:null)*]:
        $($counter 1 +)* 0


print(count_tts_recursive![0 1 2 3 4 5])
print(count_tts_with_null![0 1 2 3 4 5])
