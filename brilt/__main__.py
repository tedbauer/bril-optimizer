import json
import sys

from brilt.cli import gen_cfg, blockify
from brilt.dom_utils import find_doms, gen_dom_tree, gen_dom_frontier
from brilt.ssa import to_ssa, from_ssa
from brilt.licm import find_backedges, find_nat_loop_body, licm


if __name__ == "__main__":
    prog = json.loads(sys.stdin.read())
    #cfg = gen_cfg(blockify(prog))
    #backedges = find_backedges(cfg, "x0")
    #find_nat_loop_body(cfg, backedges[1])
    licm(prog)
    #print(gen_dom_tree(gen_cfg(blockify(prog)), find_doms(gen_cfg(blockify(prog)))))
    #print(gen_dom_frontier(gen_cfg(blockify(prog)), "left"))
    #print(from_ssa(json.loads(to_ssa(prog))))

