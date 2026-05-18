# Observation File Schema

`observations.npz` stores public long-run observations for the ultrawalk
endpoint task. Load it with:

```python
import numpy as np
data = np.load("/workspace/data/observations.npz")
```

Arrays:

```text
case_id            int,   shape (10,)
epsilon            float, shape (10,)
W                  float, shape (10,)
t_final            float, shape (10,)
checkpoint_times   int,   shape (4,)
sigma_checkpoints  float, shape (10, 4)
rho_final          float, shape (10, 1025)
x_grid             int,   shape (1025,)
```

Each row of `sigma_checkpoints` corresponds to one public case. The same
`checkpoint_times` array applies to every row. Estimate `inv_dw` for each row
using:

```text
Y = log(sigma_checkpoints[row]) / log(checkpoint_times)
X = 1 / log(checkpoint_times)
```

The intercept of a linear fit of `Y` against `X` is the finite-time estimate of
`1/d_w` for that case.
