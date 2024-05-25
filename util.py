from collections import deque

class Stack(deque):
    def push(self, x):
        assert self.size() < self.maxlen, "StackOverflow"
        self.append(x)

    @property
    def top(self):
        assert self.size() > 0, "StackUnderflow"
        return self[-1]

    @top.setter
    def top(self, value):
        assert self.size() > 0, "StackUnderflow"
        self[-1] = value

    def size(self):
        return len(self)

    def __repr__(self):
        return f'Stack[{", ".join(str(x) for x in self)} <-]'

# Расширяет 31-битное число, если отрицательно
def extend_bits(num_31bit: int) -> int:
    num_31bit &= 0x7FFFFFFF
    if num_31bit & 0x40000000:
        return -(-num_31bit & 0x3FFFFFFF)
    return num_31bit
