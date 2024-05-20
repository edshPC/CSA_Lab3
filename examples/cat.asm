; Cat
_start:
in:
    in 1 ; symbol
    dup ; symbol, symbol
    push 0xA ; symbol, symbol, '\n'
    sub ; symbol, symbol-'\n'
    jz exit
    pop ; symbol
    out 2 ; -
    jmp in
exit:
    hlt