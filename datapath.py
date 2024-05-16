from util import *
from isa import *

class ALU:
    left = 0
    right = 0

class DataPath:
    instruction_micro_address = {}  # Адрес нахождения инструкций в памяти микрокоманд
    address_reg = 0
    buffer = 0
    output_buf = []
    alu = ALU()
    controlunit = None

    def __init__(self, input_buf: list, memory_size: int = 2 ** 16, ds_size: int = 2 ** 10):
        self.data_stack = Stack(maxlen=ds_size)
        self.memory_size = memory_size
        self.memory = [0] * memory_size
        self.input_buf = input_buf

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
            self.memory[idx] |= self.instruction_micro_address.get(opcode, 0) << 32
            print(self.memory[idx])
            if len(args) == 1: # Есть аргумент
                # Старший бит показывает прямую загрузку аргумента вместо обращения к памяти
                if type(args[0]) == int: # Аргумент - адрес
                    self.memory[idx] |= args[0]
                else: # Аргумент - прямая загрузка
                    self.memory[idx] |= (1 << 31) | (int(args[0], 0) & 0x7FFFFFFF)

    def sig_dsPUSH(self):
        self.data_stack.push(0)
    def sig_dsPOP(self):
        self.data_stack.pop()

    def sig_latchAR(self):
        if self.controlunit.microcommand & MC.ARmuxPC:
            self.address_reg = self.controlunit.pc
        if self.controlunit.microcommand & MC.ARmuxBUF:
            self.address_reg = self.buffer & 0xFFFFFFFF
        if self.controlunit.microcommand & MC.ARmuxTOS:
            self.address_reg = self.data_stack.top
    def sig_latchTOS(self):
        self.data_stack.top = self.buffer

    def sig_memREAD(self):
        if self.address_reg & (1 << 31): # Прямая загрузка
            self.buffer = self.address_reg & 0x7FFFFFFF
        else:
            self.buffer = self.memory[self.address_reg]

    def sig_memWRITE(self):
        self.memory[self.address_reg] = self.data_stack.top


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
    def sig_aluINC(self):
        self.alu.left += 1
        self.alu.right += 1
    def sig_aluDEC(self):
        self.alu.left -= 1
        self.alu.right -= 1


