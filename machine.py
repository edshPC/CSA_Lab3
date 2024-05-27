import argparse
import logging

from controlunit import ControlUnit
from datapath import DataPath
from isa import read_program


def simulation(program: dict, input_tokens: list, ticklim=10000, **kwargs):
    datapath = DataPath(input_tokens, **kwargs)
    controluint = ControlUnit(program["start"], datapath, **kwargs)
    try:
        datapath.load_program(program["code"])
        logging.debug("%s", controluint)
        while controluint.tick() < ticklim:
            logging.debug("%s", controluint)
        logging.warning("Tick limit exceeded!")
    except SystemExit:
        logging.info("Program halted")
    except EOFError:
        logging.warning("Try to read empty input buffer!")
    except AssertionError as e:
        logging.warning("Program interrupted: %s", e)
    except IndexError:
        logging.warning("Not enough memory!")
    except Exception:
        logging.exception("Unexpected error")

    logging.info("Output: %s", "".join(datapath.output_buf))
    print("".join(datapath.output_buf))
    print("Ticks:", controluint._tick)


def main(program_file, input_file=None, **kwargs):
    program = read_program(program_file)
    input_tokens = []
    if input_file is not None:
        with open(input_file, encoding="utf-8") as file:
            input_tokens = [c for c in file.read()]

    simulation(program, input_tokens, **kwargs)


parser = argparse.ArgumentParser()

parser.add_argument("program_file")
parser.add_argument("input_file", nargs="?")
parser.add_argument("-t", "--ticklim", type=int)
parser.add_argument("-m", "--memsize", type=int)
parser.add_argument("-d", "--dsize", type=int)
parser.add_argument("-r", "--rsize", type=int)
parser.add_argument("-l", "--loglevel", default="DEBUG")

if __name__ == "__main__":
    args = parser.parse_args()
    logging.getLogger().setLevel(args.loglevel)
    logging.basicConfig(format="%(levelname)-7s %(module)s:%(funcName)-13s %(message)s")
    kwargs = {k: v for k, v in vars(args).items() if v is not None}
    main(**kwargs)
