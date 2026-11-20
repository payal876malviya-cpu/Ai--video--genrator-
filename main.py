import os
import threading
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

from .providers import REGISTRY, GenParams, ProviderError  # noqa: E402

OUT = ROOT / "outputs"
UPLOADS = OUT / "uploads"
OUT.mkdir(exist_ok=True)
UPLOADS.mkdir(exist_ok=True)

app = FastAPI(title="AI Video Studio")
JOBS: dict[str, dict] = {}       # in-memory; resets on restart
RATIOS = {"9:16", "16:9", "1:1"}
STYLES = {"cinematic", "3d-animation", "realistic", "anime"}


def provider():
    return REGISTRY.get(os.getenv("VIDEO_PROVIDER", "demo").lower(), REGISTRY["demo"])


@app.get("/api/status")
def status():
    p = provider()
    ready, reason = p.configured()
    return {"provider": p.name, "label": p.label, "is_demo": p.is_demo, "ready": ready,
            "reason": reason, "durations": p.durations, "reports_progress": p.reports_progress}


def start_job(params: GenParams):
    p = provider()
    ready, reason = p.configured()
    if not ready:
        raise HTTPException(503, f"Provider '{p.name}' is not ready: {reason}")
    job_id = uuid.uuid4().hex[:12]
    JOBS[job_id] = {"id": job_id, "state": "running", "progress": 0, "message": "Starting"}

    def progress(pct, msg=""):
        JOBS[job_id].update(progress=pct, message=msg)

    def run():
        try:
            res = p.generate(params, OUT, job_id, progress)
            JOBS[job_id].update(state="done", progress=100, message="Done", **res)
        except ProviderError as e:
            JOBS[job_id].update(state="error", error=str(e))
        except Exception as e:
            JOBS[job_id].update(state="error", error=f"Unexpected error: {e}")

    threading.Thread(target=run, daemon=True).start()
    return {"job_id": job_id}


def check(prompt, ratio, style, duration):
    if not prompt.strip():
        raise HTTPException(400, "Prompt is required.")
    if ratio not in RATIOS or style not in STYLES:
        raise HTTPException(400, "Invalid aspect ratio or style.")
    if duration not in provider().durations:
        raise HTTPException(400, f"Duration must be one of {provider().durations} seconds.")


@app.post("/api/generate/text")
def gen_text(prompt: str = Form(...), negative_prompt: str = Form(""),
             aspect_ratio: str = Form("16:9"), style: str = Form("cinematic"),
             duration: int = Form(4)):
    check(prompt, aspect_ratio, style, duration)
    return start_job(GenParams("text", prompt, negative_prompt, aspect_ratio, style, duration))


@app.post("/api/generate/image")
async def gen_image(image: UploadFile = File(...), prompt: str = Form(""),
                    style: str = Form("cinematic"), aspect_ratio: str = Form("16:9"),
                    duration: int = Form(4)):
    check(prompt or "x", aspect_ratio, style, duration)
    if image.content_type not in ("image/png", "image/jpeg", "image/webp"):
        raise HTTPException(400, "Upload a PNG, JPG or WebP image.")
    data = await image.read()
    if len(data) > int(os.getenv("MAX_UPLOAD_MB", "8")) * 1024 * 1024:
        raise HTTPException(413, "Image is too large.")
    path = UPLOADS / f"{uuid.uuid4().hex}{Path(image.filename or 'x.png').suffix.lower()}"
    path.write_bytes(data)
    return start_job(GenParams("image", prompt, "", aspect_ratio, style, duration, path))


@app.get("/api/jobs/{job_id}")
def job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found (the server may have restarted).")
    return JOBS[job_id]


app.mount("/outputs", StaticFiles(directory=OUT), name="outputs")
app.mount("/css", StaticFiles(directory=ROOT / "frontend/css"), name="css")
app.mount("/js", StaticFiles(directory=ROOT / "frontend/js"), name="js")


@app.get("/")
def index():
    return FileResponse(ROOT / "frontend/index.html")
