import os
import sys
import json
import numpy as np

def test_file_existence():
    output_dir = os.environ.get('OUTPUT_DIR', '/workspace/output')
    required_files = [
        'simulator.py',
        'analysis.py',
        'epsilon_star.json',
        'transport_table.csv',
        'notes.md'
    ]
    for f in required_files:
        path = os.path.join(output_dir, f)
        assert os.path.exists(path), f"Required file {f} is missing"
    print("All required files exist.")

def test_simulator_behavior():
    output_dir = os.environ.get('OUTPUT_DIR', '/workspace/output')
    sys.path.insert(0, output_dir)
    import simulator

    sys.path.insert(0, '/workspace/tests')
    try:
        from reference_walk import simulate_walk
    except ImportError:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
        from reference_walk import simulate_walk

    epsilon = 0.5
    W = np.pi / 2
    seed = 42
    t_max = 64
    sample_times = [16, 32, 64]

    res = simulator.simulate(epsilon, W, seed, t_max, sample_times)
    ref_res = simulate_walk(epsilon, W, seed, t_max, sample_times)

    assert res['norm_error'] < 1e-10, f"Norm error too large: {res['norm_error']}"
    np.testing.assert_allclose(res['sigma'], ref_res['sigma'], rtol=1e-5, err_msg="Sigma values do not match reference")
    np.testing.assert_allclose(res['rho_final'], ref_res['rho_final'], rtol=1e-5, atol=1e-8, err_msg="Final density does not match reference")
    print("Simulator behavior matches reference and conserves norm.")

def test_analysis_behavior():
    import analysis
    times = np.array([64, 128, 256, 512])
    sigma = np.exp(0.5 * np.log(times) + 0.1)
    res = analysis.estimate_inv_dw(times, sigma)
    assert 'inv_dw' in res, "Missing inv_dw"
    assert abs(res['inv_dw'] - 0.5) < 1e-5, f"Expected 0.5, got {res['inv_dw']}"
    print("Analysis behavior is valid.")

def test_epsilon_star():
    output_dir = os.environ.get('OUTPUT_DIR', '/workspace/output')
    path = os.path.join(output_dir, 'epsilon_star.json')
    with open(path, 'r') as f:
        data = json.load(f)

    try:
        with open('/workspace/tests/reference_epsilon_star.json', 'r') as f:
            ref = json.load(f)
    except FileNotFoundError:
        with open(os.path.join(os.path.dirname(__file__), 'reference_epsilon_star.json'), 'r') as f:
            ref = json.load(f)

    interval = ref['accepted_interval']
    eps = data['epsilon_star']
    assert interval[0] <= eps <= interval[1], f"epsilon_star {eps} outside accepted interval {interval}"
    print(f"epsilon_star {eps} is within accepted interval {interval}.")

def test_transport_table():
    import csv
    output_dir = os.environ.get('OUTPUT_DIR', '/workspace/output')
    path = os.path.join(output_dir, 'transport_table.csv')
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0, "Transport table is empty"
    required_cols = {'case_id', 'epsilon', 'W', 't_final', 'inv_dw', 'stderr', 'localized', 'notes'}
    assert set(reader.fieldnames) == required_cols, f"Missing columns in transport table: {required_cols - set(reader.fieldnames)}"
    print("Transport table schema is valid.")

if __name__ == '__main__':
    try:
        test_file_existence()
        test_simulator_behavior()
        test_analysis_behavior()
        test_epsilon_star()
        test_transport_table()
        print("All tests passed.")
        sys.exit(0)
    except AssertionError as e:
        print(f"Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
