# Codex build prompt: layered-motion-composition

Implement the first production-ready scaffold for the `layered-motion-composition` Harbor task.

The task evaluates whether an agent can improve a supplied frozen MoMask-style text-to-motion system on ordered compound instructions under a fixed compute budget. Keep the task method-agnostic: do not prescribe adapters, LoRA, prompt decomposition, segment concatenation, reranking, inpainting, full fine-tuning, or physics postprocessing.

## Build requirements

1. Preserve the public output contract in `instruction.md`.
2. Keep agent and verifier Docker images isolated.
3. Never copy hidden prompts, reference BVHs, detector weights, baseline hidden scores, pass thresholds, or oracle deltas into the agent image.
4. Provide small synthetic fixtures so repository CI can validate schema, determinism, units, finite values, root continuity, ground penetration, and bone-length consistency without large weights.
5. Add public tools for canonical motion I/O and basic physical diagnostics.
6. Define an external asset injection contract for:
   - immutable frozen runtime and pretrained weights;
   - licensed atomic and layered BVHs;
   - canonical skeleton and normalization data;
   - hidden structured motion specifications and paraphrases;
   - private semantic detectors and reference features;
   - BVH-to-VRMA visual reporting assets.
7. The production verifier must execute the submitted generator on hidden prompts and score:
   - action presence and order;
   - counts, sides, directions, pauses, and final poses;
   - transition smoothness;
   - foot contact, ground penetration, balance, root continuity, and skeletal consistency;
   - paraphrase consistency and diversity;
   - runtime, peak memory, artifact size;
   - improvement over the frozen baseline.
8. Generate a reviewable HTML report containing canonical skeleton videos, trusted BVH exports, and optionally VRMA animations. Canonical global joints remain the graded artifact.
9. Document threshold calibration against the frozen model, naive segment composition, contact-aware blending, a trainable adapter baseline, intentionally invalid outputs, and a strong reference method.
10. Keep all dependencies pinned and all production evaluation offline.

## Initial hidden motion grammar

Support procedural variants of ten families: hop-to-jumping-jacks; walk-turn-walk; jog-decelerate-sit; arms-squats-jump; asymmetric sidesteps; kicks-balance-bow; circle-face-wave; crouch-stand-spin-freeze; march-and-clap; jump-land-step-kneel. Randomize wording, side, counts, durations, and held-out action combinations.

## Completion criteria

- Synthetic fixture verification works without network access.
- Valid fixture output passes; malformed, NaN, wrong-length, root-teleporting, penetrating, and bone-drifting outputs fail.
- Agent image contains no hidden evaluation assets.
- Reviewer documentation explains data provenance, licensing, physical metrics, anti-contamination design, resource assumptions, and remaining production asset work.
- The scaffold is reviewable without committing multi-gigabyte checkpoints or motion archives.

Tracks issue #1.
