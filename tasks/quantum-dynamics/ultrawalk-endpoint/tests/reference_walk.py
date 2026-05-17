import numpy as np

def simulate_walk(epsilon, W, seed, t_max, sample_times, lattice_radius=None):
    if lattice_radius is None:
        lattice_radius = t_max
    num_levels = int(np.log2(max(1, lattice_radius))) + 2
    np.random.seed(seed)
    chi = np.random.uniform(-W, W, size=num_levels)
    theta = (np.pi / 4.0) * (epsilon ** np.arange(num_levels))
    C = np.zeros((num_levels, 2, 2), dtype=complex)
    C[:, 0, 0] = np.sin(theta)
    C[:, 0, 1] = np.exp(1j * chi) * np.cos(theta)
    C[:, 1, 0] = np.exp(-1j * chi) * np.cos(theta)
    C[:, 1, 1] = -np.sin(theta)

    size = 2 * lattice_radius + 1
    origin = lattice_radius
    x_grid = np.arange(-lattice_radius, lattice_radius + 1)

    levels = np.zeros(size, dtype=int)
    mask = (x_grid != 0)
    levels[mask] = np.log2(x_grid[mask] & -x_grid[mask]).astype(int)
    levels[~mask] = -1

    psi = np.zeros((size, 2), dtype=complex)
    psi[origin, 0] = 1.0 / np.sqrt(2)
    psi[origin, 1] = 1j / np.sqrt(2)

    C_lattice = np.zeros((size, 2, 2), dtype=complex)
    C_lattice[origin, 0, 0] = 1.0
    C_lattice[origin, 1, 1] = 1.0
    valid = (levels >= 0)
    C_lattice[valid] = C[levels[valid]]

    times_set = set(sample_times)
    sigma_vals = []
    sampled_times = []
    max_norm_error = 0.0

    for t in range(1, t_max + 1):
        active_min = max(0, origin - (t - 1))
        active_max = min(size, origin + (t - 1) + 1)
        psi_act = psi[active_min:active_max]
        C_act = C_lattice[active_min:active_max]
        psi_coined = np.einsum('iab,ib->ia', C_act, psi_act)
        psi_new = np.zeros_like(psi)
        if active_min + 1 < size:
            psi_new[active_min+1:active_max+1, 0] = psi_coined[:, 0]
        if active_max - 1 > 0:
            psi_new[active_min-1:active_max-1, 1] = psi_coined[:, 1]
        psi = psi_new

        if t in times_set:
            rho = np.abs(psi[:, 0])**2 + np.abs(psi[:, 1])**2
            norm = np.sum(rho)
            max_norm_error = max(max_norm_error, abs(1.0 - norm))
            mean_x = np.sum(x_grid * rho)
            mean_x2 = np.sum(x_grid**2 * rho)
            sigma = np.sqrt(max(0.0, mean_x2 - mean_x**2))
            sampled_times.append(t)
            sigma_vals.append(sigma)

    rho_final = np.abs(psi[:, 0])**2 + np.abs(psi[:, 1])**2
    return {
        'times': np.array(sampled_times),
        'sigma': np.array(sigma_vals),
        'rho_final': rho_final,
        'x_grid': x_grid,
        'norm_error': float(max_norm_error)
    }
