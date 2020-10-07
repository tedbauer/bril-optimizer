from brilt.cli import gen_cfg, blockify, gen_name2block
from brilt.dom_utils import gen_dom_frontier, gen_dom_tree, find_doms

import json


def gen_fresh_name(prefix, blocks):
    c = 0
    name = None
    while True:
        c += 1
        name = prefix + "." + str(c)
        found_new_name = True
        for block in blocks:
            for instr in block:
                if "dest" in instr:
                    if name == instr["dest"]:
                        found_new_name = False
        if found_new_name: break
    assert name is not None
    return name


def rename(bname, block, blocks, stack, dom_tree, cfg, name2block, varz):
    pop_times = dict()
    for v in varz: pop_times[v] = 0
    for instr in block:
        if "args" in instr:
            for i, arg in enumerate(instr["args"]):
                if arg != "cond" and instr["op"] != "phi":
                    instr["args"][i] = stack[arg][-1]

        if "dest" in instr:
            old_name = instr["dest"]
            pop_times[old_name] += 1
            new_name = gen_fresh_name(old_name, blocks)
            instr["dest"] = new_name
            stack[old_name].append(new_name)

    # do phi node stuff here
    for s in cfg[bname]:
        for instr in name2block[s]:
            if "op" in instr and instr["op"] == "phi":
                instr["args"].append(stack[instr["orig_name"]][-1])
                instr["labels"].append(bname)

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
                has_phi = False
                for instr in name2block[bname]:
                    if "dest" in instr and instr["dest"] == v and instr["op"] == "phi":
                        has_phi = True
                if not has_phi:
                    phi_node = {
                        "args": [],
                        "dest": v,
                        "labels": [],
                        "op": "phi",
                        "type": "int",
                        "orig_name": v
                    }
                    # todo: if no label in block, insert at pos 1
                    name2block[bname].insert(1, phi_node)

    stack = dict()
    for v in varz: stack[v] = []
    rename("entry", name2block["entry"], blocks, stack, dom_tree, cfg, name2block, varz)

    for bname in name2block:
        for instr in name2block[bname]:
            if "phi" in instr:
                del name2block[bname]["orig_name"]

    new_prog = {
        "functions": [{
            "name": "main",
            "args": [{"name": "cond", "type": "bool"}],
            "instrs": [instr for block in blocks for instr in block]
        }]
    }
    return json.dumps(new_prog)

