# coding: macro-polo

macro_rules! my_macro:
    []:
        'My first macro!'

    [$s:string]:
        f'Got {$s!r}'

print(my_macro!('howdy'))
