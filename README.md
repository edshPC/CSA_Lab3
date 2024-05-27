# CSA_Lab3

Лабораторная работа #3 по дисциплине "Архитектура компьютера"\
Выполнил: Щербинин Эдуард Павлович, P3214

Вариант из таблицы:\
`asm | stack | neum | mc -> hw | instr | struct | stream | port | cstr | prob2 | cache`\
Выполнена в базовом варианте:\
`asm | stack | neum | mc | tick | struct | stream | port | cstr | prob2 | -`

## Язык программирования

### Синтаксис

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
        | <op1> ' 0x' [1-9a-f] [0-9a-f]*
        | "word" ' ' ".*"
        
<op0> ::= "nop"
      | "pop"
      | "push_by"
      | "pop_by"
      | "swap"
      | "add"
      | "sub"
      | "mul"
      | "div"
      | "mod"
      | "neg"
      | "inc"
      | "dec"
      | "dup"
      | "ret"
      | "hlt"

<op1> ::= "push"
      | "pop"
      | "jmp"
      | "jz"
      | "jn"
      | "call"
      | "in"
      | "out"
      | "resw"
      
      
<comment> ::= ' '* ';' [^\n]*

```

### Семантика

Код выполняется последовательно, одна инструкция за другой.

Метки определяются на отдельной строке исходного кода.
Чувствительны к регистру. Переопределение недопустимо.\
Метки могут быть использованы как аргумент (в т.ч. до определения)\
Адресация начинается с `0x1`. Адрес `0x0` интерпретируется как `NULL`.

Выполнение программы начинается с обязательной метки `_start`.

Доступны команды транслятора:

* `WORD <arg>` - объявить переменную в памяти
* `DB <arg>` - WORD alias
* `RESW <amount>` - зарезервировать в памяти буфер на `amount` машинных слов. Инициализируется нулями

Для набора инструкций см. [систему команд](#система-команд)\
Команды не чуствительны к регистру: `WORD == word`\
Символ `;` и всё после него (до конца строки) считается комментарием и будет проигнорировано

Пример использования:

```asm
decimal: ; Определение метки
    word 42 ; Инициализирует ячейку десячитным числом
    db 42 ; Эквивалент
hexadecimal:
    word 0xA ; Инициализирует ячейку шестнадцатеричным числом
message:
    word "Hello, world!", 0xA, 0 ; Инициализирует каждый символ строки в собственную ячейку по порядку
buffer:
    resw 256 ; Выделит в памяти 256 слов
    resw 0x100 ; Эквивалент

_start: ; начало выполнения программы
    push decimal ; Как аргумент команде передастся адрес метки decimal
```

С примером программы, работающей с массивом чисел, можно ознакомиться [тут](examples/example.asm)

## Организация памяти

### Основная память

* DRAM
* Архитектура: фон Неймана, данные **могут** интерпретироваться как команды, а команды - как данные
* Размер одной ячейки памяти - 64 бита
* В ячейках памяти хранятся строго числа
* Адресация - прямая абсолютная, поддерживается прямая загрузка на стек
* Доступ осуществляется по адресу, хранящемся в регистре `AR (Address reg)`
* Поддерживаются 31-битные беззнаковые адреса, наличие `1` в 31-м бите показывает прямую загрузку 31-битного знакового литерала на стек вместо обращения в память

### Стек

* 64-разрядный
* Вершина стека `TOS` представляет последний элемент стека, доступ к стеку возможен **исключительно** через `TOS`
* Аппаратно представляет собой SRAM память + регистр-указатель вершины стека, который по сигналу ин(де-)крементируется. Обращение к `TOS` является обращением к памяти по адресу в этом регистре

```text
           memory                             stack
