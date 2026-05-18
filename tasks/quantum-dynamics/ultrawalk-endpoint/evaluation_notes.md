# Ultrawalk Endpoint Evaluation Notes

Date: 2026-05-17

## Harness Fixes

- Baked `environment/data/` into the Docker image so `/workspace/data/observations.npz` exists in Harbor runs.
- Kept Harbor reward outputs numeric-only at `/logs/verifier/reward.json` and `/logs/verifier/reward.txt`.
- Wrote detailed rubric diagnostics to `/logs/verifier/rubric_details.json`.
- Replaced the binary verifier with a graded rubric so incomplete but serious attempts receive partial credit.
- Reduced the environment request to 2 CPUs and 3072 MB. The task data are small and the verifier checks short hidden simulations, so memory pressure should not be part of the benchmark difficulty.
- Added `visualization.py` as a low-weight human-audit artifact. It must produce a nonempty diagnostic image from submitted outputs, but numerical reward still comes from simulator and table consistency.

## Task-Clarity Fixes

- Expanded the agent-facing instructions with the exact coin, hierarchy-level, initial-state, and shift conventions.
- Clarified that the origin uses the identity coin but still participates in the shift stage.
- Documented the correct finite-time scaling fit: `log(sigma) / log(t)` versus `1 / log(t)`.
- Documented the `observations.npz` schema in `environment/data/README_observations.md`.
- Removed the hardcoded endpoint value from the output-schema example to reduce endpoint memorization.
- Added guidance for diagnostic density, scaling, and transport plots so human physicists can quickly inspect failure modes.

## Current Docker Results

- `jobs/2026-05-17__18-03-50`: oracle, reward `1.0` under the 3072 MB task config with `visualization.py` and the task-level `rubric.toml`.
- `jobs/2026-05-17__16-28-57`: Aider + `openai/openai/deepseek-v4-pro`, reward `0.235499`.
- `jobs/2026-05-17__18-24-23`: Aider + `openai/openai/qwen3.5-397b-a17b`, reward `0.76`.
- `/tmp/ultrawalk_gpt53_codex_eval`: direct Azure Responses call to `gpt-5.3-codex`, evaluated with the same Docker verifier under `--memory=3g --cpus=2`, reward `0.59`.
- `/tmp/ultrawalk_gpt54_eval`: direct Azure Responses call to `gpt-5.4`, evaluated with the same Docker verifier under `--memory=3g --cpus=2`, reward `0.69636`.
- `jobs/2026-05-17__15-11-27`: Aider + `openai/openai/alibaba-qwen3-32b`, incomplete/cancelled legacy run with no verifier reward.
- `jobs/2026-05-17__14-54-12`: Aider + `openai/openai/kimi-k2.6`, cancelled legacy run with no verifier reward.

DeepSeek's latest visualization-aware run produced a meaningful but weaker partial solution. It wrote several Python files to `/workspace/` instead of `/workspace/output/`, so Harbor correctly treated `simulator.py`, `analysis.py`, and `visualization.py` as missing. It did produce a transport table, but the endpoint was outside the accepted interval and table consistency with public cases was weak.

GPT-5.3-Codex produced all six required outputs and good method notes, but the simulator did not match the hidden reference walk and the transport table did not use the public case IDs, so it received low simulator and table-consistency credit.

GPT-5.4 produced all six required outputs, passed the analysis-function checks, and generated a nonempty diagnostic plot. It still missed the exact reference walk physics (`sigma` relative error about `1.5`, final-density max error about `0.243`) and underestimated the endpoint at `0.63`.

Qwen3.5-397B-A17B produced the strongest non-oracle result so far. It created all required artifacts, matched the hidden simulator reference to numerical precision, passed the synthetic scaling checks, and generated two visualization artifacts. It lost points because `epsilon_star.json` remained at `0` and `transport_table.csv` contained only the header, so the endpoint and public-case transport evidence were incomplete.

## Token and Cost Telemetry

Direct Azure Responses runs include an API `usage` object:

| Model | Reward | Input Tokens | Output Tokens | Reasoning Tokens | Total Tokens | API Duration | Score Points / 1k Tokens | Est. API Cost | Score Points / $ | Telemetry Source |
|-------|--------|--------------|---------------|------------------|--------------|--------------|---------------------------|---------------|------------------|------------------|
| `gpt-5.4` | `0.69636` | `1,789` | `14,510` | `7,689` | `16,299` | `173s` | `4.27` | `$0.2221` | `313.5` | Responses `usage` |
| `gpt-5.3-codex` | `0.59` | `1,598` | `6,180` | `2,460` | `7,778` | `59s` | `7.59` | `$0.0893` | `660.6` | Responses `usage` |
| `qwen3.5-397b-a17b` | `0.76` | `~74,300` | `~24,600` | Unknown | `~98,900` | `482s wall` | `0.77` | `~$0.1270` | `598.6` | Aider log, approximate |
| `deepseek-v4-pro` | `0.235499` | `~49,100` | `~12,330` | Unknown | `~61,430` | `879s wall` | `0.38` | `~$0.1283` | `183.5` | Aider log, approximate |
| `qwen3-32b` | Unscored | `~24,100` | `~16,423` | Unknown | `~40,523` | Unknown | N/A | `~$0.0151` | N/A | Aider log, approximate |
| `kimi-k2.6` | Unscored | `~11,400` | `~61,000` | Unknown | `~72,400` | Unknown | N/A | `~$0.2548` | N/A | Aider log, approximate |

The direct Responses estimates come from `scripts/summarize_response_run.py`, which reads `response.json`, `logs/rubric_details.json`, and the local pricing table in `config/model_pricing.json`. The frontend artifact comes from `scripts/build_leaderboard_json.py`, which also parses legacy Aider token log lines when Harbor result files report null token usage.

OpenAI's public pricing lists GPT-5.4 standard at `$2.50` input, `$0.25` cached input, and `$15.00` output per 1M tokens, and GPT-5.3-Codex standard at `$1.75` input, `$0.175` cached input, and `$14.00` output per 1M tokens. DigitalOcean's AI Platform pricing lists DeepSeek V4 Pro at `$1.74` input and `$3.48` output, Qwen3-32B at `$0.25` input and `$0.55` output, Qwen3.5-397B-A17B at `$0.55` input and `$3.50` output, Qwen3 Coder Flash at `$0.45` input and `$1.70` output, and Kimi K2.6 at `$0.95` input and `$4.00` output per 1M tokens. Private deployments may bill differently, so the scripts accept local pricing-table updates.

Harbor Aider runs currently leave `n_input_tokens`, `n_output_tokens`, and `cost_usd` as `null` in the job result. Reliable DeepSeek, Qwen, and Kimi token/cost telemetry will require either adapter-level instrumentation or a wrapper that calls the model API directly and records response usage.

## Adapter/Endpoint Notes

- `openai/deepseek-v4-pro` with the stock Harbor Aider model string failed before editing because the wrapper stripped the provider before calling Aider. The working invocation is `-m openai/openai/deepseek-v4-pro` with `OPENAI_API_BASE`/`OPENAI_BASE_URL` passed via `--ae`.
- Kimi 2.6 and Qwen 3 32B attempts through Aider were cancelled after long silent runs. These are not counted as task scores.
- A direct endpoint proxy attempt for Qwen timed out at the HTTP layer, and the OpenAI-branded fallback model was not enabled for the provided key.
- `gpt-5.4` is available on the Azure Responses endpoint as deployment name `gpt-5.4`. The `openai-gpt-5.4*` aliases are not available there, and the DigitalOcean endpoint returned `403 Forbidden` for `openai-gpt-5.4*`.
