# Akamai GPU expansion run: results (2026-10-12)

The Akamai inference workshop's own vLLM drafted richer detail for every SmartCiti.X zone:

- **Model:** `Qwen/Qwen3-4B`, served by vLLM on a dedicated Akamai Cloud GPU, with thinking turned off.
- **Script:** `expand.py`, run in the workshop's JupyterLab pod (1 GB RAM, CPU only). The pod called the GPU over HTTP.
- **Input:** `input.json`, with 246 zones and council halls across the 41 worlds. Each item holds only registry facts: zone purpose, building kind and door, agents and roles, Volum, and landmark style.

## Concurrency sweep on this workload

| Concurrency | Drafts | OK | Wall time | Drafts per min | Output tok/s | p50 latency |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4 | 4 | 24.0 s | 10.0 | 38.9 | 6.19 s |
| 4 | 8 | 8 | 13.3 s | 36.2 | 134.6 | 6.08 s |
| 8 | 16 | 16 | 12.8 s | 74.9 | 264.0 | 5.85 s |
| 16 | 32 | 32 | 19.0 s | 100.9 | 371.5 | 6.53 s |
| 32 | 64 | 64 | 17.9 s | **215.1** | **770.6** | 7.02 s |

There was no saturation knee up to 32: throughput kept rising while latency barely moved. Module 07 of the workshop sweeps higher. Use its knee to set the gateway's `MAX_INFLIGHT_LLM` and the concurrency of the next run.

## Full run

| Metric | Value |
|---|---|
| Zones drafted | **246 / 246**, 0 failed (4 needed one retry) |
| Wall time | **66.0 s** at concurrency 32 |
| Latency | p50 7.74 s, p95 10.18 s |
| Output tokens | 55,681 |

Every draft passed the checks in `expand.py`:
- strict JSON in the required shape;
- no claim of a human-reserved action (treasury, votes, appointments, charter, enactment, windfall);
- every number in a draft already appears in that zone's facts.

## Quality: these are drafts, not registry truth

Samples:

- `zone:locator-x/underwriting-desk`, interior: "A high-tech studio with large monitors displaying real-time data and predictive models…". Its walkthrough mentions the "seven-gate LOCATOR screen" (which is in the facts) and the door at `[0, 0, 4]` (also in the facts).
- `council:robotics-dao`, exterior: "Steeplechase-style rotunda…". "Rotunda" comes from the landmark style; "steeplechase-style" is invented.

The number check stops invented figures, but it does not stop invented **descriptive** detail such as "large monitors", "real-time data" or "steeplechase". The `rp1_notes` mostly repeat the rules the model was given (Z-up, 47 characters, glTF), so they add little.

All output therefore stays labelled `draft: true, reviewed: false`. It is never merged into `cards.json` or `my-fabric/` registries. A steward or the world's owner reviews it before any of it becomes canonical.

## Files

- `input.json`: the facts sent (built from `worldforge/out/<slug>/cards.json` and the landmarks index).
- `expand.py`: the runner: `sweep` and `run`. It uses the Python standard library only and reads `VLLM_HOST`, `MODEL_NAME` and `VLLM_API_KEY`.
- `expansion.json`: the 246 drafts. It is still in the pod at `~/workshop/smartciti/expansion.json`. Download it from JupyterLab (right-click → Download) and place it here, at `worldforge/akamai/expansion.json`.
