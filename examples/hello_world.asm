; Hello world
message:
    db "Hello, world!", 10, 0
symbol:
    db message

_start:
    push symbol ; symbol
hi:
    dup ; symbol, symbol
    push_by ; symbol, [symbol]
    jz exit
    out 2 ; symbol
    inc ; symbol++
    jmp hi
exit:
    hlt