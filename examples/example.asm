; Example of commands
fake_number:
    add ; Используем команду как данные
hex:
    word 0xA10F
buf:
    resw 0x100
    db 0
array:
    db 10, 7, 12, 1, 666, 0x100, "AB"
array_len:
    db 8
array_pointer:
    db array

; f(x) = x^2 + 2x - 7
function:
    dup ; x, x
    dup ; x, x, x
    mul ; x, x^2
    swap ; x^2, x
    push 2
    mul ; x^2, 2x
    push 7 ; x^2, 2x, 7
    sub ; x^2, 2x-7
    add ; x^2 + 2x - 7
    ret

_start:
    push array_pointer ; *arr
loop:
    dup
    dup ; *arr+i x3
    push_by ; *arr+i x2, arr[i]
    call function ; *arr+i x2, f(arr[i])
    swap ; *arr+i, f(arr[i]), *arr+i
    pop_by ; *arr+i
    inc ; *arr+i+1
    dup ; *arr+i+1 x2
    push array_pointer ; *arr+i+1 x2, *arr
    sub ; *arr+i+1, i+1
    push array_len ; *arr+i+1, i+1, len
    sub ; *arr+i+1, i+1-len ; if 0 it is the end
    jz end
    pop ; *arr+i+1 ; next element
    jmp loop
end:
    push fake_number ; Кладем на стек команду add как данные
