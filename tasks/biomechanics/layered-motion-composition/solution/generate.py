#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def make_motion(num_frames: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    t = np.linspace(0.0, 1.0, num_frames, dtype=np.float32)
    root = np.stack((0.4 * t, 0.95 + 0.04 * np.sin(4 * np.pi * t), np.zeros_like(t)), axis=-1)
    offsets = np.zeros((22, 3), dtype=np.float32)
    offsets[:, 1] = np.arange(22, dtype=np.float32) * 0.025
    phase = rng.uniform(0, 2 * np.pi)
    sway = 0.01 * np.sin(2 * np.pi * t + phase).astype(np.float32)
    joints = root[:, None, :] + offsets[None, :, :]
    joints[:, :, 0] += sway[:, None]
    return joints.astype(np.float32)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompts", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", required=True, type=int)
    args = parser.parse_args()

    prompts = [json.loads(line) for line in Path(args.prompts).read_text().splitlines() if line.strip()]
    arrays = {
        f"{p['motion_id']}/joints": make_motion(int(p["num_frames"]), args.seed + i)
        for i, p in enumerate(prompts)
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(output, **arrays)


if __name__ == "__main__":
    main()
