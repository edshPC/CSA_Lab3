from datapath import *
from isa import *


# Сборка машинных команд через микрокод.
# Каждый элемент - кортеж микрокоманд, каждый элемент кортежа задает 1 такт
instructions: dict[Opcode: tuple[int]] = {
    Opcode.NOP: (MC.EndOfCommand,),
    Opcode.HLT: (MC.HLT,),
    Opcode.PUSH: (MC.latchAR | MC.ARmuxBUF | MC.dsPUSH, MC.memREAD | MC.latchTOS | MC.EndOfCommand),
    Opcode.POP: (MC.latchAR | MC.ARmuxBUF, MC.memWRITE | MC.dsPOP | MC.EndOfCommand),
    Opcode.ADD: (MC.aluRIGHT | MC.dsPOP, MC.aluLEFT | MC.aluADD | MC.latchTOS | MC.EndOfCommand),
    Opcode.SUB: (MC.aluRIGHT | MC.dsPOP, MC.aluLEFT | MC.aluSUB | MC.latchTOS | MC.EndOfCommand),
    Opcode.MUL: (MC.aluRIGHT | MC.dsPOP, MC.aluLEFT | MC.aluMUL | MC.latchTOS | MC.EndOfCommand),
    Opcode.DIV: (MC.aluRIGHT | MC.dsPOP, MC.aluLEFT | MC.aluDIV | MC.latchTOS | MC.EndOfCommand),
    Opcode.MOD: (MC.aluRIGHT | MC.dsPOP, MC.aluLEFT | MC.aluMOD | MC.latchTOS | MC.EndOfCommand),
    Opcode.NEG: (MC.aluLEFT | MC.aluNEG | MC.aluNOP, MC.latchTOS | MC.EndOfCommand),
    Opcode.INC: (MC.aluLEFT | MC.aluINC | MC.aluNOP, MC.latchTOS | MC.EndOfCommand),
    Opcode.DEC: (MC.aluLEFT | MC.aluDEC | MC.aluNOP, MC.latchTOS | MC.EndOfCommand),
    Opcode.DUP: (MC.aluLEFT | MC.aluNOP | MC.dsPUSH, MC.latchTOS | MC.EndOfCommand),
    Opcode.JMP: (MC.BRANCH | MC.EndOfCommand,),
    Opcode.JZ: (MC.BRANCH | MC.jzBRANCH | MC.EndOfCommand,),
    Opcode.JN: (MC.BRANCH | MC.jnBRANCH | MC.EndOfCommand,),
    Opcode.CALL: (MC.BRANCH | MC.pushSTATE | MC.EndOfCommand,),
    Opcode.RET: (MC.BRANCH | MC.popSTATE | MC.EndOfCommand,),

}

class ControlUnit:
    _tick = 0  # Текущий такт
    microcommand_pc = 1  # pc микрокоманд
    microcommand = 0  # Текущая микрокоманда
    # Память микрокоманд (инициализирована с нуля NOP-om и выборкой инструкции)
    microcommand_mem = [
        MC.EndOfCommand, # NOP
        MC.ARmuxPC | MC.latchAR, # Instr fetch
        MC.memREAD | MC.latchMPC
    ]

    def __init__(self, startpos: int, datapath: DataPath, rs_size: int = 2 ** 8):
        self.ret_stack = Stack(maxlen=rs_size)
        self.pc = startpos
        self.datapath = datapath
        datapath.controlunit = self
        for opcode in instructions:  # Идём по списку инструкций
            datapath.instruction_micro_address[opcode] = len(self.microcommand_mem)
            self.microcommand_mem.extend(instructions[opcode])


    def tick(self):
        self.microcommand = self.microcommand_mem[self.microcommand_pc]
        self.microcommand_pc += 1

        if self.microcommand & MC.HLT:
            exit()
        if self.microcommand & MC.EndOfCommand:
            self.microcommand_pc = 1
            self.pc += 1

        if self.microcommand & MC.latchAR:
            self.datapath.sig_latchAR()

        if self.microcommand & MC.aluLEFT:
            self.datapath.sig_aluLEFT()
        if self.microcommand & MC.aluRIGHT:
            self.datapath.sig_aluRIGHT()
        if self.microcommand & MC.aluNEG:
            self.datapath.sig_aluNEG()
        if self.microcommand & MC.aluINC:
            self.datapath.sig_aluINC()
        if self.microcommand & MC.aluDEC:
            self.datapath.sig_aluDEC()
        if self.microcommand & MC.aluADD:
            self.datapath.sig_aluADD()
        if self.microcommand & MC.aluSUB:
            self.datapath.sig_aluSUB()
        if self.microcommand & MC.aluMUL:
            self.datapath.sig_aluMUL()
        if self.microcommand & MC.aluDIV:
            self.datapath.sig_aluDIV()
        if self.microcommand & MC.aluMOD:
            self.datapath.sig_aluMOD()
        if self.microcommand & MC.aluNOP:
            self.datapath.sig_aluNOP()

        if self.microcommand & MC.dsPUSH:
            self.datapath.sig_dsPUSH()

        if self.microcommand & MC.memREAD:
            self.datapath.sig_memREAD()
        if self.microcommand & MC.memWRITE:
            self.datapath.sig_memWRITE()

        if self.microcommand & MC.latchTOS:
            self.datapath.sig_latchTOS()

        if self.microcommand & MC.latchMPC:
            self.sig_latchMPC()

        if self.microcommand & MC.dsPOP:
            self.datapath.sig_dsPOP()

        if self.microcommand & MC.BRANCH:
            self.sig_BRANCH()

        print(self._tick, self.pc, self.datapath.data_stack)
        self._tick += 1
        return self._tick

    def sig_latchMPC(self):
        self.microcommand_pc = self.datapath.buffer >> 32

    def sig_BRANCH(self):
        if not self.datapath.buffer: # NULL
            return
        assert self.datapath.buffer & (1 << 31) == 0, "Cannot access memory by address, use labels"
        if self.microcommand & MC.pushSTATE:
            self.ret_stack.push(self.pc)
        if self.microcommand & MC.popSTATE:
            self.datapath.buffer = self.ret_stack.pop()

        jump = True
        if self.microcommand & MC.jzBRANCH:
            jump &= self.datapath.flag_zero
        if self.microcommand & MC.jnBRANCH:
            jump &= self.datapath.flag_negative
        if jump:
            self.pc = self.datapath.buffer & 0x7FFFFFFF


