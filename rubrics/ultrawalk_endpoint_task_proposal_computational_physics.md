# Task Proposal: Ultrawalk Endpoint

## Benchmark

**Benchmark Name:** Computational Physics  
**Task Family:** Quantum Dynamics  
**Topic Area:** Disordered Quantum Transport  
**Subtopic:** Discrete-Time Quantum Walks, Localization, Finite-Time Scaling

This benchmark is specifically for computational physics tasks. The task family and topic area should distinguish the physics subdomain, not imply that the benchmark spans all sciences.

## Proposed Task Name

`ultrawalk-endpoint`

This name is intentionally short for command-line use while still identifying the scientific target: estimating a critical endpoint in a hierarchical quantum ultra-walk.

## One-Sentence Summary

Given long-time “shadow” observations from a phase-disordered hierarchical discrete-time quantum walk, the agent must reconstruct a physically valid simulator, analyze finite-time transport scaling, and estimate the critical value of \( \epsilon_* \) separating localized and transporting behavior at maximal phase disorder.

## Problem Statement

A one-dimensional discrete-time quantum walk evolves on the integer line with a two-component wavefunction. At each time step, a site-dependent unitary coin is applied, followed by a conditional shift: the upper component moves right and the lower component moves left.

The walk contains two interacting sources of structure:

1. a deterministic hierarchy of increasingly reflective barriers controlled by \( \epsilon \), and  
2. sparse phase disorder controlled by \( W \), where one random phase is drawn per hierarchy level rather than per lattice site.

The agent receives several precomputed long-time probability-density observations and sparse transport checkpoints. These observations are expensive enough that they should not be regenerated from scratch during evaluation. The agent must build a simulator and analysis pipeline capable of estimating the maximal-disorder critical endpoint

\[
\epsilon_* \approx \sup \left\{ \epsilon \in (0,1] : \frac{1}{d_w}(\epsilon, \pi/2) = 0 \right\}.
\]

The final answer is an estimated \( \epsilon_* \), supported by a transport table showing inverse walk-dimension estimates on both sides of the proposed transition.

## Why This Task Belongs in the Computational Physics Benchmark

This task is designed to test a realistic computational-physics workflow:

- implementing a nontrivial quantum dynamics simulator,
- handling site-dependent unitary evolution,
- modeling sub-extensive disorder,
- extracting asymptotic behavior from finite-time data,
- distinguishing localization from very slow transport,
- producing reproducible numerical artifacts under resource constraints.

The difficulty is not the length of code alone. The core challenge is scientific: the agent must connect finite-time observations to an asymptotic localization transition without relying on brute-force simulations that are too expensive for the benchmark.

## Scientific Model

The wavefunction at site \( x \) and time \( t \) is

\[
\psi_{x,t} =
\begin{pmatrix}
\psi^A_{x,t} \\
\psi^B_{x,t}
\end{pmatrix}.
\]

The coin at hierarchy level \( i \) is

\[
C(\theta_i,\chi_i) =
\begin{pmatrix}
\sin \theta_i & e^{i\chi_i}\cos\theta_i \\
e^{-i\chi_i}\cos\theta_i & -\sin\theta_i
\end{pmatrix}.
\]

For \( x \neq 0 \), define the hierarchy level \( i(x) \) by

\[
x = 2^{i(x)}(2j+1).
\]

At the origin, the coin is the identity.

The deterministic barrier backbone is

\[
\theta_i = \frac{\pi}{4}\epsilon^i.
\]

The sparse phase disorder is

\[
\chi_i \sim \mathrm{Uniform}[-W,W],
\]

with one \( \chi_i \) drawn per hierarchy level for each disorder instance. All sites with the same hierarchy level share the same phase.

The initial condition is

\[
\psi_{0,0} =
\frac{1}{\sqrt{2}}
\begin{pmatrix}
1 \\
i
\end{pmatrix},
\qquad
\psi_{x,0}=0 \quad \text{for } x \neq 0.
\]

The observable is the root-mean-square displacement

\[
\sigma(t) =
\sqrt{
\sum_x x^2 \rho(x,t)
-
\left(\sum_x x\rho(x,t)\right)^2
},
\]

where

\[
\rho(x,t) = |\psi^A_{x,t}|^2 + |\psi^B_{x,t}|^2.
\]