+----------------------------+    +----------------------------+
| 00 : undefined (NULL)      |    | 00 :       ...             |
| 01 :      ...              |    |                            |
| part for variables/data/buf|    |           data             |
|           ...              |    |                            |
| n  : program start         |    |            ...             |
|           ...              |    |----------------------------|
| m  : hlt                   |    | n  :       TOS             |
+----------------------------+    +----------------------------+
```

Ячейка памяти `0x1` соответствует адресу первой инструкции / константы.
Попытка обратиться к адресу `0x0` игнориуется.\
Рекомендуется задавать константы / выделять буфера в начале программы,
далее после метки `_start` задавать машинные инструкции,
для исключения вероятности выполнения данных как инструкций.

### Память микрокоманд

* Read-Only Memory
* Размер одной ячейки микрокоманды - 32 бита
* Каждый бит микрокоманды соответсвутет определённому сигналу

```text
     microcommand memory
+----------------------------+
| 00 : NOP, goto instr fetch |
| 01 : instruction fetch t1  |
| 02 : instruction fetch t2  |
| 03 :      ...              | 
|   microcoded instructions  |
|           ...              |
+----------------------------+
```

## Система команд

Особенности:

* Машинное слово - 64 бита
* Старшие 32 бита машинного слова указывают на адрес начала исполнения инструкции в памяти микрокоманд
* Младшие 32 бита - аргумент инструкции, в зависимости от 31-го бита будет либо загружен из памяти, либо прямой загузкой в стек
* Обработка данных осуществляется только в стеке данных через `TOS`
* Поток управления:
    * Значение счётчика команд `PC` инкрементируется после исполнения последней микрокоманды каждой инструкции
    * Значение счётчика микрокоманд `mPC` инкрементируется каждый такт, устанавливается на цикл выборки команды `0x1` после исполнения последней микрокоманды каждой инструкции
    * Поддерживаются безусловные и условные переходы

Набор инструкций (обозначения: `<аргумент>`, `{..., TOS-1, TOS}`, `[опционально]`):

* `NOP` – нет операции
* `PUSH <addr/lit>` - положить на вершину стека значение по адресу метки / прямое значение
* `POP [<addr>] {e1}` - снять значение с вершины стека и [положить по адресу метки]
* `PUSH_BY {e1}` - положить на вершину стека значение по адресу вершины стека e1
* `POP_BY {e1, e2}` - по адресу вершины стека e2 положить значение вершины стека e1
* `SWAP {e1, e2}` - положить 2 элемента стека в обратном порядке e2, e1
* `ADD {e1, e2}` – положить на стек результат операции сложения e1 + e2
* `SUB {e1, e2}` – положить на стек результат операции вычитания e1 – e2
* `MUL {e1, e2}` – положить на стек результат операции умножения e1 * e2
* `DIV {e1, e2}` – положить на стек результат операции _целочисленного_ деления e1 / e2
* `MOD {e1, e2}` – положить на стек результат операции взятия остатка e1 % e2.
* `NEG {e1}` – инвертировать знак элемента вершины стека
* `INC {e1}` – увеличить значение вершины стека на 1
* `DEC {e1}` – уменьшить значение вершины стека на 1
* `DUP {e1}` – дублировать элемент с вершины стека
* `JMP <addr>` - совершить переход по указанному адресу
* `JZ <addr>` - если TOS равен 0, совершить переход по указанному адресу
* `JN <addr>` - если TOS отрицательный, совершить переход по указанному адресу
* `CALL <addr>` - вызвать функцию по указанному адресу
* `RET` - вернуться из функции на следующую после вызова инструкцию
* `IN <port>` - получить данные из внешнего устройства по указанному порту и загрузить на стек
* `OUT <port>` - отправить данные во внешнее устройство по указанному порту со стека и снять его
* `HLT` - остановить программу

Если команда задействовала `{элемент стека}`, он будет снят со стека.

## Транслятор

CLI: `python translator.py <input_file> <target_file>`

Реализован в модуле [translator](./translator.py)\
Трансляция реализуется в два прохода:

1. Генерация машинного кода без адресов переходов и расчёт значений меток перехода
    * [Машинные инструкции](#система-команд) один в один транслируются в машинные команды
    * [Команды транслятора](#семантика) определяют напрямую начальное состояние памяти
    * Машинный код представляет собой JSON-объект из начального адреса и списка машинных инструкций
2. Подстановка адресов меток в аругументы инструкци

## Модель процессора

CLI: `python machine.py [-h | --help] <program_file> [input_file] [-t TICKLIM] [-m MEMSIZE] [-d DSIZE] [-r RSIZE] [-l LOGLEVEL]`,\
где

* `TICKLIM` - лимит тактов симуляции (default 10^4)
* `MEMSIZE` - размер основной памяти в ячейках (default 2^16)
* `DSIZE` - размер стека данных процессора (default 2^8)
* `RSIZE` - размер стека возвратов процессора (default 2^8)
* `LOGLEVEL` - уровень логирования (default DEBUG)

Реализована в модуле [machine](./machine.py)

Описание:

* Микропрограммное управление
* Микрокод расшифровывается и исполняется посигнально
* Исполнение инструкции проходит в два этапа:
    * цикл выборки: 2 такта, по окончанию цикла счётчик микрокоманд указывает на начало нужной инструкции в памяти микрокоманд
    * цикл исполнения: зависит от инструкции, в среднем 2-4 такта, по окончанию цикла счётчик микрокоманд возвращается на цикл выборки
* Процесс моделирования – потактовый, каждый такт выводится в файл логирования
* Начало симуляции происходит в функции `simulation`
* Остановка моделирования проиходит в случае:
    * выполнения инструкции `HLT`
    * превышения лимита тактов симуляции
    * попытки получить элемент из пустого потока ввода
    * попытки получить значение из любого из пустых стеков
    * попытки положить значение на любой из заполненных стеков

Схема:
![Схема](schema.png)
Не загружается изображение? Загляните [сюда](schema.png)

### DataPath

Реализован в модуле [datapath](./datapath.py)

Описание устройств:

* `ControlUnit` - [ControlUnit](#controlunit)
* `Data stack` - [стек данных](#стек), хранящий текущие данные для обработки
* `BUFFER` - дополнительный регистр, куда могут приходить различные значения, перед загрузкой на стек. Нужен для возможности получения доступа к двум различным операндам
* `ALU` - АЛУ, поддерживающее различные операции. Имеет дополнительные регистры для возможности последовательной загрузки и снятия нескольких операндов стека
* `Memory` - [основная память](#основная-память)
* `ADDRESS` - регистр, в котором хранится адрес памяти для обращения
* `IO Controller` - контроллер ввода-вывода, принимающий и декодирующий порт устройства, по сигналу читает или записывает в одно из устройств `Unit X` данные

Описание сигналов (все сигналы приходят от ControlUnit'а, исполняются за 1 такт):

* `dsPUSH` - положить значение на стек данных (инициализируется `0`)
* `dsPOP` - снять значение со стека данных
* `latchTOS` - защёлкнуть значение на вершине стека данных (из `BUFFER`)
* `latchBUF` - защёлкнуть значение в `BUFFER`
* `latchAR` - защёлкнуть значение в `ADDRESS`
* `memREAD` - прочитать значение из памяти по адресу в `ADDRESS`
* `memWRITE` - записать значение в память (из `TOS`) по адресу в `ADDRESS`
* `IN` - прочитать очередное значение из устройства ввода с портом в `BUFFER(15..0)`
* `OUT` - отправить значение (из `TOS`) устройству вывода с портом в `BUFFER(15..0)`
* `aluLEFT` - защёлкнуть значение в левом регистре АЛУ (из `TOS`)
* `aluRIGHT` - защёлкнуть значение в правом регистре АЛУ (из `TOS`)
* `aluNEG` - брать из левого регистра значение `- LEFT`
* `aluINC` - брать из левого регистра значение `LEFT + 1`
* `aluDEC` - брать из левого регистра значение `LEFT - 1`
* `aluNOP` - пропустить через АЛУ значение `LEFT`
* `aluADD` - пропустить через АЛУ значение `LEFT + RIGHT`
* `aluSUB` - пропустить через АЛУ значение `LEFT - RIGHT`
* `aluMUL` - пропустить через АЛУ значение `LEFT * RIGHT`
* `aluDIV` - пропустить через АЛУ значение `LEFT // RIGHT`
* `aluMOD` - пропустить через АЛУ значение `LEFT % RIGHT`

