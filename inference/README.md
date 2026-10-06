# Inference service

The self-hosted model service Backend B owns in iteration 2 (task B37). This
is the only thing `HostedModelClient` (B38, not yet built) talks to — nobody
outside this directory should import a model library directly.

## Scope of this scaffold (B37)

- Load both models once at startup and run a warm-up call for each, so the
  first real request isn't the one paying model-load latency.
- One scoring route, one generation route, a health check.
- No persistence anywhere on the scoring path — the image lives in memory
  for the duration of one request and is never written to disk. (Formal
  assertion of that guarantee is B40.)

Not in scope here: `HostedModelClient` itself (B38), deployment (B39), and
prompt threshold calibration (B25/B26) — those are separate tasks and should
stay separate PRs.

## Model choice

Both defaults are CPU-hostable, since hosting budget wasn't decided yet and
everything is swappable behind these two classes without touching the routes
or `ModelClient` on the Backend B side:

| Capability | Model | Why |
|---|---|---|
| `score_image` | `openai/clip-vit-base-patch32` (CLIP) | Zero-shot image/text similarity, no training required, ~600MB, fast enough on CPU for single-image requests. Standard tool for "does this photo match this short prompt." |
| `generate_text` | `Qwen/Qwen2.5-1.5B-Instruct` | Short template-step rewriting is low-stakes text generation, not reasoning — a small instruct model is enough and keeps CPU latency tolerable. |

Override via env vars if hosting changes (`INFERENCE_CLIP_MODEL_NAME`,
`INFERENCE_TEXT_MODEL_NAME`, `INFERENCE_DEVICE=cuda`) — see `app/config.py`.

## Endpoints

`POST /generate`
```json
{"prompt": "...", "max_tokens": 64, "timeout_s": 10}
```
→ `{"text": "..."}` or `{"text": null}` on timeout or failure.

`POST /score` (multipart/form-data)
- `image`: file
- `prompts`: JSON-encoded list of strings, e.g. `["p_play_equipment", "p_blue"]`

→ `{"scores": [0.9, 0.1]}` — one score per prompt, in the order given, scored
independently (not a softmax over prompts). `null` on failure.
Malformed `prompts` or an undecodable image returns `400`.

`GET /health`

## Running

```bash
cd inference
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

First startup downloads both models from Hugging Face — expect it to take a
while and to need a few GB of disk.

## Testing

```bash
pytest
```

The test suite never loads a real model: `app.state.scorer` / `.generator`
are replaced with fakes before any request, and the client is never used as
a context manager, so the lifespan (which does the real model loading) never
runs. There is currently no automated test that exercises the real
`ClipScorer` / `TextGenerator` against actual weights — verify those
manually (`uvicorn` + a real request) once you can download the models in
your environment. That real-model check should happen before B39 (deploy).
