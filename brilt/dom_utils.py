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


def find_strict_doms(cfg):
    d = find_doms(cfg)
    for v in d: d[v].remove(v)
    return d


def gen_dom_tree(cfg, doms):
    dom_tree = dict()
    for v in cfg: dom_tree[v] = set()

    strict_doms = find_strict_doms(cfg)

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


def gen_dom_frontier(cfg, a):
    doms = find_doms(cfg)
    frontier = set()
    for b in cfg:
        if a in doms[b]:
            continue
        for pred in find_preds(b, cfg):
            if a in doms[pred]:
                frontier.add(b)
    return frontier