### ControlUnit

Реализован в модуле [controlunit](./controlunit.py)

Описание устройств:

* `DataPath` - [DataPath](#datapath)
* `_tick` - спец регистр-счётчик тиков, нужен для отладки
* `Ret stack` - [стек возвратов](#стек), в который можно положить текущее состояние `PC` либо снять предыдущее
* `PC` - счётчик команд, регистр, в котором хранится адрес очередной инструкции для исполнения
* `BRANCHER` - спец устройство-комбинационная схема, которая, учитывая сигналы, определеяет, какое значение пропустить мультиплексору в `PC`
* `mPC` - счётчик микрокоманд, регистр, в котором хранится адрес (памяти микрокоманд) очередной исполняемой микрокоманды
* `Microcommand memory` - Read-only [память микрокоманд](#память-микрокоманд), выдаёт всегда значение по адресу в `mPC`
* `Microcommand` - регистр, в котором хранится текущая исполняемая микрокоманда для ее декодирования по сигналам

Описание сигналов (исполняются за 1 такт):

* `tick` - инкременитировать значение счётчика тиков, приходит строго каждый такт
* `latchPC` - защёлкнуть значение в счётчике команд
* `latchMPC` - защёлкнуть значение в счётчике микрокоманд
* `latchMC` - защёлкнуть значение в регистре микрокоманд из памяти микрокоманд
* `statePUSH` - положить и защёлкнуть на стеке возвратов значение `PC`
* `statePOP` - снять значение со стека возвратов
* `BRANCH` - сигнал перехода (пропустить в `PC` значение перехода)
* `jz_branch` - совершить `BRANCH` только если `Z-flag` - истина
* `jn_branch` - совершить `BRANCH` только если `N-flag` - истина

## Тестирование

* Тестирование осуществляется при помощи golden test-ов
* Тесты реализованы в модуле [golden_test](golden_test.py)
* Выполняются все тесты в директории [golden](golden)

Запустить тесты: `poetry run pytest . -v`\
Обновить конфигурацию: `poetry run pytest . -v --update-goldens`

CI при помощи [Github Actions](.github/workflows/python.yaml):

<details>
<summary>Spoiler</summary>

```yaml
name: Python CI

on:
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Run tests and collect coverage
        run: |
          poetry run coverage run -m pytest .
          poetry run coverage report -m
        env:
          CI: true

  lint:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.12

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install poetry
          poetry install

      - name: Check code formatting with Ruff
        run: poetry run ruff format --check .

      - name: Run Ruff linters
        run: poetry run ruff check .
```

где:

* `poetry` - управления зависимостями для языка программирования Python.
* `coverage` - формирование отчёта об уровне покрытия исходного кода.
* `pytest` - утилита для запуска тестов.
* `ruff` - утилита для форматирования и проверки стиля кодирования.

</details>

Пример использования и журнал работы процессора на примере [cat](examples/cat.asm):

<details>
<summary>Spoiler</summary>

```shell
> python translator.py examples/cat.asm target.json
source LoC: 14 code instr: 10
> cat target.json
{"start": 1, "code": [{"index": 1, "opcode": "in", "args": [2147483649]},
 {"index": 2, "opcode": "dup", "args": []},
 {"index": 3, "opcode": "push", "args": [2147483658]},
 {"index": 4, "opcode": "sub", "args": []},
 {"index": 5, "opcode": "jz", "args": [9]},
 {"index": 6, "opcode": "pop", "args": []},
 {"index": 7, "opcode": "out", "args": [2147483650]},
 {"index": 8, "opcode": "jmp", "args": [1]},
 {"index": 9, "opcode": "hlt", "args": []},
 {"index": 10, "opcode": "hlt", "args": []}]}
> echo "cat" $'\n' > input.txt
> python machine.py target.json input.txt
DEBUG   machine:simulation     Tick: 0 	mPC: 0x1 	PC: 0x1 	BUF: 0x0 	AR: 0x0 	MC: 0x0
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 1 	mPC: 0x2 	PC: 0x1 	BUF: 0x0 	AR: 0x1 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 2 	mPC: 0x2a 	PC: 0x1 	BUF: 0x2a80000001 	AR: 0x1 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   datapath:sig_in        input: 'c'
DEBUG   machine:simulation     Tick: 3 	mPC: 0x2b 	PC: 0x1 	BUF: 0x63 	AR: 0x1 	MC: 0x10000100
 	DataStack[0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 4 	mPC: 0x1 	PC: 0x2 	BUF: 0x63 	AR: 0x1 	MC: 0x6
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 5 	mPC: 0x2 	PC: 0x2 	BUF: 0x63 	AR: 0x2 	MC: 0x60
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 6 	mPC: 0x23 	PC: 0x2 	BUF: 0x2300000000 	AR: 0x2 	MC: 0x410
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 7 	mPC: 0x24 	PC: 0x2 	BUF: 0x63 	AR: 0x2 	MC: 0x81100
 	DataStack[99, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 8 	mPC: 0x1 	PC: 0x3 	BUF: 0x63 	AR: 0x2 	MC: 0x6
 	DataStack[99, 99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 9 	mPC: 0x2 	PC: 0x3 	BUF: 0x63 	AR: 0x3 	MC: 0x60
 	DataStack[99, 99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 10 	mPC: 0x5 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x3 	MC: 0x410
 	DataStack[99, 99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 11 	mPC: 0x6 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x8000000a 	MC: 0x1a0
 	DataStack[99, 99, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 12 	mPC: 0x1 	PC: 0x4 	BUF: 0xa 	AR: 0x8000000a 	MC: 0x406
 	DataStack[99, 99, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 13 	mPC: 0x2 	PC: 0x4 	BUF: 0xa 	AR: 0x4 	MC: 0x60
 	DataStack[99, 99, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 14 	mPC: 0x15 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x410
 	DataStack[99, 99, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 15 	mPC: 0x16 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x2200
 	DataStack[99, 99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 16 	mPC: 0x1 	PC: 0x5 	BUF: 0x59 	AR: 0x4 	MC: 0x9006
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 17 	mPC: 0x2 	PC: 0x5 	BUF: 0x59 	AR: 0x5 	MC: 0x60
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 18 	mPC: 0x26 	PC: 0x5 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x410
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 19 	mPC: 0x1 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x1800002
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 20 	mPC: 0x2 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x6 	MC: 0x60
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 21 	mPC: 0x7 	PC: 0x6 	BUF: 0x700000000 	AR: 0x6 	MC: 0x410
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 22 	mPC: 0x8 	PC: 0x6 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa0
 	DataStack[99, 89 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 23 	mPC: 0x1 	PC: 0x7 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa02
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 24 	mPC: 0x2 	PC: 0x7 	BUF: 0x700000000 	AR: 0x7 	MC: 0x60
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 25 	mPC: 0x2c 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x410
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   datapath:sig_out       output: '' << 'c'
DEBUG   machine:simulation     Tick: 26 	mPC: 0x2d 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x20000000
 	DataStack[99 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 27 	mPC: 0x1 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x202
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 28 	mPC: 0x2 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x8 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 29 	mPC: 0x25 	PC: 0x8 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 30 	mPC: 0x1 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x800002
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 31 	mPC: 0x2 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x1 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 32 	mPC: 0x2a 	PC: 0x1 	BUF: 0x2a80000001 	AR: 0x1 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   datapath:sig_in        input: 'a'
DEBUG   machine:simulation     Tick: 33 	mPC: 0x2b 	PC: 0x1 	BUF: 0x61 	AR: 0x1 	MC: 0x10000100
 	DataStack[0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 34 	mPC: 0x1 	PC: 0x2 	BUF: 0x61 	AR: 0x1 	MC: 0x6
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 35 	mPC: 0x2 	PC: 0x2 	BUF: 0x61 	AR: 0x2 	MC: 0x60
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 36 	mPC: 0x23 	PC: 0x2 	BUF: 0x2300000000 	AR: 0x2 	MC: 0x410
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 37 	mPC: 0x24 	PC: 0x2 	BUF: 0x61 	AR: 0x2 	MC: 0x81100
 	DataStack[97, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 38 	mPC: 0x1 	PC: 0x3 	BUF: 0x61 	AR: 0x2 	MC: 0x6
 	DataStack[97, 97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 39 	mPC: 0x2 	PC: 0x3 	BUF: 0x61 	AR: 0x3 	MC: 0x60
 	DataStack[97, 97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 40 	mPC: 0x5 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x3 	MC: 0x410
 	DataStack[97, 97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 41 	mPC: 0x6 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x8000000a 	MC: 0x1a0
 	DataStack[97, 97, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 42 	mPC: 0x1 	PC: 0x4 	BUF: 0xa 	AR: 0x8000000a 	MC: 0x406
 	DataStack[97, 97, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 43 	mPC: 0x2 	PC: 0x4 	BUF: 0xa 	AR: 0x4 	MC: 0x60
 	DataStack[97, 97, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 44 	mPC: 0x15 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x410
 	DataStack[97, 97, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 45 	mPC: 0x16 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x2200
 	DataStack[97, 97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 46 	mPC: 0x1 	PC: 0x5 	BUF: 0x57 	AR: 0x4 	MC: 0x9006
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 47 	mPC: 0x2 	PC: 0x5 	BUF: 0x57 	AR: 0x5 	MC: 0x60
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 48 	mPC: 0x26 	PC: 0x5 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x410
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 49 	mPC: 0x1 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x1800002
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 50 	mPC: 0x2 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x6 	MC: 0x60
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 51 	mPC: 0x7 	PC: 0x6 	BUF: 0x700000000 	AR: 0x6 	MC: 0x410
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 52 	mPC: 0x8 	PC: 0x6 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa0
 	DataStack[97, 87 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 53 	mPC: 0x1 	PC: 0x7 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa02
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 54 	mPC: 0x2 	PC: 0x7 	BUF: 0x700000000 	AR: 0x7 	MC: 0x60
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 55 	mPC: 0x2c 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x410
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   datapath:sig_out       output: 'c' << 'a'
DEBUG   machine:simulation     Tick: 56 	mPC: 0x2d 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x20000000
 	DataStack[97 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 57 	mPC: 0x1 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x202
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 58 	mPC: 0x2 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x8 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 59 	mPC: 0x25 	PC: 0x8 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 60 	mPC: 0x1 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x800002
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 61 	mPC: 0x2 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x1 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 62 	mPC: 0x2a 	PC: 0x1 	BUF: 0x2a80000001 	AR: 0x1 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   datapath:sig_in        input: 't'
DEBUG   machine:simulation     Tick: 63 	mPC: 0x2b 	PC: 0x1 	BUF: 0x74 	AR: 0x1 	MC: 0x10000100
 	DataStack[0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 64 	mPC: 0x1 	PC: 0x2 	BUF: 0x74 	AR: 0x1 	MC: 0x6
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 65 	mPC: 0x2 	PC: 0x2 	BUF: 0x74 	AR: 0x2 	MC: 0x60
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 66 	mPC: 0x23 	PC: 0x2 	BUF: 0x2300000000 	AR: 0x2 	MC: 0x410
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 67 	mPC: 0x24 	PC: 0x2 	BUF: 0x74 	AR: 0x2 	MC: 0x81100
 	DataStack[116, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 68 	mPC: 0x1 	PC: 0x3 	BUF: 0x74 	AR: 0x2 	MC: 0x6
 	DataStack[116, 116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 69 	mPC: 0x2 	PC: 0x3 	BUF: 0x74 	AR: 0x3 	MC: 0x60
 	DataStack[116, 116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 70 	mPC: 0x5 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x3 	MC: 0x410
 	DataStack[116, 116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 71 	mPC: 0x6 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x8000000a 	MC: 0x1a0
 	DataStack[116, 116, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 72 	mPC: 0x1 	PC: 0x4 	BUF: 0xa 	AR: 0x8000000a 	MC: 0x406
 	DataStack[116, 116, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 73 	mPC: 0x2 	PC: 0x4 	BUF: 0xa 	AR: 0x4 	MC: 0x60
 	DataStack[116, 116, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 74 	mPC: 0x15 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x410
 	DataStack[116, 116, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 75 	mPC: 0x16 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x2200
 	DataStack[116, 116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 76 	mPC: 0x1 	PC: 0x5 	BUF: 0x6a 	AR: 0x4 	MC: 0x9006
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 77 	mPC: 0x2 	PC: 0x5 	BUF: 0x6a 	AR: 0x5 	MC: 0x60
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 78 	mPC: 0x26 	PC: 0x5 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x410
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 79 	mPC: 0x1 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x1800002
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 80 	mPC: 0x2 	PC: 0x6 	BUF: 0x2600000009 	AR: 0x6 	MC: 0x60
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 81 	mPC: 0x7 	PC: 0x6 	BUF: 0x700000000 	AR: 0x6 	MC: 0x410
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 82 	mPC: 0x8 	PC: 0x6 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa0
 	DataStack[116, 106 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 83 	mPC: 0x1 	PC: 0x7 	BUF: 0x700000000 	AR: 0x0 	MC: 0xa02
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 84 	mPC: 0x2 	PC: 0x7 	BUF: 0x700000000 	AR: 0x7 	MC: 0x60
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 85 	mPC: 0x2c 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x410
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   datapath:sig_out       output: 'ca' << 't'
DEBUG   machine:simulation     Tick: 86 	mPC: 0x2d 	PC: 0x7 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x20000000
 	DataStack[116 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 87 	mPC: 0x1 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x7 	MC: 0x202
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 88 	mPC: 0x2 	PC: 0x8 	BUF: 0x2c80000002 	AR: 0x8 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 89 	mPC: 0x25 	PC: 0x8 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 90 	mPC: 0x1 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x8 	MC: 0x800002
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 91 	mPC: 0x2 	PC: 0x1 	BUF: 0x2500000001 	AR: 0x1 	MC: 0x60
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 92 	mPC: 0x2a 	PC: 0x1 	BUF: 0x2a80000001 	AR: 0x1 	MC: 0x410
 	DataStack[ <-]
 	RetStack[ <-]
DEBUG   datapath:sig_in        input: '\n'
DEBUG   machine:simulation     Tick: 93 	mPC: 0x2b 	PC: 0x1 	BUF: 0xa 	AR: 0x1 	MC: 0x10000100
 	DataStack[0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 94 	mPC: 0x1 	PC: 0x2 	BUF: 0xa 	AR: 0x1 	MC: 0x6
 	DataStack[10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 95 	mPC: 0x2 	PC: 0x2 	BUF: 0xa 	AR: 0x2 	MC: 0x60
 	DataStack[10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 96 	mPC: 0x23 	PC: 0x2 	BUF: 0x2300000000 	AR: 0x2 	MC: 0x410
 	DataStack[10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 97 	mPC: 0x24 	PC: 0x2 	BUF: 0xa 	AR: 0x2 	MC: 0x81100
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 98 	mPC: 0x1 	PC: 0x3 	BUF: 0xa 	AR: 0x2 	MC: 0x6
 	DataStack[10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 99 	mPC: 0x2 	PC: 0x3 	BUF: 0xa 	AR: 0x3 	MC: 0x60
 	DataStack[10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 100 	mPC: 0x5 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x3 	MC: 0x410
 	DataStack[10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 101 	mPC: 0x6 	PC: 0x3 	BUF: 0x58000000a 	AR: 0x8000000a 	MC: 0x1a0
 	DataStack[10, 10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 102 	mPC: 0x1 	PC: 0x4 	BUF: 0xa 	AR: 0x8000000a 	MC: 0x406
 	DataStack[10, 10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 103 	mPC: 0x2 	PC: 0x4 	BUF: 0xa 	AR: 0x4 	MC: 0x60
 	DataStack[10, 10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 104 	mPC: 0x15 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x410
 	DataStack[10, 10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 105 	mPC: 0x16 	PC: 0x4 	BUF: 0x1500000000 	AR: 0x4 	MC: 0x2200
 	DataStack[10, 10 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 106 	mPC: 0x1 	PC: 0x5 	BUF: 0x0 	AR: 0x4 	MC: 0x9006
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 107 	mPC: 0x2 	PC: 0x5 	BUF: 0x0 	AR: 0x5 	MC: 0x60
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 108 	mPC: 0x26 	PC: 0x5 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x410
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 109 	mPC: 0x1 	PC: 0x9 	BUF: 0x2600000009 	AR: 0x5 	MC: 0x1800002
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 110 	mPC: 0x2 	PC: 0x9 	BUF: 0x2600000009 	AR: 0x9 	MC: 0x60
 	DataStack[10, 0 <-]
 	RetStack[ <-]
DEBUG   machine:simulation     Tick: 111 	mPC: 0x4 	PC: 0x9 	BUF: 0x400000000 	AR: 0x9 	MC: 0x410
 	DataStack[10, 0 <-]
 	RetStack[ <-]
INFO    machine:simulation    Program halted
INFO    machine:simulation    Output: cat
cat
Ticks: 111

```

</details>

Пример тестирования:

<details>
<summary>Spoiler</summary>

```shell
> poetry run pytest . -v
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-7.4.4, pluggy-1.5.0 -- /home/runner/.cache/pypoetry/virtualenvs/csa-lab3-KALrB3YY-py3.12/bin/python
cachedir: .pytest_cache
rootdir: /home/runner/work/CSA_Lab3/CSA_Lab3
configfile: pyproject.toml
plugins: golden-0.2.2
collecting ... collected 5 items
golden_test.py::test_translator_asm_and_machine[golden/cat.yml] PASSED   [ 20%]
golden_test.py::test_translator_asm_and_machine[golden/hello_username.yml] PASSED [ 40%]
golden_test.py::test_translator_asm_and_machine[golden/hello_world.yml] PASSED [ 60%]
golden_test.py::test_translator_asm_and_machine[golden/example.yml] PASSED [ 80%]
golden_test.py::test_translator_asm_and_machine[golden/prob2.yml] PASSED [100%]
============================== 5 passed in 3.75s ===============================
```

</details>

```text
| ФИО                      | алг            | LoC | code инстр | такт  |
| Щербинин Эдуард Павлович | cat            | 14  | 10         | 351   |
| Щербинин Эдуард Павлович | hello_world    | 18  | 11         | 317   |
| Щербинин Эдуард Павлович | hello_username | 50  | 33         | 1260  |
```
