#!/usr/bin/env python3
"""Summarize a direct Responses API benchmark run.

Expected run directory layout:
  response.json
  logs/rubric_details.json

Costs are estimated from a local pricing table or explicit CLI rates. The API
usage object reports tokens, not the final invoiced amount, so keep provider or
enterprise deployment overrides in config/model_pricing.json.
"""

import argparse
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRICING_FILE = REPO_ROOT / "config" / "model_pricing.json"


def read_json(path):
    with open(path, "r") as f:
        return json.load(f)


def load_pricing(path):
    if path is None or not path.exists():
        return {}
    return read_json(path).get("models", {})


def normalize_model_name(model):
    return (model or "").split("/")[-1]


def pricing_for_model(models, model):
    if not model:
        return None
    candidates = [
        model,
        normalize_model_name(model),
        model.replace("openai/", ""),
        model.replace("azure/", ""),
    ]
    for candidate in candidates:
        if candidate in models:
            return models[candidate]
    return None


def dollars(tokens, usd_per_million):
    return tokens * usd_per_million / 1_000_000.0


def format_money(value):
    if value is None:
        return "N/A"
    if value < 0.01:
        return f"${value:.5f}"
    return f"${value:.4f}"


def format_float(value, digits=2):
    if value is None:
        return "N/A"
    return f"{value:.{digits}f}"


def markdown_row(summary):
    return (
        f"| `{summary['model']}` | {summary['score_points']:.1f}/100 | "
        f"{summary['input_tokens']:,} | {summary['output_tokens']:,} | "
        f"{summary['reasoning_tokens']:,} | {summary['total_tokens']:,} | "
        f"{summary['api_duration_s']}s | {format_money(summary['estimated_cost_usd'])} | "
        f"{format_float(summary['score_points_per_1k_total_tokens'], 2)} | "
        f"{format_float(summary['score_points_per_dollar'], 1)} | |"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", help="Directory containing response.json and logs/rubric_details.json")
    parser.add_argument(
        "--pricing-file",
        type=Path,
        default=DEFAULT_PRICING_FILE,
        help="JSON file with per-model USD-per-1M-token rates",
    )
    parser.add_argument("--input-usd-per-million", type=float, default=None)
    parser.add_argument("--output-usd-per-million", type=float, default=None)
    parser.add_argument("--cached-input-usd-per-million", type=float, default=None)
    parser.add_argument(
        "--markdown-row",
        action="store_true",
        help="Print a leaderboard-ready Markdown table row instead of JSON",
    )
    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    response = read_json(run_dir / "response.json")
    rubric = read_json(run_dir / "logs" / "rubric_details.json")
    usage = response.get("usage", {})

    input_tokens = int(usage.get("input_tokens") or 0)
    output_tokens = int(usage.get("output_tokens") or 0)
    cached_tokens = int(usage.get("input_tokens_details", {}).get("cached_tokens") or 0)
    reasoning_tokens = int(usage.get("output_tokens_details", {}).get("reasoning_tokens") or 0)
    total_tokens = int(usage.get("total_tokens") or input_tokens + output_tokens)
    reward = float(rubric.get("reward") or 0.0)
    model = response.get("model")

    pricing_models = load_pricing(args.pricing_file)
    model_pricing = pricing_for_model(pricing_models, model) or {}
    input_rate = (
        args.input_usd_per_million
        if args.input_usd_per_million is not None
        else model_pricing.get("input_usd_per_million")
    )
    output_rate = (
        args.output_usd_per_million
        if args.output_usd_per_million is not None
        else model_pricing.get("output_usd_per_million")
    )
    cached_rate = (
        args.cached_input_usd_per_million
        if args.cached_input_usd_per_million is not None
        else model_pricing.get("cached_input_usd_per_million")
    )

    cost_usd = None
    if input_rate is not None and output_rate is not None:
        uncached_input = max(0, input_tokens - cached_tokens)
        if cached_rate is None:
            cached_rate = input_rate
        cost_usd = (
            dollars(uncached_input, input_rate)
            + dollars(cached_tokens, cached_rate)
            + dollars(output_tokens, output_rate)
        )

    score_points = 100.0 * reward
    duration_s = (
        int(response["completed_at"]) - int(response["created_at"])
        if response.get("completed_at") and response.get("created_at")
        else None
    )
    score_points_per_1k = (
        score_points / (total_tokens / 1000.0) if total_tokens else None
    )
    score_points_per_dollar = (
        score_points / cost_usd if cost_usd and cost_usd > 0 else None
    )

    summary = {
        "model": model,
        "status": response.get("status"),
        "reward": reward,
        "score_points": score_points,
        "input_tokens": input_tokens,
        "cached_input_tokens": cached_tokens,
        "uncached_input_tokens": max(0, input_tokens - cached_tokens),
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": total_tokens,
        "api_duration_s": duration_s,
        "score_points_per_1k_total_tokens": score_points_per_1k,
        "estimated_cost_usd": cost_usd,
        "score_points_per_dollar": score_points_per_dollar,
        "pricing": {
            "source_file": str(args.pricing_file) if args.pricing_file else None,
            "matched_model": normalize_model_name(model),
            "input_usd_per_million": input_rate,
            "cached_input_usd_per_million": cached_rate,
            "output_usd_per_million": output_rate,
            "cost_basis": "estimated from token usage; provider invoices may differ",
        },
    }

    if args.markdown_row:
        print(markdown_row(summary))
    else:
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
