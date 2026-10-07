# Inference host

Scores photos for the photo-check feature (iteration 3, task B47). The only
caller is the server's `HostedImageScorer` (B53). The server owns prompts,
thresholds and the decision; this host only returns a similarity number.

Text generation is out of scope for iteration 3. `app/generator.py` is left
over from iteration 2 and nothing imports it any more; delete it when
convenient.

## Model

`open_clip` ViT-B/32, pretrained `laion2b_s34b_b79k`, CPU by default. Both are
pinned in `app/config.py` (`INFERENCE_CLIP_MODEL_NAME`,
`INFERENCE_CLIP_PRETRAINED`). Changing either changes every score, so the
per-prompt thresholds in `server/content/prompts/vocabulary.yaml` must be
re-measured first (B54).

## Endpoints

`GET /health` — no token. Returns `{"status": "ok", ...}`.

`POST /score?prompt=<text>` — `Authorization: Bearer <token>`

The body is the raw image bytes (not multipart). Returns `{"score": 0.31}`, the
cosine similarity between the image and the prompt text.

| Status | Meaning |
|---|---|
| 400 | empty body, or bytes are not a decodable image |
| 401 | missing or wrong token, or no token configured on the host |
| 403 | `INFERENCE_REQUIRE_HTTPS=true` and the request did not arrive over HTTPS |
| 413 | body over `INFERENCE_MAX_IMAGE_BYTES` (default 5 MB) |

## Privacy

- The photo is read straight into memory. `UploadFile` is deliberately not
  used: it moves bodies above about 1 MB to a temporary file on disk.
- No body is logged. The prompt text is a query parameter, so the body is never
  parsed into an error message.
- Nothing is written to disk. `tests/test_main.py` checks that large photos
  leave the temp directory unchanged.

## Configuration

| Variable | Default | Notes |
|---|---|---|
| `INFERENCE_TOKEN` | unset | Shared secret. Unset means `/score` refuses everything. |
| `INFERENCE_REQUIRE_HTTPS` | `false` | Set `true` when deployed. Honours `X-Forwarded-Proto`. |
| `INFERENCE_MAX_IMAGE_BYTES` | 5242880 | Second size wall behind the server's own cap. |
| `INFERENCE_DEVICE` | `cpu` | `cuda` if the host has a GPU. |

The server side uses `INFERENCE_HOST_URL` and `INFERENCE_HOST_TOKEN`.

## Running

```bash
cd inference
python -m venv .venv
.venv\Scripts\Activate.ps1        # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
INFERENCE_TOKEN=change-me uvicorn app.main:app
```

The first start downloads the model weights. HTTPS is terminated by whatever
fronts the host (the university's proxy, or `uvicorn --ssl-keyfile/--ssl-certfile`).

## Testing

```bash
pytest
```

The suite never loads the model: `app.state.scorer` is replaced with a fake and
the lifespan never runs. There is no automated test of the real
`OpenClipScorer`. Check it by hand once weights can be downloaded: start the
host, `POST /score` with a photo of something red and the prompt
`something red`, then with an unrelated photo, and confirm the first scores
higher. Do this before B54 measurement and before deploying.