The inverse walk dimension is estimated using the finite-time scaling relation

\[
\sigma(t) \sim t^{1/d_w}.
\]

A practical extrapolation uses

\[
Y(t) = \frac{\log \sigma(t)}{\log t},
\qquad
X(t) = \frac{1}{\log t}.
\]

The intercept of a late-time fit of \( Y \) against \( X \) estimates \( 1/d_w \). A value consistent with zero indicates localization; a positive value indicates transport.

## Agent-Visible Inputs

The runtime container should expose the following files:

```text
/workspace/data/problem.md
/workspace/data/observations.npz
/workspace/data/public_cases.json
/workspace/data/README_observations.md
```

### `observations.npz`

The observation archive should contain:

| Key | Shape | Meaning |
|---|---:|---|
| `rho_final` | `(n_cases, n_sites)` | Final-time probability-density profiles |
| `x_grid` | `(n_sites,)` | Integer site coordinates |
| `epsilon` | `(n_cases,)` | Barrier parameter for each public observation |
| `W` | `(n_cases,)` | Disorder strength for each public observation |
| `t_final` | `(n_cases,)` | Final simulation time for each observation |
| `case_id` | `(n_cases,)` | Public case identifiers |
| `sigma_checkpoints` | `(n_cases, n_times)` | RMS-displacement values at selected times |
| `checkpoint_times` | `(n_times,)` | Times corresponding to the checkpointed values |

The public cases should include approximately ten maximal-disorder observations with \( W = \pi/2 \), chosen to bracket the transition region.

## Required Agent Outputs

The agent must create the following files:

```text
/workspace/output/simulator.py
/workspace/output/analysis.py
/workspace/output/visualization.py
/workspace/output/epsilon_star.json
/workspace/output/transport_table.csv
/workspace/output/notes.md
```

### `simulator.py`

Must expose:

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

| Key | Type | Meaning |
|---|---|---|
| `times` | array-like | Sampled times |
| `sigma` | array-like | RMS displacement at sampled times |
| `rho_final` | array-like | Final probability density |
| `x_grid` | array-like | Site coordinates for `rho_final` |
| `norm_error` | float | Maximum probability-norm drift |

### `analysis.py`

Must expose:

```python
def estimate_inv_dw(times, sigma) -> dict:
    ...
```

Expected return keys:

| Key | Type | Meaning |
|---|---|---|
| `inv_dw` | float | Estimated inverse walk dimension |
| `stderr` | float | Uncertainty estimate for the fit |
| `fit_window` | list | Time range used for the estimate |

It must also expose:

```python
def estimate_epsilon_star(observations_path: str) -> dict:
    ...
```

Expected return keys:

| Key | Type | Meaning |
|---|---|---|
| `epsilon_star` | float | Estimated critical endpoint |
| `uncertainty` | float | Estimated uncertainty |
| `table` | list | Transport estimates used to justify the answer |

### `epsilon_star.json`

Required schema:

```json
{
  "epsilon_star": 0.73,
  "uncertainty": 0.03,
  "method": "finite-time scaling from simulator-calibrated transport estimates"
}
```

### `transport_table.csv`

Required columns:

```text
case_id,epsilon,W,t_final,inv_dw,stderr,localized,notes
```

`localized` must be a boolean-like value such as `true` or `false`.

### `visualization.py`

Must expose:

```python
def create_diagnostic_plots(output_dir: str = "/workspace/output") -> list[str]:
    ...
```

The function should create at least one PNG/JPG/GIF diagnostic image showing the model's submitted transport estimates, endpoint choice, or representative density profiles. This is intended for human physicist review. It is deliberately low-weight in the automated reward so that agents cannot pass the task by producing visually plausible but numerically wrong plots.

### `notes.md`

A short human-readable explanation of the approach, including:

- how the simulator was constructed,
- how \( 1/d_w \) was estimated,
- which cases support localization,
- which cases support transport,
- why the reported \( \epsilon_* \) is plausible.

The notes file is not the main grading target, but it improves reviewability.

## Verifier Design

The verifier should grade outcomes, not implementation style. It should execute the submitted simulator and analysis code and inspect generated artifacts.

### Required Checks

1. **Artifact existence and schema**

   The verifier checks that all required output files exist and parse correctly.

