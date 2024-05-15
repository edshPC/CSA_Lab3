from util import *
from isa import *



class DataPath:
    instruction_micro_address = {}  # Адрес нахождения инструкций в памяти микрокоманд
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

            # Старшие 32 бита - адрес микрокода инструкции, младшие - аргумент
            self.memory[idx] |= self.instruction_micro_address.get(opcode, 0) << 32
            if len(args) == 1: # Есть аргумент
                # Старший бит показывает прямую загрузку аргумента вместо обращения к памяти
                if type(args[0]) == int: # Аргумент - адрес
                    self.memory[idx] |= args[0]
                else: # Аргумент - прямая загрузка
                    self.memory[idx] |= (1 << 31) | (int(args[0], 0) & 0x8FFFFFFF)




