from copy import deepcopy

from brilt.cli import find_preds


def find_doms(cfg):
    dom = dict()
    for vertex in cfg: dom[vertex] = set(cfg.keys())
    iterations = 0
    while True:
        iterations += 1
        old_dom = dom.copy()
        for vertex in cfg:
            pred_doms = [dom[p] for p in find_preds(vertex, cfg)]
            dom[vertex] = {vertex}
            if len(pred_doms) > 0:
                dom[vertex] = dom[vertex].union(set.intersection(*pred_doms))
        if old_dom == dom:
            break
    return dom


def gen_dom_tree(cfg, doms):
    dom_tree = dict()
    for v in cfg: dom_tree[v] = set()

    strict_doms = deepcopy(doms)
    for v in strict_doms: strict_doms[v].remove(v)

    for a in cfg:
        a_dominates = set()
        for v in doms:
            if a in doms[v] and a != v: a_dominates.add(v)

        for b in a_dominates:
            imm_doms = True
            for s in strict_doms[b]:
                if a in strict_doms[s]:
                    imm_doms = False
                    break
            if imm_doms: dom_tree[a].add(b)

    return dom_tree
