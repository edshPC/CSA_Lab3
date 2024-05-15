from datapath import *

class ControlUnit:
    _tick = 0  # Текущий такт
    sub_pc = 0  # Под счётчик команд, для счёта внутри микрокодов

    def __init__(self, startpos: int, datapath: DataPath, rs_size: int = 2 ** 8):
        self.ret_stack = Stack(maxlen=rs_size)
        self.pc = startpos
        self.datapath = datapath

    def tick(self):
        self._tick += 1
