from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
SUBMISSION = Path(os.environ.get("SUBMISSION_DIR", "/workspace/output"))
PROMPTS = Path(os.environ.get("PROMPTS_FILE", ROOT / "fixtures/prompts.jsonl"))
RUN = ROOT / "run"
OUTPUT = RUN / "motions.npz"
SEED = "1729"


def _load_prompts() -> list[dict]:
    return [json.loads(line) for line in PROMPTS.read_text().splitlines() if line.strip()]


def _run(path: Path) -> bytes:
    RUN.mkdir(exist_ok=True)
    if OUTPUT.exists():
        OUTPUT.unlink()
    subprocess.run(
        [sys.executable, str(path), "--prompts", str(PROMPTS), "--output", str(OUTPUT), "--seed", SEED],
        check=True,
        timeout=300,
    )
    return OUTPUT.read_bytes()


def _arrays() -> tuple[list[dict], dict[str, np.ndarray]]:
    prompts = _load_prompts()
    with np.load(OUTPUT, allow_pickle=False) as archive:
        arrays = {key: archive[key] for key in archive.files}
    return prompts, arrays


def test_generator_exists_and_is_deterministic():
    generator = SUBMISSION / "generate.py"
    assert generator.is_file(), "missing /workspace/output/generate.py"
    first = _run(generator)
    second = _run(generator)
    assert first == second, "fixed prompt file and seed must reproduce byte-identical NPZ"


def test_output_contract():
    prompts, arrays = _arrays()
    assert set(arrays) == {f"{p['motion_id']}/joints" for p in prompts}
    for prompt in prompts:
        joints = arrays[f"{prompt['motion_id']}/joints"]
        assert joints.shape == (prompt["num_frames"], 22, 3)
        assert joints.dtype == np.float32
        assert np.isfinite(joints).all()
        assert np.max(np.abs(joints)) < 20.0, "positions must be global meters"


def test_basic_physical_validity():
    _, arrays = _arrays()
    # Fixture skeleton uses a chain solely to make CI independent of private assets.
    parents = np.array([-1] + list(range(21)))
    for joints in arrays.values():
        lengths = np.linalg.norm(joints[:, 1:] - joints[:, parents[1:]], axis=-1)
        reference = np.median(lengths, axis=0)
        relative = np.abs(lengths - reference) / np.maximum(reference, 1e-5)
        assert np.quantile(relative, 0.99) < 0.03, "severe bone-length drift"
        root_step = np.linalg.norm(np.diff(joints[:, 0], axis=0), axis=-1)
        assert np.max(root_step) < 1.0, "root teleportation"
        assert np.min(joints[..., 1]) > -0.25, "severe ground penetration"


def test_method_metadata():
    method = json.loads((SUBMISSION / "method.json").read_text())
    assert set(method) == {"name", "description", "entrypoint", "model_delta_path"}
    assert method["entrypoint"] == "/workspace/output/generate.py"


def test_private_behavioral_assets_are_external():
    private = ROOT / "private"
    # Production runs mount this directory. Repository CI intentionally does not.
    if not private.exists():
        return
    required = {
        "hidden_prompts.jsonl",
        "hidden_specs.json",
        "reference_features.npz",
        "baseline_hidden_scores.json",
        "thresholds.json",
    }
    assert required.issubset({p.name for p in private.iterdir()})
