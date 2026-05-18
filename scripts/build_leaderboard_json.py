#!/usr/bin/env python3
"""Build a frontend-friendly leaderboard JSON artifact.

The exporter combines three telemetry sources:
- direct Responses API run directories with `response.json` and rubric details,
- Harbor job result files,
- Aider logs with approximate `Tokens: ... sent, ... received` lines.

Harbor/Aider token parsing is marked approximate because Aider's text logs are
not an authoritative billing API. Prefer direct Responses usage objects when
they are available.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RUNS_FILE = REPO_ROOT / "config" / "leaderboard_runs.json"
DEFAULT_PRICING_FILE = REPO_ROOT / "config" / "model_pricing.json"
DEFAULT_OUTPUT_FILE = REPO_ROOT / "leaderboard.json"

TOKEN_RE = re.compile(
    r"Tokens:\s+(?P<input>[0-9.]+)\s*(?P<input_unit>k|m)?\s+sent,\s+"
    r"(?P<output>[0-9.]+)\s*(?P<output_unit>k|m)?\s+received",
    re.IGNORECASE,
)


def read_json(path: Path) -> dict[str, Any]:
    with open(path, "r") as f:
        return json.load(f)


def resolve_path(path: str | None) -> Path | None:
    if not path:
        return None
    p = Path(path)
    return p if p.is_absolute() else REPO_ROOT / p


def token_number(value: str, unit: str | None) -> int:
    multiplier = 1
    if unit and unit.lower() == "k":
        multiplier = 1_000
    elif unit and unit.lower() == "m":
        multiplier = 1_000_000
    return int(round(float(value) * multiplier))


def normalize_model_name(model: str | None) -> str | None:
    if not model:
        return None
    return model.split("/")[-1]


def pricing_for_model(pricing_models: dict[str, Any], model: str | None) -> dict[str, Any] | None:
    if not model:
        return None
    candidates = [
        model,
        normalize_model_name(model),
        model.replace("openai/", ""),
        model.replace("azure/", ""),
    ]
    for candidate in candidates:
        if candidate in pricing_models:
            return pricing_models[candidate]
    return None


def estimate_cost(tokens: dict[str, Any], pricing: dict[str, Any] | None) -> float | None:
    if not pricing:
        return None
    input_rate = pricing.get("input_usd_per_million")
    output_rate = pricing.get("output_usd_per_million")
    cached_rate = pricing.get("cached_input_usd_per_million")
    if input_rate is None or output_rate is None:
        return None
    if cached_rate is None:
        cached_rate = input_rate
    if tokens.get("input") is None or tokens.get("output") is None:
        return None
    input_tokens = int(tokens.get("input") or 0)
    cached_tokens = int(tokens.get("cached_input") or 0)
    output_tokens = int(tokens.get("output") or 0)
    uncached = max(0, input_tokens - cached_tokens)
    return (
        uncached * float(input_rate)
        + cached_tokens * float(cached_rate)
        + output_tokens * float(output_rate)
    ) / 1_000_000.0


def parse_aider_tokens(path: Path | None) -> dict[str, Any]:
    if not path or not path.exists():
        return {
            "input": None,
            "cached_input": None,
            "output": None,
            "reasoning": None,
            "total": None,
            "source": "unavailable",
            "approximate": True,
            "turns": 0,
        }
    input_total = 0
    output_total = 0
    turns = 0
    for line in path.read_text(errors="replace").splitlines():
        match = TOKEN_RE.search(line)
        if not match:
            continue
        turns += 1
        input_total += token_number(match.group("input"), match.group("input_unit"))
        output_total += token_number(match.group("output"), match.group("output_unit"))
    if turns == 0:
        return {
            "input": None,
            "cached_input": None,
            "output": None,
            "reasoning": None,
            "total": None,
            "source": "unavailable",
            "approximate": True,
            "turns": 0,
        }
    return {
        "input": input_total,
        "cached_input": 0,
        "output": output_total,
        "reasoning": None,
        "total": input_total + output_total,
        "source": "aider_log",
        "approximate": True,
        "turns": turns,
    }


def response_summary(run_dir: Path) -> dict[str, Any]:
    response = read_json(run_dir / "response.json")
    rubric = read_json(run_dir / "logs" / "rubric_details.json")
    usage = response.get("usage", {})
    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cached_tokens = int(usage.get("input_tokens_details", {}).get("cached_tokens") or 0)
    reasoning_tokens = int(usage.get("output_tokens_details", {}).get("reasoning_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
    duration = None
    if response.get("completed_at") and response.get("created_at"):
        duration = int(response["completed_at"]) - int(response["created_at"])
    return {
        "model": response.get("model"),
        "reward": float(rubric.get("reward") or 0.0),
        "duration_s": duration,
        "tokens": {
            "input": input_tokens,
            "cached_input": cached_tokens,
            "output": output_tokens,
            "reasoning": reasoning_tokens,
            "total": total_tokens,
            "source": "responses_usage",
            "approximate": False,
            "turns": None,
        },
    }


def harbor_summary(result_path: Path, agent_log_path: Path | None) -> dict[str, Any]:
    result = read_json(result_path)
    stats = result.get("stats", {})
    reward = None
    evals = stats.get("evals") or {}
    for eval_result in evals.values():
        if not eval_result.get("n_trials"):
            continue
        metrics = eval_result.get("metrics") or []
        if metrics and metrics[0].get("mean") is not None:
            reward = float(metrics[0]["mean"])
            break
    duration = None
    if result.get("started_at") and result.get("finished_at"):
        try:
            start = datetime.fromisoformat(result["started_at"].replace("Z", "+00:00"))
            finish = datetime.fromisoformat(result["finished_at"].replace("Z", "+00:00"))
            duration = int((finish - start).total_seconds())
        except ValueError:
            duration = None
    tokens = {
        "input": stats.get("n_input_tokens"),
        "cached_input": stats.get("n_cache_tokens"),
        "output": stats.get("n_output_tokens"),
        "reasoning": None,
        "total": None,
        "source": "harbor_result",
        "approximate": False,
        "turns": None,
    }
    if tokens["input"] is None or tokens["output"] is None:
        tokens = parse_aider_tokens(agent_log_path)
    else:
        tokens["total"] = int(tokens["input"] or 0) + int(tokens["output"] or 0)
    return {"reward": reward, "duration_s": duration, "tokens": tokens}


def score_points_per_1k(score_points: float | None, total_tokens: int | None) -> float | None:
    if score_points is None or not total_tokens:
        return None
    return score_points / (total_tokens / 1000.0)


def finite_or_none(value: float | None) -> float | None:
    if value is None:
        return None
    return value if math.isfinite(value) else None


def build_leaderboard(runs_file: Path, pricing_file: Path) -> dict[str, Any]:
    run_config = read_json(runs_file)
    pricing_doc = read_json(pricing_file)
    pricing_models = pricing_doc.get("models", {})
    results = []

    for entry in run_config.get("results", []):
        run_type = entry["run_type"]
        run_path = resolve_path(entry.get("run_path"))
        agent_log_path = resolve_path(entry.get("agent_log_path"))
        measured: dict[str, Any] = {
            "reward": None,
            "duration_s": None,
            "tokens": {
                "input": None,
                "cached_input": None,
                "output": None,
                "reasoning": None,
                "total": None,
                "source": "unavailable",
                "approximate": False,
                "turns": None,
            },
        }

        if run_type == "responses" and run_path and run_path.exists():
            measured = response_summary(run_path)
            if measured.get("model"):
                entry["model"] = measured["model"]
        elif run_type == "harbor" and run_path and run_path.exists():
            measured = harbor_summary(run_path, agent_log_path)
        elif run_type == "catalog":
            measured["tokens"]["source"] = "not_run"

        model = entry.get("model")
        pricing = pricing_for_model(pricing_models, model)
        reward = measured.get("reward")
        score_points = 100.0 * reward if reward is not None else None
        cost = estimate_cost(measured["tokens"], pricing)
        total_tokens = measured["tokens"].get("total")
        score_per_dollar = score_points / cost if score_points is not None and cost else None

        results.append(
            {
                "id": entry["id"],
                "task_id": run_config["task_id"],
                "display_name": entry["display_name"],
                "model": model,
                "agent": entry["agent"],
                "status": entry["status"],
                "run_type": run_type,
                "run_path": entry.get("run_path"),
                "score": {
                    "reward": reward,
                    "points": score_points,
                    "points_per_1k_tokens": finite_or_none(
                        score_points_per_1k(score_points, total_tokens)
                    ),
                    "points_per_usd": finite_or_none(score_per_dollar),
                },
                "tokens": measured["tokens"],
                "cost": {
                    "estimated_usd": cost,
                    "source": "pricing_table" if cost is not None else "unavailable",
                    "approximate": bool(measured["tokens"].get("approximate")),
                    "rates_usd_per_1m": pricing,
                },
                "duration_s": measured.get("duration_s"),
                "diagnostics": entry["diagnostics"],
            }
        )

    ranked = [r for r in results if r["score"]["points"] is not None]
    ranked.sort(key=lambda row: row["score"]["points"], reverse=True)
    rank_by_id = {row["id"]: i + 1 for i, row in enumerate(ranked)}
    for row in results:
        row["rank"] = rank_by_id.get(row["id"])

    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "task_id": run_config["task_id"],
        "pricing": {
            "unit": pricing_doc.get("metadata", {}).get("unit"),
            "last_reviewed": pricing_doc.get("metadata", {}).get("last_reviewed"),
            "sources": pricing_doc.get("metadata", {}).get("sources", {}),
            "notes": pricing_doc.get("metadata", {}).get("notes", []),
        },
        "results": sorted(results, key=lambda row: (row["rank"] is None, row["rank"] or 9999)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs-file", type=Path, default=DEFAULT_RUNS_FILE)
    parser.add_argument("--pricing-file", type=Path, default=DEFAULT_PRICING_FILE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_FILE)
    args = parser.parse_args()

    leaderboard = build_leaderboard(args.runs_file, args.pricing_file)
    args.output.write_text(json.dumps(leaderboard, indent=2) + "\n")
    print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
