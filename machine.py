import sys
from datapath import DataPath
from controlunit import ControlUnit
from isa import read_program

def simulation(program, input_tokens, limit=10000, **kwargs):
    datapath = DataPath(input_tokens, **kwargs)
    controluint = ControlUnit(program["start"], datapath, **kwargs)
    datapath.load_program(program["code"])
    try:
        while controluint.tick() < limit:
            pass
        # Превышен лимит
        print("Первышен лимит")
    except EOFError:
        pass
    except SystemExit:
        print("Halted")

def main(program_file, input_file = None):
    program = read_program(program_file)
    input_tokens = []
    if input_file is not None:
        with open(input_file, "r", encoding="utf-8") as file:
            input_tokens = [c for c in file.read()]
    print(input_tokens)

    simulation(program, input_tokens)

if __name__ == "__main__":
    assert 2 <= len(sys.argv) <= 3, "Wrong arguments: machine.py <program_file> [<input_file>]"
    _, program_file, *input_file = sys.argv
    main(program_file, *input_file)
