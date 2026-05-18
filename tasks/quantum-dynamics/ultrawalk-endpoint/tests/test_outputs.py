import csv
import importlib
import json
import os
import sys

import numpy as np


OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "/workspace/output")
LOG_DIR = os.environ.get("VERIFIER_LOG_DIR", "/logs/verifier")
REQUIRED_FILES = [
    "simulator.py",
    "analysis.py",
    "visualization.py",
    "epsilon_star.json",
    "transport_table.csv",
    "notes.md",
]
TABLE_COLUMNS = [
    "case_id",
    "epsilon",
    "W",
    "t_final",
    "inv_dw",
    "stderr",
    "localized",
    "notes",
]


class Rubric:
    def __init__(self):
        self.points = 0.0
        self.max_points = 0.0
        self.details = []

    def add(self, name, earned, possible, message):
        earned = max(0.0, min(float(earned), float(possible)))
        self.points += earned
        self.max_points += possible
        self.details.append(
            {
                "name": name,
                "earned": earned,
                "possible": float(possible),
                "message": message,
            }
        )
        status = "PASS" if abs(earned - possible) < 1e-12 else "PARTIAL" if earned else "FAIL"
        print(f"[{status}] {name}: {earned:.3f}/{possible:.3f} - {message}")

    @property
    def reward(self):
        if self.max_points == 0:
            return 0.0
        return round(self.points / self.max_points, 6)


def load_reference_walk():
    for path in ("/workspace/tests", os.path.dirname(__file__)):
        if path not in sys.path:
            sys.path.insert(0, path)
    from reference_walk import simulate_walk

    return simulate_walk


def load_reference_interval():
    for path in (
        "/workspace/tests/reference_epsilon_star.json",
        os.path.join(os.path.dirname(__file__), "reference_epsilon_star.json"),
    ):
        try:
            with open(path, "r") as f:
                return json.load(f)["accepted_interval"]
        except FileNotFoundError:
            continue
    return [0.7, 0.76]


