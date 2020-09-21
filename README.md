# Bril Optimizer
## Usage

Run basic LVN followed by TDCE:

    cat <benchmark.json> | python3 cli.py

## Evaluation

Here's a table of results of running the optimizations with [Brench][brenchlink] (`brench benchmark.toml`):

| benchmark | run | result |
| --- | --- | --- |
| quadratic | baseline | 785 |
| quadratic | myopt | 379 |
| orders | baseline | 5352 |
| orders | myopt | 5352 |
| sieve | baseline | 3482 |
| sieve | myopt | 3455 |
| check-primes | baseline | 8468 |
| check-primes | myopt | 7721 |
| sum-sq-diff | baseline | 3039 |
| sum-sq-diff | myopt | 2735 |
| loopfact | baseline | 116 |
| loopfact | myopt | 107 |
| recfact | baseline | 104 |
| recfact | myopt | 96 |
| perfect | baseline | 233 |
| perfect | myopt | 233 |
| digital-root | baseline | 248 |
| digital-root | myopt| 248 |
| ackermann | baseline | 1464231 |
| ackermann | myopt | 1464231 |
| pythagorean\_triple | baseline | 61518 |
| pythagorean\_triple | myopt | 1518 |
| euclid | baseline | 563 |
| euclid | myopt | 502 |
| binary-fmt | baseline | 100 |
| binary-fmt | myopt | 100 |
| mat-mul | baseline | 1990407 |
| mat-mul | myopt | timeout |
| gcd | baseline | 46 |
| gcd | myopt | 46 |
| fib | baseline | 121 |
| fib | myopt | 121 |
| collatz | baseline | 169 |
| collatz | myopt | 169 |
| sum-bits | baseline | 73 |
| sum-bits | myopt | 73 |
| sqrt | baseline | 322 |
| sqrt | myopt | 303 |
| eight-queens | baseline | 1006454 |
| eight-queens | myopt | 959702 |
| fizz-buzz | baseline | 3652 |
| fizz-buzz | myopt | 3252 |

About half of the benchmarks had the same dynamic instruction count after the optimizations, but the other half had reductions between 8 and 46752, most of these values in the teens.

## Notes
- This optimization assumes that there are no values called `___value___`.

[brenchlink]: https://capra.cs.cornell.edu/bril/tools/brench.html
