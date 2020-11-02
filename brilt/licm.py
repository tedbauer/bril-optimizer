from brilt.cli import find_preds, reaching_defs, gen_cfg, blockify

def find_backedges(cfg, entry):
    """ 
    Returns a list of backedges [(v1, v2), ... (vn, vm)].
    The vertice pairs are directed, so (vx, vy) represents
    the edge vx -> vy.
    """
    print(cfg)

    visited = set()
    backedges = []
    
    curr_node = entry
    queue = cfg[entry].copy()
    while queue:
        old_node = curr_node
        curr_node = queue.pop()
        if curr_node not in visited:
            visited.add(curr_node)
            queue += cfg[curr_node]
        else:
            backedges.append((old_node, curr_node))
    
    return backedges


def find_nat_loop_body(cfg, backedge):
    """
    Returns a list of vertices [v1, ..., vn] that
    make up the natural loop body corresponding to
    backedge.
    """

    loop_body = [backedge[1]]
    queue = [backedge[0]]
    while queue:
        curr_node = queue.pop()
        if curr_node not in loop_body:
            loop_body.append(curr_node)
            queue += find_preds(curr_node, cfg)
    
    return set(loop_body)


def find_rdef_block_for(rdefs, name2block, bname, vname):
    """
    Returns the name of the block containing the
    definition of vname that reaches the block
    named bname.
    """

    for inames in rdefs[bname]:
        for iname in inames:
            instr = name2block[iname]
            if "dest" in instr and instr["dest"] == vname:
                return find_block_containing(iname)


def defining_blocks(rdefs, name2def, bname, varname):
    """
    Returns the set of block names of blocks that contains
    the definition of varname that reaches bname.
    """

    defs = set()
    for defname in rdefs[bname]:
        if "dest" in name2def[defname] and name2def[defname]["dest"] == varname:
            defs.add(defname[:defname.index("i")])
    return defs


def gen_fresh_block_name(m):
    c = 0
    name = "x" + str(c)
    while name in m: c += 1
    return name


def find_li_instrs(rdefs, name2def, name2block, loop_body):
    """
    Returns the set of instructions that are loop invariant.
    """
    li_instrs = set()
    num_defs = dict()
    for bname in loop_body:
        for i, instr in enumerate(name2block[bname]):
            if "args" in instr:
                is_li = True
                for arg in instr["args"]:
                    if arg not in num_defs:
                        num_defs[arg] = 0
                    if arg != "op1" and arg != "op2":
                        defblocks = defining_blocks(rdefs, name2def, bname, arg)
                        conda = len(defblocks.intersection(loop_body)) == 0
                        condb = num_defs[arg] == 1 and bname + "i" + str(i) not in li_instrs
                        is_li = is_li and (conda or condb)
                if is_li:
                    li_instrs.add(bname + "i" + str(i))
    return li_instrs


def licm(prog):
    """
    Returns a new prog with all loop-invariant
    instructions moved to loop preheaders.
    """
    blocks = blockify(prog)
    cfg = gen_cfg(blocks)

    backedges = find_backedges(cfg, "x0")
    loop_body = find_nat_loop_body(cfg, backedges[0])

    rdefs, name2def = reaching_defs(blocks, cfg)

    name2block = dict()
    for block in blocks:
        if 'label' in block[0]:
            name2block[block[0]['label']] = block
        else:
            name2block[gen_fresh_block_name(name2block)] = block

    li_instrs = find_li_instrs(rdefs, name2def, name2block, loop_body)
    print(li_instrs)

