# coding: macro-polo

macro_rules! my_macro:
    []:
        'My first macro!'

    [$s:string]:
        ('Got ' + repr($s))

print(my_macro!('hello'))
