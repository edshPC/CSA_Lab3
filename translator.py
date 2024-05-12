from isa import *

import sys
import re


def get_meaningful(text):
    # Удаляем из текста лишние отступы и комментарии
    return re.sub(r'^\s+|\s*;.*', '', text, flags=re.MULTILINE)


def translate_stage_1(text: str):
    code = []
    labels = {}

    for token in text.splitlines():
        token = token.strip()
        pc = len(code)

        if token.endswith(":"):  # токен содержит метку
            label = token.strip(":")
            assert label not in labels, f"Redefinition of label: {label}"
            labels[label] = pc
        else:  # токен содержит инструкцию
            mnemonic, *args = re.split(r',? +', token)
            opcode = Opcode(mnemonic)
            assert len(args) == opcode.arg_count, f"Invalid number of args for '{mnemonic}': Expected {opcode.arg_count}, got {len(args)}"
            code.append({"index": pc, "opcode": opcode, "args": args})

    return labels, code


def translate_stage_2(labels, code):
    print(labels)
    for instruction in code:
        args = instruction["args"]
        for i in range(len(args)):
            if re.fullmatch(r'[a-z_]+', args[i], flags=re.IGNORECASE):
                assert args[i] in labels, f"Label not defined: {args[i]}"
                args[i] = labels[args[i]]
            else:
                assert re.fullmatch(r'0x[\da-f]+|\d+', args[i], flags=re.IGNORECASE), f"Unknown type of argument: {args[i]}"
    return code


def translate(text):
    text = get_meaningful(text)  # Удаление комментариев и пустых строк
    labels, code = translate_stage_1(text)
    return translate_stage_2(labels, code)


def main(source, target):
    with open(source, encoding="utf-8") as f:
        source = f.read()

    code = translate(source)
    write_code(target, code)
    print("source LoC:", source.count("\n")+1, "code instr:", len(code))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)
