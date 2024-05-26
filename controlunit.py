from __future__ import annotations

from datapath import DataPath
from isa import MC, Opcode
from util import Stack

# Сборка машинных команд через микрокод.
# Каждый элемент - кортеж микрокоманд, каждый элемент кортежа задает 1 такт
instructions: dict[Opcode, tuple[int]] = {
    Opcode.NOP: (MC.EndOfCommand,),
    Opcode.HLT: (MC.HLT,),
    Opcode.PUSH: (MC.latch_ar | MC.ARmuxBUF | MC.ds_push, MC.mem_read | MC.latch_tos | MC.EndOfCommand),
    Opcode.POP: (MC.latch_ar | MC.ARmuxBUF, MC.mem_write | MC.ds_pop | MC.EndOfCommand),
    Opcode.PUSH_BY: (MC.alu_left | MC.alu_nop, MC.latch_ar | MC.ARmuxBUF, MC.mem_read | MC.latch_tos | MC.EndOfCommand),
    Opcode.POP_BY: (
        MC.alu_left | MC.alu_nop | MC.ds_pop,
        MC.latch_ar | MC.ARmuxBUF,
        MC.mem_write | MC.ds_pop | MC.EndOfCommand,
    ),
    Opcode.ADD: (MC.alu_right | MC.ds_pop, MC.alu_left | MC.alu_add | MC.latch_tos | MC.EndOfCommand),
    Opcode.SUB: (MC.alu_right | MC.ds_pop, MC.alu_left | MC.alu_sub | MC.latch_tos | MC.EndOfCommand),
    Opcode.MUL: (MC.alu_right | MC.ds_pop, MC.alu_left | MC.alu_mul | MC.latch_tos | MC.EndOfCommand),
    Opcode.DIV: (MC.alu_right | MC.ds_pop, MC.alu_left | MC.alu_div | MC.latch_tos | MC.EndOfCommand),
    Opcode.MOD: (MC.alu_right | MC.ds_pop, MC.alu_left | MC.alu_mod | MC.latch_tos | MC.EndOfCommand),
    Opcode.NEG: (MC.alu_left | MC.alu_neg | MC.alu_nop, MC.latch_tos | MC.EndOfCommand),
    Opcode.INC: (MC.alu_left | MC.alu_inc | MC.alu_nop, MC.latch_tos | MC.EndOfCommand),
    Opcode.DEC: (MC.alu_left | MC.alu_dec | MC.alu_nop, MC.latch_tos | MC.EndOfCommand),
    Opcode.DUP: (MC.alu_left | MC.alu_nop | MC.ds_push, MC.latch_tos | MC.EndOfCommand),
    Opcode.JMP: (MC.BRANCH | MC.EndOfCommand,),
    Opcode.JZ: (MC.BRANCH | MC.jz_branch | MC.EndOfCommand,),
    Opcode.JN: (MC.BRANCH | MC.jn_branch | MC.EndOfCommand,),
    Opcode.CALL: (MC.BRANCH | MC.push_state | MC.EndOfCommand,),
    Opcode.RET: (MC.BRANCH | MC.pop_state | MC.EndOfCommand,),
    Opcode.IN: (MC.ds_push | MC.IN, MC.latch_tos | MC.EndOfCommand),
    Opcode.OUT: (MC.OUT, MC.ds_pop | MC.EndOfCommand),
}

# Инициализация памяти микрокоманд (инициализирована с нуля NOP-om и выборкой инструкции)
microcommand_init: list[int] = [
    MC.EndOfCommand,  # NOP
    MC.ARmuxPC | MC.latch_ar,  # Instr fetch
    MC.mem_read | MC.latch_mpc,
]


