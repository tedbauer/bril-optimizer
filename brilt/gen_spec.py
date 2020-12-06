import subprocess, copy

from brilt.cli import lvn_prog


def stitch(prog, trace)
    """
    Return a new program that is `prog` with `trace` "stitched" in.
    See `gen_spec_prog` for the resulting program format.
    """
    pass


def opt_trace(trace):
    """
    Return a new program that is `trace` with LVN and TDCE applied.
    """
    newtrace = copy.deepcopy(trace)
    lvn_prog(newtrace)
    return newtrace


def gen_trace(prog_filename, args):
    """
    Returns a Bril program that contains the instructions
    executed in the trace generated when `prog_filename` is
    run with `args`.
    """
    pass


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

    spec_prog = stich(prog, otrace)

    cmd = "cat " + prog_filename.strip("\n") + " | bril2json | brili 4"
    subprocess.Popen(cmd, shell=True)
