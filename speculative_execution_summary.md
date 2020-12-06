# Speculative Execution

The speculative execution pass runs the original program with some supplied input,
and then optimizes the program assuming that supplied input. For example, consider
this program:

```
@main(a: int) {

  ten: int = const 10;

  b1: int = const 1;
  b2: int = const 2;
  b3: int = const 3;
  b4: int = const 4;
  b5: int = const 5;

  s: int = const 0;

  cond: bool = lt a ten;

  br cond .then .else;

.then:
  s: int = add b1 s;
  s: int = add b2 s;
  s: int = add b3 s;
  s: int = add b4 s;
  s: int = add b5 s;
  print s;
  jmp .done;

.else:
  print ten;

.done:
  ret;
}
```

If `a` is greater than or equal to 10, then there are many variables that
become dead code, e.g. `b1`, `b2`, etc. So the optimization can transform this program into:

```
@main(a: int) {

.trace:
  speculate;
  ten: int = const 10;
  cond: bool = lt a ten;
  cond2: bool = not cond;
  guard cond2 .orig;
  print ten;
  commit;
  ret;

.orig:
  ten: int = const 10;

  b1: int = const 1;
  b2: int = const 2;
  b3: int = const 3;
  b4: int = const 4;
  b5: int = const 5;

  s: int = const 0;

  cond: bool = lt a ten;

  br cond .then .else;

.then:
  s: int = add b1 s;
  s: int = add b2 s;
  s: int = add b3 s;
  s: int = add b4 s;
  s: int = add b5 s;
  print s;
  jmp .done;

.else:
  print ten;

.done:
  ret;
}
```

The original program takes 11 dynamic instructions to execute, with an input greater
than 10. The transformed program, with the stitched-in trace (that received LVN and
TDCE optimizations), takes 8 dynamic instructions. (The overhead makes the other case
slower, though.)

This assumes that the `brili` interpreter emits traces. If we run the original
program with the input `10`, then the trace looks like this:

```
{"dest":"ten","op":"const","type":"int","value":10}
{"dest":"b1","op":"const","type":"int","value":1}
{"dest":"b2","op":"const","type":"int","value":2}
{"dest":"b3","op":"const","type":"int","value":3}
{"dest":"b4","op":"const","type":"int","value":4}
{"dest":"b5","op":"const","type":"int","value":5}
{"dest":"s","op":"const","type":"int","value":0}
{"args":["a","ten"],"dest":"cond","op":"lt","type":"bool"}
LT
{"args":["cond"],"labels":["then","else"],"op":"br"}
{"args":["ten"],"op":"print"}
10
{"op":"ret"}
```

The optimizer ignores the 10 that gets printed out. Also, the "LT" signals
that the trace took the "LT" path in the following `br` instruction.

Assuming `brili`'s been modified to emit these traces, this can be reproduced with:

```
echo "c1.bril" | python3 -m brilt | bril2txt # show transformed program
```
