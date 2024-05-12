from collections import deque

class Stack(deque):
    def push(self, x):
        self.append(x)

    def top(self):
        return self[-1]

    def size(self):
        return len(self)
