# Authoring notes

This PR is a lightweight, reviewable scaffold. Large pretrained checkpoints, licensed motion archives, private semantic detectors, hidden references, and the production BVH-to-VRMA converter are intentionally not committed.

## First-principles judgment target

The agent is given a frozen text-to-motion system and enough public trajectories and diagnostics to investigate it. The instruction states only the desired behavior and resource limits. The agent must decide what to change and how to spend training and inference compute.

## Asset injection

The production build pipeline must mount immutable assets at build time:

- `/opt/motion-benchmark/runtime/`: frozen model source and canonical motion runtime;
- `/opt/motion-benchmark/weights/`: RVQ-VAE, masked transformer, residual transformer, length estimator, and evaluator weights;
- `/workspace/data/`: public atomic/layered trajectories, annotations, skeleton, normalization, and validation examples;
- `/tests/private/`: hidden prompts/specifications, reference features/BVHs, detector weights, baseline scores, thresholds, seeds, and visualization assets.

No private verifier asset may exist in the agent image, a parent image, Docker history, git history, environment variables, or public caches.

## Hidden evaluation

Generate private prompts from structured event specifications rather than committing ten fixed sentences. Hold out action combinations and independently vary paraphrase, side, count, duration, direction, pauses, and final pose. Score canonical 22-joint global positions; use trusted BVH and VRMA conversion only for reporting.

## Production scoring

Initial target weights:

- 45% structured event semantics and ordering;
- 30% biomechanical validity;
- 15% reference-distribution or motion-prior score;
- 10% efficiency.

Hard gates should cover complete output, deterministic fixed-seed generation, finite values, units, principal-action coverage, correct order, severe penetration, skeletal consistency, runtime, artifact size, and positive improvement over the frozen baseline.

## Calibration experiments before thresholds are frozen

Run and archive results for:

1. frozen pretrained baseline;
2. prompt-only variants;
3. naive segment concatenation;
4. interpolation/blending without contact constraints;
5. contact-aware composition;
6. small adapter or LoRA baseline;
7. candidate reranking at multiple sample budgets;
8. a strong private reference method;
9. intentionally malformed, collapsed, penetrating, skating, and bone-drifting outputs.

Thresholds must permit multiple valid optimization strategies and must not require matching one reference trajectory frame by frame.

## Data provenance and licensing

Every committed or externally injected trajectory needs source, license, preprocessing, original skeleton, retargeting transform, frame rate, scale, and event-annotation provenance. Public and private splits must be checked for duplicate and near-duplicate source clips.

## Resource target

Development target: one T4/L4-class GPU, 8 CPUs, 32 GB RAM, 40–50 GB storage, four hours, internet disabled. Production verifier target: separate image, one comparable GPU initially, 8 CPUs, 24–32 GB RAM, one hour. Recalibrate after profiling the actual frozen runtime and hidden generation count.
