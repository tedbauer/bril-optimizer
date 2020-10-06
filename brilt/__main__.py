import json
import sys

from brilt.cli import gen_cfg, blockify
from brilt.dom_utils import find_doms, gen_dom_tree


if __name__ == "__main__":
    prog = json.loads(sys.stdin.read())
    print(gen_dom_tree(gen_cfg(blockify(prog)), find_doms(gen_cfg(blockify(prog)))))
