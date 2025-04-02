# coding: macro-polo

macro_rules! my_macro:
    []:
        'My first macro!'

    [$($s:string);+]:
        f'Got {[ $(repr($s)),* ]}'

print(my_macro!('hey'; 'hi'; "what's up"))
