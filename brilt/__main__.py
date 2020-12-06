import json
import sys

from brilt.cli import gen_cfg, blockify, lvn_prog
from brilt.dom_utils import find_doms, gen_dom_tree, gen_dom_frontier
from brilt.ssa import to_ssa, from_ssa
from brilt.licm import find_backedges, find_nat_loop_body, licm_prog
from brilt.gen_spec import gen_spec_prog


if __name__ == "__main__":
    #prog = json.loads(sys.stdin.read())
    prog = sys.stdin.read()
    gen_spec_prog(prog, 4)
    #lvn_prog(prog)
    #cfg = gen_cfg(blockify(prog))
    #backedges = find_backedges(cfg, "x0")
    #find_nat_loop_body(cfg, backedges[1])
    #licm_prog(prog)
    #print(gen_dom_tree(gen_cfg(blockify(prog)), find_doms(gen_cfg(blockify(prog)))))
    #print(gen_dom_frontier(gen_cfg(blockify(prog)), "left"))
    #print(from_ssa(json.loads(to_ssa(prog))))

