
def find_backedges(cfg, entry):
    """ 
    Returns a list of backedges [(v1, v2), ... (vn, vm)].
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
    



