# coding: macro-polo

macro_rules! count_tts_recursive:
    [$t:tt $($rest:tt)*]:
        1 + count_tts_recursive!($($rest)*)

    []: 0


print(count_tts_recursive![a b c d e])
