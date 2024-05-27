; Hello username
first_message:
    db "Hello! What is your name?", 10, 0
second_message:
    db "Hello, "
user_message:
    resw 0x100
buffer_end:
    db 0
first_symbol:
    db first_message
second_symbol:
    db second_message
user_symbol:
    db user_message
buffer_end_pointer:
    db buffer_end

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

    push user_symbol ; *sym
input_loop:
    dup ; *sym x2
    in 1 ; *sym x2, sym
    dup
    push 10
    sub ; *sym x2, sym, sym-'\n'
    jz input_exit
    pop ; *sym x2, sym
    swap ; *sym, sym, *sym
    pop_by ; *sym
    inc ; *sym+1
    dup ; *sym+1 x2
    push buffer_end_pointer
    sub ; *sym+1, *sym-*end+1
    jz input_exit ; дошли до конца буфера
    pop
    jmp input_loop

input_exit:
    push second_symbol
    call print_string
