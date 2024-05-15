from util import *
from isa import *

# Задание команд через микрокод. Каждый элемент - 1 такт, собирается из микрокоманд.
# Для задания нескольких тактов используется кортеж
instructions: dict[Opcode: tuple[int]] = {
    Opcode.NOP: MC.NOP,
    Opcode.HLT: MC.HLT,
    Opcode.PUSH: MC.latchAR | MC.dsPUSH,
    Opcode.POP: MC.latchAR | MC.dsPOP,
}

class DataPath:
    address_reg = 0
    output_buf = []
    def __init__(self, code: list[dict], input_buf: list, memory_size: int = 2 ** 16, ds_size: int = 2 ** 10):
        self.data_stack = Stack(maxlen=ds_size)
        self.memory_size = memory_size
        self.memory = [0] * memory_size
        self.input_buf = input_buf
        for instr in code:
            idx = instr["index"]
            opcode = instr["opcode"]
            args = instr["args"]
            if opcode == Opcode._MEM:
                # Встраивание данных в память
                self.memory[idx:idx+len(args)] = args
                continue

            # Старшие 32 бита - микрокод, младшие - аргумент
            self.memory[idx] |= instructions.get(opcode, 0)
            if len(args) == 1: # Есть аргумент
                if type(args[0]) == int: # Аргумент - адрес
                    self.memory[idx] |= args[0]
                else: # Аргумент - прямая загрузка
                    self.memory[idx] |= MC.DIRECT | int(args[0], 0)




