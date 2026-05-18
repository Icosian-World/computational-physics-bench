# Ultrawalk Endpoint

Build a simulator and analysis pipeline for a one-dimensional discrete-time
quantum walk with hierarchical barriers and sparse phase disorder. Your final
goal is to estimate the maximal-disorder endpoint `epsilon_star` separating
localized and transporting behavior.

## Physics Model

The state at site `x` and time `t` is a two-component wavefunction
`psi[x] = [psi_A[x], psi_B[x]]`.

Each time step has two stages:

1. Apply the site coin to the two-component wavefunction at every site.
2. Shift the post-coin `A` component one site to the right and the post-coin
   `B` component one site to the left.

The origin has the identity coin, but it is still shifted after the coin stage:
`A(0)` moves to `x = 1` and `B(0)` moves to `x = -1`. Do not leave amplitude
parked at the origin after the shift.

For nonzero `x`, the hierarchy level `i(x)` is the largest integer `i >= 0`
such that `2**i` divides `abs(x)`. Equivalently,
`x = 2**i * (2*j + 1)`.

The hierarchy-level coin is

```text
C(theta_i, chi_i) =
[[sin(theta_i),  exp( 1j*chi_i) * cos(theta_i)],
 [exp(-1j*chi_i) * cos(theta_i), -sin(theta_i)]]
```

where

```text
theta_i = (pi / 4) * epsilon**i
chi_i ~ Uniform[-W, W]
```

Draw one random `chi_i` per hierarchy level for each disorder instance. All
sites with the same hierarchy level share that phase. Use `numpy.random.seed`
or an equivalent deterministic NumPy generator so the same `(epsilon, W, seed)`
reproduces the same walk.

The initial condition is

```text
psi_A[0] = 1 / sqrt(2)
psi_B[0] = 1j / sqrt(2)
psi[x != 0] = 0
```

The observable is the root-mean-square displacement
`sigma(t) = sqrt(<x**2> - <x>**2)`.

## Simulator Implementation Hints

For a run to time `t_max`, a lattice radius of `t_max` is sufficient because the
walk moves at most one site per step. A convenient representation is a complex
array of shape `(2 * radius + 1, 2)`, with `origin = radius` and
`x_grid = arange(-radius, radius + 1)`.

One robust update pattern is:

1. Build the coin matrix for each occupied site or hierarchy level.
2. Apply all coins to the current state to obtain a post-coin state.
3. Create a fresh zero state for the next time step.
4. Add post-coin `A` amplitudes to index `+1` and post-coin `B` amplitudes to
   index `-1`.

The level of a nonzero integer can be computed from the largest power of two
dividing `abs(x)`. In Python, `abs_x & -abs_x` is the lowest set bit.

## Finite-Time Scaling

Estimate the inverse walk dimension from the finite-time scaling relation
`sigma(t) ~ t**(1/d_w)`. For this benchmark, use the extrapolation

```text
Y(t) = log(sigma(t)) / log(t)
X(t) = 1 / log(t)
```

Fit `Y = intercept + slope * X` over the available late-time checkpoints. The
intercept as `X -> 0` estimates `1/d_w`. Do not fit `log(sigma)` directly
against `1/log(t)`.

Classify a case as localized when the extrapolated `inv_dw` is close to zero
at maximal disorder. A practical threshold around `0.05` to `0.10` is
reasonable for the public data.

## Input Files

The runtime container provides:

- `/workspace/data/problem.md`: this problem statement.
- `/workspace/data/observations.npz`: public precomputed observations at
  `W = pi/2`.
- `/workspace/data/public_cases.json`: case metadata.
- `/workspace/data/README_observations.md`: schema notes for the NPZ file.

The NPZ contains these arrays:

- `case_id`: integer case identifiers, shape `(n_cases,)`.
- `epsilon`: epsilon value per case, shape `(n_cases,)`.
- `W`: disorder strength per case, shape `(n_cases,)`.
- `t_final`: final simulated time per case, shape `(n_cases,)`.
- `checkpoint_times`: shared sampled times, shape `(n_checkpoints,)`.
- `sigma_checkpoints`: RMS displacement per case and checkpoint,
  shape `(n_cases, n_checkpoints)`.
- `rho_final`: final probability density per case, shape
  `(n_cases, n_sites)`.
- `x_grid`: site coordinates for `rho_final`, shape `(n_sites,)`.

## Required Outputs

Create all outputs in `/workspace/output/`.

### `simulator.py`

Expose:

```python
def simulate(
    epsilon: float,
    W: float,
    seed: int,
    t_max: int,
    sample_times: list[int],
    lattice_radius: int | None = None,
    n_instances: int = 1,
) -> dict:
    ...
```

The returned dictionary must contain:

- `times`: sampled times in the same order requested.
- `sigma`: RMS displacement at those times.
- `rho_final`: final probability density at `t_max`.
- `x_grid`: site coordinates corresponding to `rho_final`.
- `norm_error`: maximum probability-norm drift.

If `n_instances > 1`, average `sigma` and `rho_final` over instances while
keeping the run deterministic from the input seed.

### `analysis.py`

Expose:

```python
def estimate_inv_dw(times, sigma) -> dict:
    ...

def estimate_epsilon_star(observations_path: str) -> dict:
    ...
```

`estimate_inv_dw` should return at least `inv_dw`, `stderr`, and `fit_window`.
`estimate_epsilon_star` should read `observations.npz`, estimate transport for
each public case using `sigma_checkpoints`, and return `epsilon_star`,
`uncertainty`, and a table-like list of per-case results.

### `epsilon_star.json`

Write valid JSON with:

```json
{
  "epsilon_star": 0.0,
  "uncertainty": 0.0,
  "method": "finite-time scaling from simulator-calibrated transport estimates"
}
```

Replace the numeric placeholders with your estimate and uncertainty. The value
should be justified by the provided observations and transport table.

### `transport_table.csv`

Write a CSV with exactly these columns:

```text
case_id,epsilon,W,t_final,inv_dw,stderr,localized,notes
```

Do not put a comment line before the header.

### `visualization.py`

Expose:

```python
def create_diagnostic_plots(output_dir: str = "/workspace/output") -> list[str]:
    ...
```

This script should create at least one PNG diagnostic figure in
`/workspace/output/`, such as `diagnostic_plots.png`. The figure should be
generated from your submitted simulator and/or transport table, not hand-drawn.
Useful panels include:

- probability density snapshots for localized and transporting parameter sets,
- `sigma(t)` checkpoints or simulated scaling curves,
- the finite-time scaling plot `log(sigma)/log(t)` against `1/log(t)`,
- the public-case transport table as `epsilon` versus `inv_dw`.

The visualization is for human physicist audit. The main reward comes from
numerical consistency, so do not substitute a plausible-looking plot for the
required simulator and analysis.

### `notes.md`

Briefly explain your simulator, finite-time scaling fit, endpoint choice, and
any numerical caveats. Also mention how to read your diagnostic plot.
