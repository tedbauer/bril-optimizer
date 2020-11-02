import json
import sys
import copy
import collections

TERMINATORS = [ "jmp", "br", "ret" ]


def find_preds(bname, cfg):
    preds = []
    for name in cfg:
        if bname in cfg[name]:
            preds.append(name)
    return preds


def reaching_defs(blocks, cfg):

    name2def = dict()

    # TODO: stick this in a function
    name2block = collections.OrderedDict()
    for block in blocks:
        inames = []
        if 'label' in block[0]:
            bname = block[0]['label']
        else:
            bname = gen_fresh_block_name(name2block)

        c = 0
        for instr in block:
            if "label" not in instr:
                iname = bname + "i" + str(c)
                name2def[iname] = instr
                inames.append(iname)
                c += 1

        name2block[bname] = inames

    in_ = {list(name2block)[0]: set()}
    out = dict()
    for name in name2block: out[name] = set()

    worklist = list(name2block.keys())
    while worklist:
        s = set()
        bname = worklist.pop()
        for pred in find_preds(bname, cfg):
            s = s.union(out[pred])
        in_[bname] = s

        new_defs = set(name2block[bname])
        vars_written_to = []
        for i in new_defs:
            if "dest" in name2def[i]:
                vars_written_to.append(name2def[i]["dest"])

        kills = set()
        for i in in_[bname]:
            if "dest" in name2def[i] and name2def[i]["dest"] in vars_written_to:
                kills.add(i)

        old_out = out.copy()
        out[bname] = new_defs.union(in_[bname].difference(kills))
        if out != old_out:
            worklist += cfg[bname]

    return out, name2def


def gen_fresh_block_name(m):
    c = 0
    name = "x" + str(c)
    while name in m: c += 1
    return name


def gen_name2block(blocks):
    name2block = collections.OrderedDict()
    for block in blocks:
        if 'label' in block[0]:
            name2block[block[0]['label']] = block
        else:
            name2block[gen_fresh_block_name(name2block)] = block
    return name2block


def gen_cfg(blocks):
    name2block = collections.OrderedDict()

    for block in blocks:
        if 'label' in block[0]:
            name2block[block[0]['label']] = block
        else:
            name2block[gen_fresh_block_name(name2block)] = block

    cfg = dict()
    for i, name in enumerate(name2block):
        block = name2block[name]
        if "op" in block[-1] and block[-1]["op"] in {"jmp", "br"}:
            cfg[name] = block[-1]["labels"]
        elif "op" in block[-1] and block[-1]["op"] == "ret":
            cfg[name] = []
        else:
            if i < len(name2block) - 1:
                cfg[name] = [list(name2block.keys())[i+1]]
            else:
                cfg[name] = []
    
    return cfg


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
            if len(curr_block) > 0:
                blocks.append(curr_block)
            curr_block = [instr]

    if len(curr_block) > 0: blocks.append(curr_block)
    return blocks
                

def overwritten_later(dest, start, block):
    for instr in block[start+1:]:
        if "dest" in instr:
            if instr["dest"] == dest:
                return True
    return False


def used(var, block):
    for instr in block:
        if "dest" in instr:
            if instr["dest"] == var:
                return True
    return False


def gen_fresh_name(prefix, block):
    i = 0
    while used(prefix + str(i), block): i += 1
    return prefix + str(i)


def lvn_block(block):
    table = collections.OrderedDict()
    var2num = dict()

    for idx, instr in enumerate(block):
        if "op" in instr and instr["op"] == "const":
            value = tuple(["const", str(instr["value"])])
            table[value] = instr["dest"]
            var2num[instr["dest"]] = list(table).index(value)
        if "args" in instr:
            # If there are unrecognized args, create entries for them
            for arg in instr["args"]:
                if arg not in var2num:
                    v = tuple(["___value___", arg])
                    table[v] = arg
                    var2num[arg] = list(table).index(v)

            value_list = [instr["op"]]
            value_list += [var2num[arg] for arg in instr["args"]]
            if instr["op"] == "call":
                value_list += instr["funcs"]
            value = tuple(value_list)

            if "dest" in instr:
                old_name = instr["dest"]
            else:
                old_name = None # never will be used

            if value in table:
                instr["op"] = "id"
                instr["args"] = [table[value]]
            else:
                if "dest" in instr:
                    if overwritten_later(instr["dest"], idx, block):
                        instr["dest"] = gen_fresh_name("x", block)
                    table[value] = instr["dest"]
                if instr["op"] != "const":
                    for i, arg in enumerate(instr["args"]):
                        instr["args"][i] = table[list(table)[var2num[arg]]]

            if "dest" in instr:
                num = list(table).index(value)
                var2num[old_name] = num


def lvn(prog):
    for func in prog["functions"]:
        blocks = form_blocks(func)

        for block in blocks:
            lvn_block(block)

        func["instrs"] = [instr for block in blocks for instr in block]


def tdce(old_prog):
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

        func["instrs"] = [instr for block in blocks for instr in block]
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


def dce2(prog):
    old_prog = copy.deepcopy(prog)
    while tdce(old_prog) != old_prog: old_prog = tdce(old_prog)
    return old_prog


def blockify(prog):
    blocks = []
    for func in prog["functions"]:
        blocks += form_blocks(func)
    return blocks


if __name__ == "__main__":
    prog = json.loads(sys.stdin.read())
    """

    if sys.argv[1] == "lvn":
        lvn(prog)
        print(json.dumps(dce1(dce2(prog))))
    elif sys.argv[1] == "reachingdefs":
        blocks = []
        for func in prog["functions"]:
            blocks += form_blocks(func)

        reaching_defs(blocks, gen_cfg(blocks))
    """
