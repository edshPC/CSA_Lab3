import json
from enum import Enum
import re


class Opcode(str, Enum):
    WORD = "word"
    DB = "db"
    RESW = "resw"

    NOP = "nop"
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

            self._MEM: (-1, -1)
        }.get(self, (0, 0))

    def __str__(self):
        return str(self.value)


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(
            re.sub(r'(\{.*?\},)', r'\1\n', json.dumps(code))
        )
