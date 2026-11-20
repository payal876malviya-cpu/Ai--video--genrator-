# AI Video Studio

Mobile-first web app for **Text-to-Video** and **Image-to-Video**, with a FastAPI backend and a plug-in provider system.

**Honest status:** out of the box it runs in **demo mode**. Demo mode returns public sample clips, clearly labelled
"Demo sample, not generated". No AI model is bundled. Real generation only works after you connect a provider below.

## Structure
```
backend/main.py              FastAPI app, jobs, validation, static serving
backend/providers/           base.py, demo.py, huggingface.py, gradio_space.py  (add your own here)
frontend/                    index.html, css/style.css, js/app.js (no build step)
outputs/                     generated videos and uploads (git-ignored)
.env.example  requirements.txt  Dockerfile  Procfile  render.yaml
```

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # leave VIDEO_PROVIDER=demo to start
uvicorn backend.main:app --reload
```
Open http://localhost:8000. If the backend is not running, the frontend falls back to a browser-only demo.

## Connecting a real model
Set `VIDEO_PROVIDER` in `.env`. Free access changes often, so verify current limits yourself before relying on any of these.

| Provider | What it is | Notes |
|---|---|---|
| `huggingface` | Hugging Face Inference Providers via `huggingface_hub` | Needs a free HF account and `HF_TOKEN`. Free accounts get only a small monthly credit; video models use it quickly. Whether a given model/provider supports text-to-video or image-to-video is decided by Hugging Face. See https://huggingface.co/docs/inference-providers |
| `gradio_space` | Any public Gradio Space with an API, called via `gradio_client` | Free but queued, rate-limited, and Spaces get renamed or removed. Open the Space, click "Use via API", and copy its `api_name` and parameters into `GRADIO_*` values in `.env`. |
| Self-hosted open models | Run e.g. LTX-Video, CogVideoX, or Wan 2.x locally | Needs a capable GPU. Write a small `Provider` subclass that calls your model. |

To add a provider: copy `backend/providers/demo.py`, implement `configured()` and `generate()`, then register it in `backend/providers/__init__.py`.
If a provider fails (bad key, quota, Space down), the error text is shown in the UI. Nothing is faked.

## API
- `GET /api/status` engine info
- `POST /api/generate/text` form: prompt, negative_prompt, aspect_ratio, style, duration
- `POST /api/generate/image` multipart: image, prompt, aspect_ratio, style, duration
- `GET /api/jobs/{id}` state, progress, video_url or error

Jobs are held in memory and reset on restart. Progress is real only for providers that report it (demo); others show an indeterminate bar.

## Free deployment options
Free tiers cannot run video models themselves; they host the app, which calls an external provider.
- **Hugging Face Spaces (Docker):** create a Space with the Docker SDK, push this repo (the `Dockerfile` listens on port 7860), add `HF_TOKEN` and `VIDEO_PROVIDER` under Settings → Secrets.
- **Render:** New → Blueprint from this repo (`render.yaml`), or Web Service with the build/start commands in that file. Free instances sleep when idle and have no persistent disk, so saved videos can disappear.
- **Railway / Fly.io / similar:** use the `Dockerfile` or `Procfile`; check their current free allowances.
- **Frontend only (GitHub Pages, Netlify):** works in browser-only demo mode; no generation without the backend.

Never commit `.env`. Keep API keys in the host's environment settings.
