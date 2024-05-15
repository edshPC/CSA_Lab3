from datapath import *
from isa import *

# Сборка машинных команд через микрокод.
# Каждый элемент - кортеж микрокоманд, каждый элемент кортежа задает 1 такт
instructions: dict[Opcode: tuple[int]] = {
    Opcode.NOP: (MC.NOP,),
    Opcode.HLT: (MC.HLT,),
    Opcode.PUSH: (MC.latchAR | MC.dsPUSH,),
    Opcode.POP: (MC.latchAR | MC.dsPOP,),
}

class ControlUnit:
    _tick = 0  # Текущий такт
    microcommand_pc = 0  # pc микрокоманд
    # Память микрокоманд (инициализирована с нуля выборкой инструкции)
    microcommand_mem = [
        MC.ARmuxPC | MC.latchAR,
        MC.memREAD | MC.latchMPC
    ]

    def __init__(self, startpos: int, datapath: DataPath, rs_size: int = 2 ** 8):
        self.ret_stack = Stack(maxlen=rs_size)
        self.pc = startpos
        self.datapath = datapath
        for opcode in instructions:  # Идём по списку инструкций
            datapath.instruction_micro_address[opcode] = len(self.microcommand_mem)
            self.microcommand_mem.extend(instructions[opcode])


    def tick(self):
        self._tick += 1

        return self._tick