2. **Simulator API**

   The verifier imports `/workspace/output/simulator.py` and checks that `simulate(...)` exists with the required behavior.

3. **Analysis API**

   The verifier imports `/workspace/output/analysis.py` and checks that `estimate_inv_dw(...)` and `estimate_epsilon_star(...)` exist.

4. **Quantum validity**

   On small hidden cases, the verifier checks:

   - probability norm remains close to one,
   - returned arrays contain finite values,
   - probability density is nonnegative,
   - the support remains inside the light cone,
   - the simulator behaves sensibly for the clean case \( \epsilon = 1, W = 0 \).

5. **Hidden simulator agreement**

   The submitted simulator is run on several hidden cases with fixed seeds and moderate \( t_{\max} \), such as 256, 512, or 1024. Its RMS-displacement curves are compared to a reference implementation with calibrated tolerances.

6. **Scaling analysis**

   The verifier gives the submitted analysis module synthetic or hidden checkpoint curves and checks whether the estimated inverse walk dimension is within a reasonable tolerance of the reference estimate.

7. **Endpoint estimate**

   The verifier checks that `epsilon_star.json` reports an \( \epsilon_* \) inside a precomputed accepted interval derived from offline higher-resolution runs.

8. **Transport table**

   The table must contain cases on both sides of the proposed transition, finite inverse walk-dimension estimates, finite uncertainty values, and localization labels consistent with the reported endpoint.

9. **Human-audit visualization**

   The verifier imports `visualization.py` or runs it as a script and checks that at least one nonempty image artifact is produced. Plot style is not heavily rewarded; this check exists to make failures more interpretable to maintainers.

## Suggested Scoring

A graded reward is used so incomplete but serious scientific attempts receive partial credit. The Harbor reward is written as a numeric JSON value while detailed diagnostics are written separately.

| Component | Weight |
|---|---:|
| Required output files | 10 |
| Simulator import and hidden-seed physics | 35 |
| Finite-time scaling analysis functions | 20 |
| Endpoint estimate | 10 |
| Transport table consistency | 20 |
| Human-audit visualization | 5 |
| Notes audit | Informational only |

An oracle solution should receive reward `1.0`. Lower scores are meaningful and should be reported on the leaderboard rather than treated as infrastructure failures.

### Hard Fail Conditions

The verifier should fail immediately if:

- `/workspace/output/simulator.py` is missing,
- `/workspace/output/epsilon_star.json` is missing,
- submitted code produces NaN or infinite observables,
- probability norm drift is catastrophically large on small hidden tests,
- required output schemas are not parseable,
- the reported \( \epsilon_* \) is outside a broad physically plausible range.

## Verifiability Assessment

This task is verifiable if the accepted endpoint interval is precomputed offline and the runtime verifier focuses on cheaper behavioral checks.

The verifier should not attempt to reproduce the full long-time phase-boundary calculation during each run. Instead, it should combine:

- small exact simulator checks,
- medium hidden reference comparisons,
- analysis-function checks,
- endpoint-range validation against an offline reference.

This makes the task reliable while preserving the scientific difficulty.

## Well-Specified Assessment

The task can be well-specified because the physical model, input files, required output files, Python APIs, and structured schemas are explicit.

The instructions should avoid over-prescribing the solution method. Agents may use direct simulation, fitted finite-time scaling, reduced-order analysis, or statistical modeling, as long as the final artifacts satisfy the scientific and numerical checks.

The task is not intended to require a particular library or exact code structure.

## Solvability Assessment

The task is solvable by an expert who understands discrete-time quantum walks and finite-size scaling. A reference solution should:

1. implement the hierarchy-index function,
2. implement the unitary coin and conditional shift,
3. simulate moderate cases with fixed seeds,
4. estimate RMS displacement,
5. fit late-time \( Y \) versus \( X \),
6. use the public long-run observations to estimate \( \epsilon_* \),
7. write the required output files.

A good expert solution should be implementable in a few hours if the offline reference interval and public data are already prepared.

## Difficulty Assessment

The task is difficult for good reasons:

- the system is quantum and unitary,
- the disorder is sparse and hierarchy-dependent,
- transport must be inferred from finite-time data,
- near the transition, very slow spreading can mimic localization,
- the agent must combine simulation, analysis, and scientific judgment.

It is not difficult because of arbitrary formatting, hidden corner cases, or excessive brute-force computation.

