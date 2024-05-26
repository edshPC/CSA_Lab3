from __future__ import annotations

import logging

from isa import MC, Opcode
from util import Stack, extend_bits


class ALU:
    left = 0
    right = 0


class IOController:
    def __init__(self):
        self.units = {
            1: [],  # IN-unit
            2: [],  # OUT-unit
        }

    def sig_in(self, port: int) -> int:
        if len(self.units[port]) == 0:
            raise EOFError
        symbol = self.units[port].pop(0)
        logging.debug("input: %s", repr(symbol))
        return ord(symbol)

    def sig_out(self, port: int, value: int):
        symbol = chr(value)
        logging.debug("output: %s << %s", repr("".join(self.units[port])), repr(symbol))
        self.units[port].append(symbol)


class DataPath:
    controlunit = None

    def __init__(self, input_buf: list[str], memory_size: int = 2**16, ds_size: int = 2**8, **_):
        self.address_reg = 0
        self.buffer = 0
        self.alu = ALU()

        self.data_stack = Stack(maxlen=ds_size)
        self.memory_size = memory_size
        self.memory = [0] * memory_size
        # Адреса нахождения инструкций в памяти микрокоманд
        self.instruction_micro_address = {}
        self.io_controller = IOController()
        self.input_buf = self.io_controller.units[1]
        self.output_buf = self.io_controller.units[2]
        self.input_buf.extend(input_buf)

    def load_program(self, code: list[dict]):
        for instr in code:
            idx = instr["index"]
            opcode = instr["opcode"]
            args = instr["args"]
            if opcode == Opcode._MEM:
                # Встраивание данных в память
                self.memory[idx : idx + len(args)] = args
                continue
            # Старшие 32 бита - адрес микрокода инструкции, младшие - аргумент
            self.memory[idx] = self.instruction_micro_address.get(opcode, 0) << 32
            for arg in args:  # Применение аргументов в младшие 32 бита
                self.memory[idx] |= arg & 0xFFFFFFFF

    @property
    def flag_zero(self) -> bool:
        return self.data_stack.top == 0

    @property
    def flag_negative(self) -> bool:
        return self.data_stack.top < 0

    def sig_ds_push(self):
        self.data_stack.push(0)

    def sig_ds_pop(self):
        self.data_stack.pop()

    def sig_latch_ar(self):
        if self.controlunit.microcommand & MC.ARmuxPC:
            self.address_reg = self.controlunit.pc
        if self.controlunit.microcommand & MC.ARmuxBUF:
            self.address_reg = self.buffer & 0xFFFFFFFF

    def sig_latch_tos(self):
        self.data_stack.top = self.buffer

    def sig_mem_read(self):
        if not self.address_reg:  # NULL
            return
        if self.address_reg & (1 << 31):  # Прямая загрузка
            self.buffer = extend_bits(self.address_reg)
        else:
            self.buffer = self.memory[self.address_reg % self.memory_size]

    def sig_mem_write(self):
        if not self.address_reg:  # NULL
            return
        assert self.address_reg & (1 << 31) == 0, "Cannot access memory by address, use labels"
        self.memory[self.address_reg % self.memory_size] = self.data_stack.top

    def sig_alu_left(self):
        self.alu.left = self.data_stack.top

    def sig_alu_right(self):
        self.alu.right = self.data_stack.top

    def sig_alu_add(self):
        self.buffer = self.alu.left + self.alu.right

    def sig_alu_sub(self):
        self.buffer = self.alu.left - self.alu.right

    def sig_alu_mul(self):
        self.buffer = self.alu.left * self.alu.right

    def sig_alu_div(self):
        self.buffer = self.alu.left // self.alu.right

    def sig_alu_mod(self):
        self.buffer = self.alu.left % self.alu.right

    def sig_alu_nop(self):
        self.buffer = self.alu.left

    def sig_alu_neg(self):
        self.alu.left *= -1

    def sig_alu_inc(self):
        self.alu.left += 1

    def sig_alu_dec(self):
        self.alu.left -= 1

    def sig_in(self):
        self.buffer = self.io_controller.sig_in(self.buffer & 0xFFFF)

    def sig_out(self):
        self.io_controller.sig_out(self.buffer & 0xFFFF, self.data_stack.top)
