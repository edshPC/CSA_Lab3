; Hello username
first_message:
    db "Hello! What is your name?", 10, 0
second_message:
    db "Hello, "
user_message:
    resw 0x100
    db 0
first_symbol:
    db first_message
second_symbol:
    db second_message
user_symbol:
    db user_message

; Печатает строку. Аргумент - указатель начала строки, возращает указатель на конец строки
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

_start:
    push first_symbol
    call print_string
    pop

input_loop:
    push user_symbol
    in 1
    dup
    push 10
    sub
    jz input_exit
    pop
    push user_symbol
    pop_by
    inc
    pop user_symbol
    jmp input_loop

input_exit:
    push second_symbol
    call print_string