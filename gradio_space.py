import json
import os
import shutil
from .base import Provider, GenParams, ProviderError


class GradioSpaceProvider(Provider):
    """Calls any Gradio Space through gradio_client. Space names, api_names and parameters
    differ per Space - copy them from the Space's 'Use via API' page into .env."""
    name = "gradio_space"
    label = "Gradio Space"
    durations = [4]

    def configured(self):
        if not os.getenv("GRADIO_SPACE"):
            return False, "GRADIO_SPACE is not set."
        try:
            import gradio_client  # noqa: F401
        except ImportError:
            return False, "gradio_client is not installed."
        return True, ""

    def generate(self, params: GenParams, out_dir, job_id, progress):
        from gradio_client import Client, handle_file
        is_text = params.mode == "text"
        api_name = os.getenv("GRADIO_TEXT_API_NAME" if is_text else "GRADIO_IMAGE_API_NAME")
        template = os.getenv("GRADIO_TEXT_PARAMS" if is_text else "GRADIO_IMAGE_PARAMS", "{}")
        if not api_name:
            raise ProviderError("Set the api_name for this mode in .env (see the Space's API page).")
        try:
            tpl = json.loads(template)
        except json.JSONDecodeError:
            raise ProviderError("GRADIO_*_PARAMS is not valid JSON.")
        values = {"prompt": params.prompt, "negative_prompt": params.negative_prompt,
                  "aspect_ratio": params.aspect_ratio, "duration": params.duration,
                  "style": params.style}
        kwargs = {}
        for k, v in tpl.items():
            if v == "{image}":
                kwargs[k] = handle_file(str(params.image_path))
            elif isinstance(v, str) and v.startswith("{") and v.endswith("}") and v[1:-1] in values:
                kwargs[k] = values[v[1:-1]]
            else:
                kwargs[k] = v
        progress(10, "Queued on Gradio Space (may wait for a GPU)")
        try:
            client = Client(os.getenv("GRADIO_SPACE"), hf_token=os.getenv("HF_TOKEN") or None)
            result = client.predict(api_name=api_name, **kwargs)
        except Exception as e:
            raise ProviderError(f"Gradio Space request failed: {e}")
        path = self._find_video(result)
        if not path:
            raise ProviderError("The Space did not return a video file.")
        out = out_dir / f"{job_id}.mp4"
        shutil.copy(path, out)
        return {"video_url": f"/outputs/{out.name}", "is_demo": False}

    @staticmethod
    def _find_video(r):
        if isinstance(r, str):
            return r
        if isinstance(r, dict):
            return r.get("video") or r.get("path")
        if isinstance(r, (list, tuple)):
            for x in r:
                p = GradioSpaceProvider._find_video(x)
                if p:
                    return p
        return None
