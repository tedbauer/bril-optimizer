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
        start = 1 if "label" in name2block[bname][0] else 0
        for i, instr in enumerate(name2block[bname][start:]):
            if "args" in instr:
                is_li = True
                for arg in instr["args"]:
                    if arg not in num_defs:
                        num_defs[arg] = 0
                    #FIXME: something about args are weird here?
                    defblocks = defining_blocks(rdefs, name2def, bname, arg)
                    conda = len(defblocks.intersection(loop_body)) == 0
                    condb = num_defs[arg] == 1 and bname + "i" + str(i) not in li_instrs
                    is_li = is_li and (conda or condb)
                if is_li:
                    li_instrs.add(bname + "i" + str(i))
    return li_instrs


def move_to_preheaders(backedge, cfg, ordered_bnames, blocks, name2def, li_instrs, preheader_name, name2block):
    """
    Mutates blocks and ordered_bnames, inserting a preheader
    block before the entry of the natural loop formed around
    backedge and moving li_instrs into this preheader. (The preheader
    block will be named preheader_name.)
    TODO: remake this dumb function that has 100 arguments
    """

    entry_bname = backedge[1]
    entry_preds = find_preds(entry_bname, cfg)
    preheader = [{'label': preheader_name}]

    #FIXME: multiple deletions can break this
    for instr in li_instrs:
        #print(instr)
        #print(name2def)
        #print(name2block[bname])
        preheader.append(name2def[instr])
        bname = instr[:instr.index("i")]
        i_idx = int(instr[instr.index("i")+1:])
        offset = 1 if "label" in name2block[bname][0] else 0
        del name2block[bname][i_idx+offset]

    for pred in entry_preds:
        cfg[pred] = preheader
    
    name2block[preheader_name] = preheader
    cfg[preheader_name] = entry_bname

    cfg[preheader_name] = name2block[entry_bname]
    name2block[entry_bname] = preheader

    blocks.insert(ordered_bnames.index(entry_bname), preheader)
    ordered_bnames.insert(ordered_bnames.index(entry_bname), preheader)


def licm(blocks):
    """
    Mutates blocks, moving all loop-invariant
    instructions to loop preheaders.
    """

    cfg = gen_cfg(blocks)
    start_bname = "x0" if 'label' not in blocks[0] else blocks[0]['label']

    backedges = find_backedges(cfg, start_bname)
    p = 0
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

        unsafe = set()
        for instr in li_instrs:
            # Check that there's only one definition in the loop body.
            count = 0
            dest = name2def[instr]["dest"]
            for bname in loop_body:
                for other_instr in name2block[bname]:
                    if "dest" in other_instr and other_instr["dest"] == dest:
                        count += 1
            if count > 1:
                unsafe.add(instr)

            # Check that every use in the loop body comes from instr.
            for bname in loop_body:
                for other_instr in name2block[bname]:
                    if "args" in other_instr:
                        for arg in other_instr["args"]:
                            if arg == name2def[instr]["dest"]:
                                defblocks = defining_blocks(rdefs, name2def, bname, arg)

                                # The only defining block should be the block
                                # that instr is in. (Before the move to the preheader.)
                                if defblocks != {instr[:instr.index("i")]}:
                                    unsafe.add(instr)

            # Check that there are no uses after the loop.
            
            # Find exits.
            exits = set()
            for node in cfg:
                if len(set(cfg[node]).difference(loop_body)) > 0:
                    exits.add(node)
            
            for exit_ in exits:
                queue = [exit_]
                visited = set()
                while queue:
                    curr_node = queue.pop()
                    if curr_node not in visited:
                        visited.add(curr_node)
                        for n in cfg[curr_node]:
                            if n not in loop_body: queue.append(n)

                        for i in name2block[curr_node]:
                            if "args" in i and name2def[instr]["dest"] in i["args"]:
                                unsafe.add(instr)



        preheader_name = "p" + str(p)
        p += 1
        move_to_preheaders(
            backedge,
            cfg,
            ordered_bnames,
            blocks,
            name2def,
            li_instrs.difference(unsafe),
            preheader_name,
            name2block
        )

def licm_prog(prog):

    for func in prog["functions"]:
        blocks = form_blocks(func)
        licm(blocks)
        func["instrs"] = [instr for block in blocks for instr in block]
    
    print(json.dumps(prog))