class ControlUnit:
    def __init__(self, startpos: int, datapath: DataPath, rs_size: int = 2**8, **_):
        self._tick = 0  # Текущий такт
        self.microcommand_pc = 1  # pc микрокоманд
        self.microcommand = 0  # Текущая микрокоманда

        self.ret_stack = Stack(maxlen=rs_size)
        self.pc = startpos
        self.datapath = datapath
        datapath.controlunit = self
        for opcode in instructions:  # Идём по списку инструкций
            datapath.instruction_micro_address[opcode] = len(microcommand_init)
            microcommand_init.extend(instructions[opcode])
        # Инициализация памяти микрокоманд
        self.microcommand_mem = tuple(microcommand_init)

    def tick(self) -> int:  # noqa: C901 - Complexity низкая, if по порядку нужны для парсинга микрокода
        self.microcommand = self.microcommand_mem[self.microcommand_pc]
        self.microcommand_pc += 1

        if self.microcommand & MC.HLT:
            exit()
        if self.microcommand & MC.EndOfCommand:
            self.microcommand_pc = 1
            self.pc += 1

        if self.microcommand & MC.latch_ar:
            self.datapath.sig_latch_ar()

        if self.microcommand & MC.alu_left:
            self.datapath.sig_alu_left()
        if self.microcommand & MC.alu_right:
            self.datapath.sig_alu_right()
        if self.microcommand & MC.alu_neg:
            self.datapath.sig_alu_neg()
        if self.microcommand & MC.alu_inc:
            self.datapath.sig_alu_inc()
        if self.microcommand & MC.alu_dec:
            self.datapath.sig_alu_dec()
        if self.microcommand & MC.alu_add:
            self.datapath.sig_alu_add()
        if self.microcommand & MC.alu_sub:
            self.datapath.sig_alu_sub()
        if self.microcommand & MC.alu_mul:
            self.datapath.sig_alu_mul()
        if self.microcommand & MC.alu_div:
            self.datapath.sig_alu_div()
        if self.microcommand & MC.alu_mod:
            self.datapath.sig_alu_mod()
        if self.microcommand & MC.alu_nop:
            self.datapath.sig_alu_nop()

        if self.microcommand & MC.ds_push:
            self.datapath.sig_ds_push()

        if self.microcommand & MC.mem_read:
            self.datapath.sig_mem_read()
        if self.microcommand & MC.mem_write:
            self.datapath.sig_mem_write()

        if self.microcommand & MC.IN:
            self.datapath.sig_in()
        if self.microcommand & MC.OUT:
            self.datapath.sig_out()

        if self.microcommand & MC.latch_tos:
            self.datapath.sig_latch_tos()

        if self.microcommand & MC.latch_mpc:
            self.sig_latch_mpc()

        if self.microcommand & MC.ds_pop:
            self.datapath.sig_ds_pop()

        if self.microcommand & MC.BRANCH:
            self.sig_branch()

        self._tick += 1
        return self._tick

    def sig_latch_mpc(self):
        self.microcommand_pc = self.datapath.buffer >> 32

    def sig_branch(self):
        if not self.datapath.buffer:  # NULL
            return
        assert self.datapath.buffer & (1 << 31) == 0, "Cannot access memory by address, use labels"
        if self.microcommand & MC.push_state:
            self.ret_stack.push(self.pc)
        if self.microcommand & MC.pop_state:
            self.datapath.buffer = self.ret_stack.pop()

        jump = True
        if self.microcommand & MC.jz_branch:
            jump &= self.datapath.flag_zero
        if self.microcommand & MC.jn_branch:
            jump &= self.datapath.flag_negative
        if jump:
            self.pc = self.datapath.buffer & 0x7FFFFFFF

    def __repr__(self):
        return f"""\
 Tick: {self._tick} \tmPC: {hex(self.microcommand_pc)} \tPC: {hex(self.pc)} \tBUF: {hex(self.datapath.buffer)} \tAR: {hex(self.datapath.address_reg)} \tMC: {hex(self.microcommand)}
 \tData{self.datapath.data_stack}
 \tRet{self.ret_stack}\
"""
