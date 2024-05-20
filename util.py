from collections import deque

class Stack(deque):
    def push(self, x):
        assert self.size() < self.maxlen, "StackOverflow"
        self.append(x)

    @property
    def top(self):
        return self[-1]

    @top.setter
    def top(self, value):
        self[-1] = value

    def size(self):
        return len(self)

# Расширяет 31-битное число, если отрицательно
def extend_bits(num_31bit: int) -> int:
    num_31bit &= 0x7FFFFFFF
    if num_31bit & 0x40000000:
        return -(-num_31bit & 0x3FFFFFFF)
    return num_31bit
