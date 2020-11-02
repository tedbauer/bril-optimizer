import json

from brilt.cli import find_preds, reaching_defs, gen_cfg, form_blocks


def find_backedges(cfg, entry):
    """ 
    Returns a list of backedges [(v1, v2), ... (vn, vm)].
    The vertice pairs are directed, so (vx, vy) represents
    the edge vx -> vy.
    """

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


def licm(blocks):
    """
    Mutates blocks, moving all loop-invariant
    instructions to loop preheaders.
    """

    cfg = gen_cfg(blocks)
    start_bname = "x0" if 'label' not in blocks[0] else blocks[0]['label']

    backedges = find_backedges(cfg, start_bname)
    for backedge in backedges:
        loop_body = find_nat_loop_body(cfg, backedge)

        rdefs, name2def = reaching_defs(blocks, cfg)

        ordered_bnames = []
        name2block = dict()
        for block in blocks:
            
            if 'label' in block[0]:
                name = block[0]['label']
            else:
                name = gen_fresh_block_name(name2block)
            
            ordered_bnames.append(name)
            name2block[name] = block

        li_instrs = find_li_instrs(rdefs, name2def, name2block, loop_body)

        entry_bname = backedge[1]
        entry_preds = find_preds(entry_bname, cfg)
        preheader_name = "p0"
        preheader = [{'label': preheader_name}]

        for instr in li_instrs:
            preheader.append(name2def[instr])
            bname = instr[:instr.index("i")]
            i_idx = int(instr[instr.index("i")+1:])
            del name2block[bname][i_idx]

        for pred in entry_preds:
            cfg[pred] = preheader
        
        name2block[preheader_name] = preheader
        cfg[preheader_name] = entry_bname

        cfg[preheader_name] = name2block[entry_bname]
        name2block[entry_bname] = preheader

        blocks.insert(ordered_bnames.index(entry_bname), preheader)
        ordered_bnames.insert(ordered_bnames.index(entry_bname), preheader)


def licm_prog(prog):

    for func in prog["functions"]:
        blocks = form_blocks(func)
        licm(blocks)
        func["instrs"] = [instr for block in blocks for instr in block]
    
    print(json.dumps(prog))