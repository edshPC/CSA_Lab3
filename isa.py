import json
from enum import Enum
import re


class Opcode(str, Enum):
    PUSH = "push"

    @property
    def arg_count(self):
        return {
            self.PUSH: 1
        }[self]

    def __str__(self):
        return str(self.value)


def write_code(filename, code):
    with open(filename, "w", encoding="utf-8") as file:
        file.write(
            re.sub(r'(\{.*?\},)', r'\1\n', json.dumps(code))
        )
