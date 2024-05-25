from util import *
from isa import *

class ALU:
    left = 0
    right = 0


class IOController:
    units = {
        1: [], # IN-unit
        2: []  # OUT-unit
    }
    def sig_IN(self, port: int) -> int:
        if len(self.units[port]) == 0:
            raise EOFError
        return ord(self.units[port].pop(0))
    def sig_OUT(self, port: int, value: int):
        self.units[port].append(chr(value))

class DataPath:
    instruction_micro_address = {}  # Адреса нахождения инструкций в памяти микрокоманд
    address_reg = 0
    buffer = 0
    alu = ALU()
    controlunit = None
    io_controller = IOController()
    input_buf = io_controller.units[1]
    output_buf = io_controller.units[2]

    def __init__(self, input_buf: list[str], memory_size: int = 2 ** 16, ds_size: int = 2 ** 8, **_):
        self.data_stack = Stack(maxlen=ds_size)
        self.memory_size = memory_size
        self.memory = [0] * memory_size
        self.input_buf.extend(input_buf)

    def load_program(self, code: list[dict]):
        for instr in code:
            idx = instr["index"]
            opcode = instr["opcode"]
            args = instr["args"]
            if opcode == Opcode._MEM:
                # Встраивание данных в память
                self.memory[idx:idx+len(args)] = args
                continue
            # Старшие 32 бита - адрес микрокода инструкции, младшие - аргумент
            self.memory[idx] = self.instruction_micro_address.get(opcode, 0) << 32
            for arg in args: # Применение аргументов в младшие 32 бита
                self.memory[idx] |= arg & 0xFFFFFFFF

    @property
    def flag_zero(self) -> bool:
        return self.data_stack.top == 0
    @property
    def flag_negative(self) -> bool:
        return self.data_stack.top < 0

    def sig_dsPUSH(self):
        self.data_stack.push(0)
    def sig_dsPOP(self):
        self.data_stack.pop()

    def sig_latchAR(self):
        if self.controlunit.microcommand & MC.ARmuxPC:
            self.address_reg = self.controlunit.pc
        if self.controlunit.microcommand & MC.ARmuxBUF:
            self.address_reg = self.buffer & 0xFFFFFFFF
    def sig_latchTOS(self):
        self.data_stack.top = self.buffer

    def sig_memREAD(self):
        if not self.address_reg: # NULL
            return
        if self.address_reg & (1 << 31): # Прямая загрузка
            self.buffer = extend_bits(self.address_reg)
        else:
            self.buffer = self.memory[self.address_reg % self.memory_size]

    def sig_memWRITE(self):
        if not self.address_reg: # NULL
            return
        assert self.address_reg & (1 << 31) == 0, "Cannot access memory by address, use labels"
        self.memory[self.address_reg % self.memory_size] = self.data_stack.top

    def sig_aluLEFT(self):
        self.alu.left = self.data_stack.top
    def sig_aluRIGHT(self):
        self.alu.right = self.data_stack.top
    def sig_aluADD(self):
        self.buffer = self.alu.left + self.alu.right
    def sig_aluSUB(self):
        self.buffer = self.alu.left - self.alu.right
    def sig_aluMUL(self):
        self.buffer = self.alu.left * self.alu.right
    def sig_aluDIV(self):
        self.buffer = self.alu.left // self.alu.right
    def sig_aluMOD(self):
        self.buffer = self.alu.left % self.alu.right
    def sig_aluNOP(self):
        self.buffer = self.alu.left
    def sig_aluNEG(self):
        self.alu.left *= -1
    def sig_aluINC(self):
        self.alu.left += 1
    def sig_aluDEC(self):
        self.alu.left -= 1

    def sig_IN(self):
        self.buffer = self.io_controller.sig_IN(self.buffer & 0xFFFF)
    def sig_OUT(self):
        self.io_controller.sig_OUT(self.buffer & 0xFFFF, self.data_stack.top)




