from brilt.cli import gen_cfg, blockify, gen_name2block
from brilt.dom_utils import gen_dom_frontier, gen_dom_tree, find_doms

import json


def gen_fresh_name(prefix, blocks):
    c = 1
    name = prefix + "." + str(c)
    found_new_name = False
    while not found_new_name:
        for block in blocks:
            for instr in block:
                if "dest" in instr:
                    if name == instr["dest"]:
                        c += 1
                        name = prefix + "." + str(c)
                    continue
        found_new_name = True
    return name


def rename(bname, block, blocks, stack, dom_tree, cfg, name2block, varz):
    pop_times = dict()
    for v in varz: pop_times[v] = 0
    for instr in block:
        if "args" in instr:
            for i, arg in enumerate(instr["args"]):
                if arg != "cond":
                    instr["args"][i] = stack[arg][-1]

        if "dest" in instr:
            old_name = instr["dest"]
            pop_times[old_name] += 1
            new_name = gen_fresh_name(old_name, blocks)
            instr["dest"] = new_name
            stack[old_name].append(new_name)

    # do phi node stuff here

    for b in dom_tree[bname]:
        rename(b, name2block[b], blocks, stack, dom_tree, cfg, name2block, varz)

    for v in pop_times:
        for _ in range(pop_times[v]): stack[v].pop()


def to_ssa(prog):
    blocks = blockify(prog)
    cfg = gen_cfg(blocks)
    name2block = gen_name2block(blocks)

    dom_tree = gen_dom_tree(cfg, find_doms(cfg))

    varz = set()
    defs = dict()
    for bname in name2block:
        for instr in name2block[bname]:
            if "dest" in instr:
                varz.add(instr["dest"])
                if instr["dest"] in defs: defs[instr["dest"]].add(bname)
                else: defs[instr["dest"]] = set([bname])

    for v in varz:
        for d in defs[v]:
            for bname in gen_dom_frontier(cfg, d):
                phi_node = {
                    "args": [v, v],
                    "dest": v,
                    "labels": ["left", "right"],
                    "op": "phi",
                    "type": "int",
                }
                # todo: if no label in block, insert at pos 1
                #name2block[bname].insert(1, phi_node)

    stack = dict()
    for v in varz: stack[v] = []
    rename("entry", name2block["entry"], blocks, stack, dom_tree, cfg, name2block, varz)

    new_prog = {
        "functions": [{
            "name": "main",
            "args": [{"name": "cond", "type": "bool"}],
            "instrs": [instr for block in blocks for instr in block]
        }]
    }
    return json.dumps(new_prog)