def observations_path():
    candidates = [
        "/workspace/data/observations.npz",
        os.path.join(os.path.dirname(__file__), "../environment/data/observations.npz"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def reference_transport_rows():
    data = np.load(observations_path())
    times = data["checkpoint_times"]
    rows = []
    for i in range(len(data["case_id"])):
        sigma = data["sigma_checkpoints"][i]
        x = 1.0 / np.log(times)
        y = np.log(sigma) / np.log(times)
        slope, intercept = np.polyfit(x, y, 1)
        rows.append(
            {
                "case_id": int(data["case_id"][i]),
                "epsilon": float(data["epsilon"][i]),
                "W": float(data["W"][i]),
                "t_final": int(data["t_final"][i]),
                "inv_dw": float(intercept),
            }
        )
    return rows


def import_from_output(module_name):
    if OUTPUT_DIR not in sys.path:
        sys.path.insert(0, OUTPUT_DIR)
    if module_name in sys.modules:
        del sys.modules[module_name]
    return importlib.import_module(module_name)


def score_files(rubric):
    present = []
    for name in REQUIRED_FILES:
        if os.path.exists(os.path.join(OUTPUT_DIR, name)):
            present.append(name)
    rubric.add(
        "required output files",
        0.10 * len(present) / len(REQUIRED_FILES),
        0.10,
        f"{len(present)}/{len(REQUIRED_FILES)} files present",
    )
    return set(present)


def score_simulator(rubric, present):
    if "simulator.py" not in present:
        rubric.add("simulator import and physics", 0.0, 0.35, "simulator.py missing")
        return

    earned = 0.0
    messages = []
    try:
        simulator = import_from_output("simulator")
        earned += 0.04
        messages.append("imports")
    except Exception as exc:
        rubric.add("simulator import and physics", 0.0, 0.35, f"import failed: {exc}")
        return

    try:
        res = simulator.simulate(0.5, np.pi / 2, 42, 64, [16, 32, 64])
        required_keys = {"times", "sigma", "rho_final", "x_grid", "norm_error"}
        if required_keys.issubset(res):
            earned += 0.04
            messages.append("returns required keys")
        if float(res.get("norm_error", 1.0)) < 1e-8:
            earned += 0.04
            messages.append("conserves norm")

        ref = load_reference_walk()(0.5, np.pi / 2, 42, 64, [16, 32, 64])
        sigma = np.asarray(res.get("sigma", []), dtype=float)
        rho = np.asarray(res.get("rho_final", []), dtype=float)
        if sigma.shape == ref["sigma"].shape:
            rel = np.max(np.abs(sigma - ref["sigma"]) / np.maximum(1e-12, np.abs(ref["sigma"])))
            sigma_score = max(0.0, 1.0 - rel / 0.25)
            earned += 0.12 * sigma_score
            messages.append(f"sigma relative error {rel:.3g}")
        else:
            messages.append("sigma has wrong shape")
        if rho.shape == ref["rho_final"].shape:
            err = np.max(np.abs(rho - ref["rho_final"]))
            rho_score = max(0.0, 1.0 - err / 0.05)
            earned += 0.11 * rho_score
            messages.append(f"rho max error {err:.3g}")
        else:
            messages.append("rho_final has wrong shape")
    except Exception as exc:
        messages.append(f"runtime failed: {exc}")

    rubric.add("simulator import and physics", earned, 0.35, "; ".join(messages))


def score_analysis(rubric, present):
    if "analysis.py" not in present:
        rubric.add("analysis scaling functions", 0.0, 0.20, "analysis.py missing")
        return

    earned = 0.0
    messages = []
    try:
        analysis = import_from_output("analysis")
        earned += 0.04
        messages.append("imports")
    except Exception as exc:
        rubric.add("analysis scaling functions", 0.0, 0.20, f"import failed: {exc}")
        return

    try:
        times = np.array([64, 128, 256, 512])
        sigma = np.exp(0.5 * np.log(times) + 0.1)
        res = analysis.estimate_inv_dw(times, sigma)
        inv_dw = float(res.get("inv_dw"))
        err = abs(inv_dw - 0.5)
        earned += 0.08 * max(0.0, 1.0 - err / 0.05)
        messages.append(f"power-law inv_dw={inv_dw:.6g}")
    except Exception as exc:
        messages.append(f"estimate_inv_dw failed: {exc}")

    try:
        times = np.array([64, 128, 256, 512])
        sigma = np.exp(0.35 * np.log(times) - 0.7)
        res = analysis.estimate_inv_dw(times, sigma)
        inv_dw = float(res.get("inv_dw"))
        err = abs(inv_dw - 0.35)
        earned += 0.04 * max(0.0, 1.0 - err / 0.05)
        messages.append(f"second exponent inv_dw={inv_dw:.6g}")
    except Exception as exc:
        messages.append(f"second exponent failed: {exc}")

    try:
        res = analysis.estimate_epsilon_star(observations_path())
        if "epsilon_star" in res:
            earned += 0.02
        if any(k in res for k in ("table", "rows", "transport_table", "details")):
            earned += 0.02
        messages.append("estimate_epsilon_star runs")
    except Exception as exc:
        messages.append(f"estimate_epsilon_star failed: {exc}")

    rubric.add("analysis scaling functions", earned, 0.20, "; ".join(messages))


def score_epsilon_star(rubric, present):
    if "epsilon_star.json" not in present:
        rubric.add("epsilon_star endpoint", 0.0, 0.10, "epsilon_star.json missing")
        return

    earned = 0.0
    messages = []
    try:
        with open(os.path.join(OUTPUT_DIR, "epsilon_star.json"), "r") as f:
            data = json.load(f)
        earned += 0.02
        eps = float(data["epsilon_star"])
        interval = load_reference_interval()
        if interval[0] <= eps <= interval[1]:
            earned += 0.06
            messages.append(f"epsilon_star {eps:.6g} inside {interval}")
        else:
            distance = min(abs(eps - interval[0]), abs(eps - interval[1]))
            earned += 0.06 * max(0.0, 1.0 - distance / 0.15)
            messages.append(f"epsilon_star {eps:.6g} outside {interval}")
        if "uncertainty" in data and "method" in data:
            earned += 0.02
    except Exception as exc:
        messages.append(f"invalid endpoint JSON: {exc}")

    rubric.add("epsilon_star endpoint", earned, 0.10, "; ".join(messages))


def parse_bool(value):
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def score_transport_table(rubric, present):
    if "transport_table.csv" not in present:
        rubric.add("transport table", 0.0, 0.20, "transport_table.csv missing")
        return

    earned = 0.0
    messages = []
    try:
        with open(os.path.join(OUTPUT_DIR, "transport_table.csv"), "r", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if reader.fieldnames == TABLE_COLUMNS:
            earned += 0.04
            messages.append("exact header")
        else:
            messages.append(f"header is {reader.fieldnames}")
        if rows:
            earned += 0.02
            messages.append(f"{len(rows)} rows")
        numeric_rows = 0
        localized_values = []
        for row in rows:
            try:
                float(row["epsilon"])
                float(row["W"])
                float(row["t_final"])
                float(row["inv_dw"])
                float(row["stderr"])
                localized_values.append(parse_bool(row["localized"]))
                numeric_rows += 1
            except Exception:
                continue
        if rows:
            earned += 0.03 * numeric_rows / len(rows)
        if any(localized_values) and not all(localized_values):
            earned += 0.02
            messages.append("contains both regimes")
        else:
            messages.append("does not show both regimes")

        ref_by_case = {row["case_id"]: row for row in reference_transport_rows()}
        matched = 0
        inv_scores = []
        metadata_scores = []
        for row in rows:
            try:
                case_id = int(float(row["case_id"]))
            except Exception:
                continue
            if case_id not in ref_by_case:
                continue
            ref = ref_by_case[case_id]
            matched += 1
            # Negative finite-time intercepts are physically interpreted as
            # zero transport, so clipping them in the submitted table is fine.
            inv_err = abs(float(row["inv_dw"]) - max(0.0, ref["inv_dw"]))
            inv_scores.append(max(0.0, 1.0 - inv_err / 0.08))
            meta_err = max(
                abs(float(row["epsilon"]) - ref["epsilon"]) / 0.005,
                abs(float(row["W"]) - ref["W"]) / 0.005,
                abs(float(row["t_final"]) - ref["t_final"]) / 1.0,
            )
            metadata_scores.append(max(0.0, 1.0 - meta_err))
        if ref_by_case:
            earned += 0.03 * min(1.0, matched / len(ref_by_case))
        if inv_scores:
            earned += 0.04 * float(np.mean(inv_scores))
            messages.append(f"mean inv_dw consistency {np.mean(inv_scores):.3f}")
        else:
            messages.append("no rows matched public case_ids")
        if metadata_scores:
            earned += 0.02 * float(np.mean(metadata_scores))
    except Exception as exc:
        messages.append(f"could not parse CSV: {exc}")

    rubric.add("transport table", earned, 0.20, "; ".join(messages))


def score_visualization(rubric, present):
    if "visualization.py" not in present:
        rubric.add("visual diagnostics", 0.0, 0.05, "visualization.py missing")
        return

    earned = 0.0
    messages = []
    before = set(os.listdir(OUTPUT_DIR)) if os.path.isdir(OUTPUT_DIR) else set()
    try:
        visualization = import_from_output("visualization")
        earned += 0.015
        messages.append("imports")
        if hasattr(visualization, "create_diagnostic_plots"):
            paths = visualization.create_diagnostic_plots(OUTPUT_DIR)
            earned += 0.015
            messages.append("create_diagnostic_plots runs")
        else:
            import subprocess

            proc = subprocess.run(
                [sys.executable, os.path.join(OUTPUT_DIR, "visualization.py")],
                cwd=OUTPUT_DIR,
                timeout=60,
                capture_output=True,
                text=True,
            )
            if proc.returncode == 0:
                earned += 0.010
                messages.append("script runs")
            paths = []

        after = set(os.listdir(OUTPUT_DIR)) if os.path.isdir(OUTPUT_DIR) else set()
        candidates = [
            os.path.join(OUTPUT_DIR, name)
            for name in sorted(after | before)
            if name.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))
        ]
        for path in paths or []:
            if isinstance(path, str) and path.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
                candidates.append(path if os.path.isabs(path) else os.path.join(OUTPUT_DIR, path))
        candidates = sorted(set(candidates))
        valid = [path for path in candidates if os.path.exists(path) and os.path.getsize(path) > 1000]
        if valid:
            earned += 0.020
            messages.append(f"{len(valid)} image artifact(s)")
        else:
            messages.append("no nonempty image artifact")
    except Exception as exc:
        messages.append(f"visualization failed: {exc}")

    rubric.add("visual diagnostics", earned, 0.05, "; ".join(messages))


def score_notes(rubric, present):
    if "notes.md" not in present:
        print("[FAIL] notes audit: notes.md missing")
        return
    try:
        with open(os.path.join(OUTPUT_DIR, "notes.md"), "r") as f:
            text = f.read().lower()
        hits = sum(
            token in text
            for token in ("simulator", "scaling", "epsilon", "localized", "transport", "plot")
        )
        print(f"[INFO] notes audit: {hits}/6 expected topics mentioned")
    except Exception as exc:
        print(f"[FAIL] notes audit: notes unreadable: {exc}")


def write_reward(rubric):
    os.makedirs(LOG_DIR, exist_ok=True)
    reward = rubric.reward
    with open(os.path.join(LOG_DIR, "reward.json"), "w") as f:
        json.dump({"reward": reward}, f, indent=2)
    with open(os.path.join(LOG_DIR, "reward.txt"), "w") as f:
        f.write(f"{reward}\n")
    with open(os.path.join(LOG_DIR, "rubric_details.json"), "w") as f:
        json.dump({"reward": reward, "details": rubric.details}, f, indent=2)
    print(f"Final reward: {reward}")


def main():
    rubric = Rubric()
    present = score_files(rubric)
    score_simulator(rubric, present)
    score_analysis(rubric, present)
    score_epsilon_star(rubric, present)
    score_transport_table(rubric, present)
    score_visualization(rubric, present)
    score_notes(rubric, present)
    write_reward(rubric)
    return 0 if rubric.reward >= 0.999 else 1


if __name__ == "__main__":
    sys.exit(main())
