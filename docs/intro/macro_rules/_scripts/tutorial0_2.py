# coding: macro-polo

macro_rules! my_macro:
    []:
        'My first macro!'

    ['hello']:
        'Got "hello"'

print(my_macro!('hello'))
