import json
import re
from enum import Enum


class Opcode(str, Enum):
    WORD = "word"
    DB = "db"
    RESW = "resw"

    NOP = "nop"
    HLT = "hlt"
    PUSH = "push"
    POP = "pop"
    PUSH_BY = "push_by"
    POP_BY = "pop_by"
    SWAP = "swap"

    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    DIV = "div"
    MOD = "mod"
    NEG = "neg"
    INC = "inc"
    DEC = "dec"
    DUP = "dup"

    JMP = "jmp"
    JZ = "jz"
    JN = "jn"
    CALL = "call"
    RET = "ret"
    IN = "in"
    OUT = "out"

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
            self.JZ: (1, 1),
            self.JN: (1, 1),
            self.CALL: (1, 1),
            self.IN: (1, 1),
            self.OUT: (1, 1),
            self._MEM: (-1, -1),
        }.get(self, (0, 0))

    def __str__(self):
        return str(self.value)


counter = 0


def autoshift():  # 1 << ++counter
    global counter
    counter += 1
    return 1 << counter


# Микрокоды команд
class MC(int, Enum):
    NOP = 0
    EndOfCommand = autoshift()

    # Защелки
    latch_tos = autoshift()
    latch_pc = autoshift()
    latch_mpc = autoshift()
    latch_ar = autoshift()

    # Мультиплексоры
    ARmuxPC = autoshift()
    ARmuxBUF = autoshift()

    # Операции со стеком
    ds_push = autoshift()
    ds_pop = autoshift()
    # Операции с памятью
    mem_read = autoshift()
    mem_write = autoshift()

    # ALU
    alu_left = autoshift()
    alu_right = autoshift()
    alu_add = autoshift()
    alu_sub = autoshift()
    alu_mul = autoshift()
    alu_div = autoshift()
    alu_mod = autoshift()
    alu_nop = autoshift()
    alu_neg = autoshift()
    alu_inc = autoshift()
    alu_dec = autoshift()

    # Ветвление
    BRANCH = autoshift()
    jz_branch = autoshift()
    jn_branch = autoshift()
    push_state = autoshift()
    pop_state = autoshift()

    IN = autoshift()
    OUT = autoshift()
    HLT = autoshift()


assert counter < 64, "Microcommand word is above 64 bit"


def write_program(filename: str, program: dict):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(re.sub(r"(\{.*?},)", r"\1\n", json.dumps(program)))


def read_program(filename: str) -> dict:
    with open(filename, encoding="utf-8") as file:
        program = json.loads(file.read())
    for instr in program["code"]:
        instr["opcode"] = Opcode(instr["opcode"])
    return program
