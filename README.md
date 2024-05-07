# CSA_Lab3
Лабораторная работа #3 по дисциплине "Архитектура компьютера"\
Выполнил: Щербинин Эдуард Павлович, P3214

Вариант из таблицы:\
`asm | stack | neum | mc -> hw | instr | struct | stream | port | cstr | prob2 | cache`\
Выполнен в базовом варианте:\
`asm | stack | neum | mc | tick | struct | stream | port | cstr | prob2 | -`

## Язык программирования
#### Синтаксис
```ebnf
<program> ::= <line>+

<line> ::= <label> <comment>? '\n'
       | <instr> <comment>? '\n'
       | <comment>? '\n'

<label> ::= <label_name> ':'

<label_name> ::= [a-zA-Z_]+

<instr> ::= <op0>
        | <op1> ' ' <label_name>
        | <op1> ' ' [1-9] [0-9]*
        
<op0> ::= "add"
      | "halt"

<op1> ::= "push"
      | "pop"
      
<comment> ::= ' '* ';' [^\n]*

```

#### Семантика
Код выполняется последовательно, одна инструкция за другой.
