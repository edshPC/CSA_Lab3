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
