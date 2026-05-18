# Computational Physics Leaderboard

## Task: `ultrawalk-endpoint`

| Rank | Model / Agent | Score | Tokens In | Tokens Out | Reasoning Tokens | Total Tokens | API Duration | Est. API Cost | Score / $ | Status | Run | Failure Diagnostics |
|------|---------------|-------|-----------|------------|------------------|--------------|--------------|---------------|-----------|--------|-----|---------------------|
| 1 | Reference Oracle | 100.0/100 | N/A | N/A | N/A | N/A | 40s wall | N/A | N/A | PASS | `jobs/2026-05-17__18-03-50` | Reference solution passes the graded Docker verifier, including visual diagnostics. |
| 2 | `qwen3.5-397b-a17b` via Harbor Aider | 76.0/100 | ~74,300 | ~24,600 | Unknown | ~98,900 | 482s wall | `~$0.1270` | `~598.6` | PARTIAL | `jobs/2026-05-17__18-24-23` | All artifacts present; simulator physics matched hidden reference and visualization passed. It lost endpoint/table points because `epsilon_star` stayed at `0` and `transport_table.csv` contained only the header. |
| 3 | `gpt-5.4` via Azure Responses | 69.6/100 | 1,789 | 14,510 | 7,689 | 16,299 | 173s | `$0.2221` | `313.5` | PARTIAL | `/tmp/ultrawalk_gpt54_eval` | Produced all required files and a diagnostic plot. Analysis functions passed, but simulator physics did not match the reference walk and the endpoint was low (`0.63`). |
| 4 | `gpt-5.3-codex` via Azure Responses | 59.0/100 | 1,598 | 6,180 | 2,460 | 7,778 | 59s | `$0.0893` | `660.6` | PARTIAL | `/tmp/ultrawalk_gpt53_codex_eval` | Produced all required files in the prior run, but simulator physics did not match the reference walk and table consistency was weak. |
| 5 | `deepseek-v4-pro` via Harbor Aider | 23.5/100 | ~49,100 | ~12,330 | Unknown | ~61,430 | 879s wall | `~$0.1283` | `~183.5` | PARTIAL | `jobs/2026-05-17__16-28-57` | Latest run wrote Python modules to `/workspace/` rather than `/workspace/output/`, so simulator, analysis, and visualization were missing to the verifier. Endpoint was also outside the accepted interval. |
| - | `qwen3-32b` via Harbor Aider | Unscored | ~24,100 | ~16,423 | Unknown | ~40,523 | Unknown | `~$0.0151` | N/A | INCOMPLETE | `jobs/2026-05-17__15-11-27` | Legacy run did not reach verifier completion; Aider log shows meaningful attempts but Harbor job metadata remained running/null after cancellation. |
| - | `kimi-k2.6` via Harbor Aider | Unscored | ~11,400 | ~61,000 | Unknown | ~72,400 | Unknown | `~$0.2548` | N/A | CANCELLED | `jobs/2026-05-17__14-54-12` | Legacy run was cancelled before verifier scoring. Aider log shows large output generation, but no graded reward was produced. |
| - | `qwen3-coder-flash` via DigitalOcean | Not run | N/A | N/A | N/A | N/A | N/A | N/A | N/A | NOT_RUN | N/A | Pricing is configured for future qwen-code runs, but no completed Harbor or direct evaluation is recorded yet. |

## Evaluation Protocol

The task uses a graded Harbor-compatible verifier:

- **Artifact contract**: required output files must be in `/workspace/output/`.
- **Physics invariants**: simulator import, norm preservation, RMS displacement, and final density are checked against hidden reference seeds.
- **Asymptotic reasoning**: `estimate_inv_dw` must use the finite-time scaling intercept of `log(sigma)/log(t)` versus `1/log(t)`.
- **Endpoint and table consistency**: `epsilon_star.json` and `transport_table.csv` are checked against the bundled public observations.
- **Human-audit visualization**: `visualization.py` must generate a nonempty diagnostic image, but plot appearance is not the main reward to avoid image-only reward hacking.

The current task config requests `2` CPUs and `3072` MB memory; the difficulty is intended to come from scientific reproduction, not host memory pressure.

## Efficiency Notes

For direct Azure Responses runs, token usage is taken from the API `usage` object and estimated cost is computed with [config/model_pricing.json](/Users/richa/Noether/computational-physics-bench/config/model_pricing.json). For legacy Harbor/Aider runs, token usage is parsed from Aider's `Tokens: ... sent, ... received` log lines, so those values are approximate and should be replaced by adapter-level usage telemetry when available.

- `gpt-5.4`: `69.636 / 16.299k = 4.27` score-points per 1k total tokens; estimated `313.5` score-points per dollar.
- `gpt-5.3-codex`: `59.0 / 7.778k = 7.59` score-points per 1k total tokens; estimated `660.6` score-points per dollar.
- `qwen3.5-397b-a17b`: `76.0 / 98.9k = 0.77` score-points per 1k approximate Aider-log tokens; estimated `598.6` score-points per dollar.
- `deepseek-v4-pro`: `23.5499 / 61.43k = 0.38` score-points per 1k approximate Aider-log tokens; estimated `183.5` score-points per dollar.
- Harbor Aider job results currently report `n_input_tokens`, `n_output_tokens`, and `cost_usd` as `null`; adapter-level instrumentation is needed for reliable token/cost telemetry.

Generate leaderboard telemetry with:

```bash
scripts/summarize_response_run.py /tmp/ultrawalk_gpt54_eval
scripts/summarize_response_run.py /tmp/ultrawalk_gpt54_eval --markdown-row
scripts/build_leaderboard_json.py --output leaderboard.json
```
