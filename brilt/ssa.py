from brilt.cli import gen_cfg, blockify, gen_name2block, form_blocks
from brilt.dom_utils import gen_dom_frontier, gen_dom_tree, find_doms

import json

# TODO:
# Convert out of SSA
# handle different types for phi nodes

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
                if instr["op"] != "phi":
                    instr["args"][i] = stack[arg][-1]

        if "dest" in instr:
            old_name = instr["dest"]
            pop_times[old_name] += 1
            new_name = gen_fresh_name(old_name, blocks)
            instr["dest"] = new_name
            stack[old_name].append(new_name)

    for s in cfg[bname]:
        for instr in name2block[s]:
            if "op" in instr and instr["op"] == "phi":
                if len(stack[instr["orig_name"]]) > 0:
                    instr["args"].append(stack[instr["orig_name"]][-1])
                    instr["labels"].append(bname)
                else:
                    instr["undefined"] = True

    for b in dom_tree[bname]:
        rename(b, name2block[b], blocks, stack, dom_tree, cfg, name2block, varz)

    for v in pop_times:
        for _ in range(pop_times[v]): stack[v].pop()


def block_uses(block, v):
    for instr in block:
        if "args" in instr:
            for arg in instr["args"]:
                if arg == v: return True
    return False


def find_type(blocks, v):
    for block in blocks:
        for instr in block:
            if "dest" in instr:
                return instr["type"]
    assert False


def to_ssa(prog):

    func_blocks = []
    for i, func in enumerate(prog["functions"]):
        blocks = form_blocks(func)
        cfg = gen_cfg(blocks)
        name2block = gen_name2block(blocks)

        for bname in name2block:
            if "label" not in name2block[bname][0]:
                name2block[bname].insert(0, {"label": bname})

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
            need_to_add = True
            while need_to_add:
                add_to_defs = set()
                for d in defs[v]:
                    for bname in gen_dom_frontier(cfg, d):
                        has_phi = False
                        for instr in name2block[bname]:
                            if "dest" in instr and instr["dest"] == v and instr["op"] == "phi":
                                has_phi = True
                        if not has_phi: #and block_uses(name2block[bname], v):
                            v_type = find_type(blocks, v)
                            phi_node = {
                                "args": [],
                                "dest": v,
                                "labels": [],
                                "op": "phi",
                                "type": "int",
                                "orig_name": v,
                                "undefined": False
                            }
                            name2block[bname].insert(1, phi_node)
                            if bname not in defs[v]: add_to_defs.add(bname)
                if len(add_to_defs) == 0: need_to_add = False
                else: defs[v] = defs[v].union(add_to_defs)

        stack = dict()
        for v in varz: stack[v] = []
        if "args" in prog["functions"][i]:
            for arg in prog["functions"][i]["args"]:
                stack[arg["name"]] = [arg["name"]]
        rename(list(name2block)[0], name2block[list(name2block)[0]], blocks, stack, dom_tree, cfg, name2block, varz)

        for i, block in enumerate(blocks):
            orig = block
            result = list(filter(lambda i: not ("op" in i and i["op"] == "phi" and i["undefined"]), block))
            blocks[i] = result

        for bname in name2block:
            for instr in name2block[bname]:
                if "phi" in instr:
                    del name2block[bname]["orig_name"]
                    del name2block[bname]["undefined"]

        func_blocks.append(blocks)

    for i, func in enumerate(prog["functions"]):
        func["instrs"] = [instr for block in func_blocks[i] for instr in block]

    return json.dumps(prog)