## Scientific Grounding

This task is grounded in real computational physics practice. Similar workflows arise when researchers:

- implement quantum-walk simulators,
- study localization transitions,
- estimate critical points from finite simulations,
- analyze disordered systems,
- design finite-size scaling studies.

A computational physicist, quantum information researcher, or statistical physicist could plausibly perform this task as part of research.

## Outcome Verification

The task grades the final artifacts:

- simulator behavior,
- transport estimates,
- endpoint estimate,
- structured output files.

It does not require a particular editor, library, fitting method, or implementation style. The process is unconstrained except for mechanistic anti-cheat and schema requirements.

## Proposed Repository Layout

For the Computational Physics benchmark, a physics-first layout could be:

```text
tasks/quantum-dynamics/ultrawalk-endpoint/
  instruction.md
  task.toml

  environment/
    Dockerfile
    generate_public_data.py
    data/
      problem.md
      observations.npz
      public_cases.json
      README_observations.md

  solution/
    solve.sh
    solve.py

  tests/
    test.sh
    test_outputs.py
    reference_walk.py
    hidden_cases.json
    reference_epsilon_star.json
```

If this task is later adapted to Terminal-Bench-Science compatibility, the path can be mirrored into a broader science taxonomy, but the benchmark identity should remain Computational Physics.

## Draft `task.toml` Metadata

```toml
schema_version = "1.0"

[metadata]
author_name = "Richa Sharma"
author_email = "richa.flutr@gmail.com"
category = "computational-physics"
tags = [
  "quantum-dynamics",
  "quantum-walks",
  "localization",
  "finite-size-scaling",
  "disordered-systems",
  "python",
  "numpy"
]
expert_time_estimate_hours = 8
difficulty_explanation = "This task requires implementing a site-dependent unitary quantum walk with sparse hierarchy-level disorder, extracting asymptotic transport behavior from finite-time data, and estimating a localization endpoint under stochastic finite-size effects. The data is synthetic but generated from a realistic research model for disordered quantum transport. In practice, this kind of task would be performed by a computational physicist or quantum information researcher studying localization and transport."
solution_explanation = "The reference solution implements the hierarchical quantum-walk simulator, computes RMS displacement over sampled times, estimates inverse walk dimension by late-time finite-time scaling, combines these estimates with the provided long-run observations, and writes the critical endpoint and transport table."
verification_explanation = "The verifier checks that the submitted simulator and analysis modules import successfully, preserve quantum norm on hidden small cases, agree with reference RMS-displacement curves on fixed-seed hidden medium cases, produce finite inverse walk-dimension estimates, and report an epsilon endpoint inside an interval calibrated from offline higher-resolution reference simulations."

[verifier]
timeout_sec = 600.0

[agent]
timeout_sec = 7200.0

[environment]
build_timeout_sec = 600.0
cpus = 4
memory_mb = 8192
storage_mb = 10240
gpus = 0
allow_internet = false
```

## Risks and Controls

| Risk | Control |
|---|---|
| Full phase-boundary scan is too expensive | Precompute long-run observations and accepted endpoint interval offline |
| Endpoint is statistically noisy | Use calibrated tolerance and hidden behavioral checks, not endpoint alone |
| Agent overfits public cases | Use hidden seeds and hidden parameter cases |
| Simulator is fake but final number is close | Require hidden RMS-displacement agreement and norm conservation |
| Verifier is brittle | Use moderate tolerances and multiple hidden cases |
| Public data leaks answer | Keep accepted interval and hidden references out of runtime image |
| Task becomes formatting-heavy | Keep schemas small and scientific outputs central |

## Acceptance Argument

This proposal should be a strong candidate for the Computational Physics benchmark if implemented carefully.

It is:

- **verifiable**, because the outputs are executable artifacts and numerical estimates;
- **well-specified**, because the model, schemas, and API are explicit;
- **solvable**, because an oracle simulator and analysis pipeline can be implemented compactly;
- **difficult**, because the scientific challenge is finite-time localization inference;
- **scientifically grounded**, because it mirrors real computational-physics workflows;
- **outcome-verified**, because the verifier checks final artifacts and behavior, not a required process.

The main implementation requirement is to keep the verifier lightweight while deriving the accepted \( \epsilon_* \) interval from a trustworthy offline reference calculation.
