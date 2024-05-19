from isa import *

import sys
import re


def get_meaningful(text: str) -> str:
    # Удаляем из текста лишние отступы и комментарии
    return re.sub(r'^\s+|\s*;.*', '', text, flags=re.MULTILINE)


def translate_stage_1(text: str) -> tuple[dict, list[dict]]:
    code = []
    labels = {}
    pc = 1

    for token in text.splitlines():
        token = token.strip()
        if len(token) == 0:
            continue
        if token.endswith(":"):  # токен содержит метку
            label = token.strip(":")
            assert label not in labels, f"Redefinition of label: {label}"
            labels[label] = pc
        else:  # токен содержит инструкцию
            mnemonic, *args = re.findall(r'(?:"[^"]*"|[^,\s])+', token) # разделение по пробелу не в кавычках
            opcode = Opcode(mnemonic.lower())
            a, b = opcode.arg_count
            assert a <= len(args) <= b, f"Invalid number of args for '{mnemonic}': Expected [{a};{b}], got {len(args)}"

            pc_diff = 1
            if opcode == Opcode.WORD or opcode == Opcode.DB: # Команда сохранения константы
                output = []
                for arg in args:
                    if re.fullmatch(r'".*"', arg):
                        # Строку сохраняем посимвольно
                        output.extend(ord(x) for x in arg.strip('"'))
                    elif re.fullmatch(r'0x[\da-fA-F]+|-?\d+', arg):
                        # Численный литерал
                        output.append(int(arg, 0))
                    else: # Метка
                        output.append(arg)
                args = output
                opcode = Opcode._MEM
                pc_diff = len(output)
            elif opcode == Opcode.RESW:
                pc_diff = int(args[0], 0)
                assert pc_diff > 0, "Cannot reserve negative space"
                args = []
                opcode = Opcode._MEM

            code.append({"index": pc, "opcode": opcode, "args": args})
            pc += pc_diff
    code.append({"index": pc, "opcode": Opcode.HLT, "args": []}) # HLT в конце программы
    return labels, code


def translate_stage_2(labels: dict[str, int], code: list[dict]) -> tuple[int, list[dict]]:
    assert "_start" in labels, "Can't find '_start' label"
    startpos = labels["_start"]
    for instruction in code:
        args = instruction["args"]
        for i in range(len(args)):
            if isinstance(args[i], int):
                continue

            if re.fullmatch(r'[a-zA-Z_]+', args[i]):
                # Если это метка
                assert args[i] in labels, f"Label not defined: {args[i]}"
                args[i] = labels[args[i]]
            else:
                # Если это литерал - 31-й бит показывает прямую загрузку аргумента вместо обращения к памяти
                assert re.fullmatch(r'0x[\da-fA-F]+|-?\d+', args[i]), f"Unknown type of argument: {args[i]}"
                args[i] = (1 << 31) | (int(args[i], 0) & 0x7FFFFFFF)


    return startpos, code


def translate(text: str) -> dict:
    text = get_meaningful(text)  # Удаление комментариев и пустых строк
    labels, code = translate_stage_1(text)
    startpos, code = translate_stage_2(labels, code)
    return {"start": startpos, "code": code}


def main(source: str, target: str):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    program = translate(source)
    write_program(target, program)
    print("source LoC:", source.count("\n")+1, "code instr:", len(program["code"]))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
