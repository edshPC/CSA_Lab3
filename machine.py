import sys
import logging
from datapath import DataPath
from controlunit import ControlUnit
from isa import read_program


def simulation(program: dict, input_tokens: list, tick_limit=10000, **kwargs):
    datapath = DataPath(input_tokens, **kwargs)
    controluint = ControlUnit(program["start"], datapath, **kwargs)
    datapath.load_program(program["code"])
    logging.debug("%s", controluint)
    try:
        while controluint.tick() < tick_limit:
            logging.debug("%s", controluint)
        logging.warning("Tick limit exceeded!")
    except SystemExit:
        logging.info("Program halted")
    except EOFError:
        logging.warning("Try to read empty iuput buffer!")
    except AssertionError as e:
        logging.warning("Program interrupted: %s", e)
    except Exception as e:
        logging.error("Unexpected error: %s", e)

    logging.info("Output: %s", "".join(datapath.output_buf))
    print("".join(datapath.output_buf))
    print("Ticks:", controluint._tick)


def main(program_file: str, input_file: str = None):
    program = read_program(program_file)
    input_tokens = []
    if input_file is not None:
        with open(input_file, "r", encoding="utf-8") as file:
            input_tokens = [c for c in file.read()]

    simulation(program, input_tokens, tick_limit=2**16, memory_size=2**16, ds_size=2**8, rs_size=2**8)


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    logging.basicConfig(format="%(levelname)-7s %(module)s:%(funcName)-13s %(message)s")
    assert 2 <= len(sys.argv) <= 3, "Wrong arguments: machine.py <program_file> [<input_file>]"
    _, program_file, *input_file = sys.argv
    main(program_file, *input_file)
