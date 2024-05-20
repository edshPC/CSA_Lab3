; Prob2
val_a:
    db 0
val_b:
    db 1
sum:
    db 0
output:
    resw 0x20
output_symbol:
    db output_symbol

print_string:
    dup
    push_by
    jz print_exit
    out 2
    inc
    jmp print_string
print_exit:
    pop
    ret

check:
    push sum ; sum
    push val_a ; sum, a
    push 2 ; sum, a, 2
    mod ; sum, a%2
    jz sum_a
    pop ; sum
    jmp skip_a
sum_a:
    pop ; sum
    push val_a ; sum, a
    add ; sum+a
skip_a:
    push val_b ; sum, b
    push 2 ; sum, b, 2
    mod ; sum, b%2
    jz sum_b
    pop ; sum
    jmp skip_b
sum_b:
    pop ; sum
    push val_b ; sum, b
    add ; sum+b
skip_b:
    pop sum
    ret


_start:
    push val_a
    push val_b
    add
    pop val_a

    push val_a
    push val_b
    add
    pop val_b

    call check
    push 4000000
    push val_b
    sub
    jn end
    pop
    jmp _start
end:
    pop
    push sum
output_loop:
    dup
    push 10
    mod
    push 48 ; ascii '0'
    add
    push output_symbol
    dec
    dup
    pop output_symbol
    pop_by
    push 10
    div
    jz exit
    jmp output_loop
exit:
    push output_symbol
    push 0
    pop output_symbol
    call print_string

