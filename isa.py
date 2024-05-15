import json
from enum import Enum
import re


class Opcode(str, Enum):
    WORD = "word"
    DB = "db"
    RESW = "resw"

    NOP = "nop"
    HLT = "hlt"
    PUSH = "push"
    POP = "pop"

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    INC = "inc"
    DEC = "dec"
    DUP = "dup"

    JMP = "jmp"

    # Оператор загрузки литералов в память, не может быть вызван из программы
    _MEM = "mem"

    @property
    def arg_count(self):
        return {
            self.WORD: (1, 1024),
            self.DB: (1, 1024),
            self.RESW: (1, 1),

            self.PUSH: (1, 1),
            self.POP: (0, 1),
            self.JMP: (1, 1),

            self._MEM: (-1, -1)
        }.get(self, (0, 0))

    def __str__(self):
        return str(self.value)

counter = 32
def autoshift():  # 1 << counter++
    global counter
    counter += 1
    return 1 << (counter - 1)

# Микрокоды команд
class MC(int, Enum):
    NOP = 0
    BRANCH = autoshift()  # Команда ветвления?

    # Вентили
    latchTOS = autoshift()
    latchPC = autoshift()
    latchAR = autoshift()

    # Операции со стеком
    dsPUSH = autoshift()
    dsPOP = autoshift()


    #ALU
    aluADD = autoshift()
    aluSUB = autoshift()
    aluMUL = autoshift()
    aluDIV = autoshift()
    aluMOD = autoshift()
    aluINC = autoshift()
    aluDEC = autoshift()

    DIRECT = autoshift()  # Прямая загрузка аргумента
    HLT = autoshift()



def write_program(filename, program):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(
            re.sub(r'(\{.*?\},)', r'\1\n', json.dumps(program))
        )

def read_program(filename):
    with open(filename, "r", encoding="utf-8") as file:
        program = json.loads(file.read())
    for instr in program["code"]:
        instr["opcode"] = Opcode(instr["opcode"])
    return program