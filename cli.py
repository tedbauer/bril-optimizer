import json
import sys
import copy

TERMINATORS = [ "jmp", "br", "ret" ]


def form_blocks(func_body):
    blocks = []
    curr_block = []
    
    for instr in func_body["instrs"]:

        if "op" in instr:
            curr_block.append(instr)

            if instr["op"] in TERMINATORS:
                blocks.append(curr_block)
                curr_block = []

        else:
            blocks.append(curr_block)
            curr_block = [instr]

    blocks.append(curr_block)
    return blocks
                

def dce2(old_prog):
    last_def = dict()
    prog = copy.deepcopy(old_prog)
    for func in prog["functions"]:
        blocks = form_blocks(func)
        for block in blocks:
            last_def = dict()
            to_delete = set()
            for idx, instr in enumerate(block):
                if "args" in instr:
                    for arg in instr["args"]:
                        if arg in last_def:
                            last_def.pop(arg)

                if "dest" in instr and instr["dest"] in last_def:
                    to_delete.add(idx)

                if "dest" in instr:
                    last_def[instr["dest"]] = instr

            for idx in sorted(to_delete, reverse=True):
                del block[idx]

        func["instrs"] = [instr for instr in block for block in blocks]
    return prog


def dce(old_prog):
    prog = copy.deepcopy(old_prog)
    for func in prog["functions"]:
        used = set()
        to_delete = list()

        for instr in func["instrs"]:
            if "args" in instr:
                used.update(instr["args"])

        for idx, instr in enumerate(func["instrs"]):
            if "dest" in instr and instr["dest"] not in used:
                to_delete.append(idx)

        for idx in sorted(to_delete, reverse=True):
            del func["instrs"][idx]
    return prog


def dce1(prog):
    old_prog = copy.deepcopy(prog)
    while dce(old_prog) != old_prog: old_prog = dce(old_prog)
    return old_prog


if __name__ == "__main__":
    prog = json.loads(sys.stdin.read())
    prog2 = dce2(prog)
    print(json.dumps(prog2))
