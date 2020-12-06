import subprocess
from subprocess import Popen, PIPE
import copy, json

from brilt.cli import lvn_prog


def stitch(prog, trace):
    """
    Return a new program that is `prog` with `trace` "stitched" in.
    See `gen_spec_prog` for the resulting program format.
    """
    prog["functions"][0]["instrs"].insert(0, {"label": "orig"})
    prog["functions"][0]["instrs"].insert(0, {"op": "ret"})
    prog["functions"][0]["instrs"].insert(0, {"op": "commit"})
    for instr in trace["functions"][0]["instrs"][::-1]:
        prog["functions"][0]["instrs"].insert(0, instr)
    prog["functions"][0]["instrs"].insert(0, {"op": "speculate"})
    prog["functions"][0]["instrs"].insert(0, {"label": "trace"})
    return prog


def opt_trace(trace):
    """
    Return a new program that is `trace` with LVN and TDCE applied.
    """
    otrace = lvn_prog(copy.deepcopy(trace))
    return otrace


def gen_trace(prog_filename, args):
    """
    Returns a Bril program that contains the instructions
    executed in the trace generated when `prog_filename` is
    run with `args`.
    """
    cmd = "cat " + prog_filename.strip("\n") + " | bril2json | brili " + " ".join(args)
    instrs = []
    with Popen(cmd, shell=True, stdout=PIPE, universal_newlines=True) as p:
        lines = [l.strip("\n") for l in p.stdout.readlines()]
        for (i, line) in enumerate(lines):
            if line[0] == "{" and "jmp" not in line and "ret" not in line:
                if "br" in line:
                    instr = json.loads(line.strip("\n"))
                    if lines[i-1] == "LT":
                        instrs.append({"op": "not", "args": ["cond"], "dest": "cond2", "type": "bool"})
                    instrs.append({"op": "guard", "args": ["cond2"], "labels": ["orig"]})
                else:
                    instrs.append(json.loads(line.strip("\n")))
    prog = {
      "functions": [
        {
          "name": "main",
          "args": [{"name": "a", "type": "int"}], #FIXME
          "instrs": instrs
        }
      ]
    }
    return prog


def get_prog(prog_filename):
    cmd = "cat " + prog_filename.strip("\n") + " | bril2json"
    result = subprocess.run(cmd, shell=True, stdout=PIPE, universal_newlines=True)
    return json.loads(result.stdout)


def gen_spec_prog(prog_filename, args):
    """
    1. Runs the specified program, and collects a trace. Branches
       of the form `br c .a .b;` are turned into `guard c .b;`.
    2. Optimizes the trace with LVN and dead code elimination.
    3. Creates a new program that looks like this:

    ```
    @main(<orig_args>) {
    .trace:
      speculate;
      <optimized trace>
      commit;

    .orig:
      <orig_program>

    }
    ```

    """

    # echo prog_json and pass it to brili

    trace = gen_trace(prog_filename, args)
    otrace = opt_trace(trace)
    prog = get_prog(prog_filename)
    spec_prog = stitch(prog, otrace)
    return spec_prog

