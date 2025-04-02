# coding: macro-polo

macro_rules! count_tts_with_null:
    [$($_:tt $counter:null)*]:
        $($counter 1 +)* 0

print(count_tts_with_null![a b c d e])
