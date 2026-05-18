# Ultrawalk Endpoint Data Context

This task asks you to reproduce and analyze a one-dimensional discrete-time
quantum walk with hierarchical barriers and sparse phase disorder. The full
task instructions are in `/workspace/instruction.md`; this file summarizes the
data and the main physics conventions.

At each time step, apply the site coin at every site and then shift the
post-coin `A` component to `x + 1` and the post-coin `B` component to `x - 1`.
The origin has the identity coin, but the shift still happens after that
identity coin is applied.

For `x != 0`, the hierarchy level is the exponent of the largest power of two
dividing `abs(x)`. The level-`i` coin uses
`theta_i = (pi / 4) * epsilon**i` and one random phase
`chi_i ~ Uniform[-W, W]` shared by all sites at that level.

Use the RMS displacement `sigma(t)` to estimate inverse walk dimension. The
finite-time extrapolation for this benchmark is

```text
Y(t) = log(sigma(t)) / log(t)
X(t) = 1 / log(t)
```

The intercept of a late-time linear fit of `Y` versus `X` estimates `1/d_w`.

The file `observations.npz` contains public observations at maximal disorder
`W = pi/2`. Its arrays are documented in `README_observations.md`.

Implementation hint: a lattice radius of `t_max` is enough for the simulator,
because the walk moves only one site per step. Apply all coins first, then
perform the conditional shift into a fresh array.

The submitted `visualization.py` should generate human-audit plots from the
submitted simulator, analysis outputs, or transport table. These plots are
diagnostic artifacts; the main verifier reward still comes from numerical
physics checks.
