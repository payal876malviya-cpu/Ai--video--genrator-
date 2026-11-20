from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ProviderError(Exception):
    """Raised with a user-readable message when generation cannot complete."""


@dataclass
class GenParams:
    mode: str                      # "text" | "image"
    prompt: str
    negative_prompt: str = ""
    aspect_ratio: str = "16:9"
    style: str = "cinematic"
    duration: int = 4
    image_path: Optional[Path] = None


class Provider:
    name = "base"
    label = "Base"
    is_demo = False
    supports_text = True
    supports_image = True
    durations = [4]                # durations (seconds) the provider can honour
    reports_progress = False

    def configured(self) -> tuple[bool, str]:
        """Return (ready, human-readable reason if not ready)."""
        return True, ""

    def generate(self, params: GenParams, out_dir: Path, job_id: str, progress) -> dict:
        """Return {"video_url": str, "is_demo": bool}. Call progress(pct, msg) if supported."""
        raise NotImplementedError
