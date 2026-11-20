import os
from .base import Provider, GenParams, ProviderError


class HuggingFaceProvider(Provider):
    """Uses huggingface_hub.InferenceClient. Which models/providers work, and how much
    free quota you get, is decided by Hugging Face and changes over time - check
    https://huggingface.co/docs/inference-providers before relying on it."""
    name = "huggingface"
    label = "Hugging Face Inference Providers"
    durations = [4]

    def configured(self):
        if not os.getenv("HF_TOKEN"):
            return False, "HF_TOKEN is not set."
        try:
            import huggingface_hub  # noqa: F401
        except ImportError:
            return False, "huggingface_hub is not installed."
        return True, ""

    def generate(self, params: GenParams, out_dir, job_id, progress):
        from huggingface_hub import InferenceClient
        client = InferenceClient(provider=os.getenv("HF_INFERENCE_PROVIDER", "auto"),
                                 api_key=os.getenv("HF_TOKEN"))
        progress(10, "Sending request to Hugging Face")
        try:
            if params.mode == "text":
                data = client.text_to_video(params.prompt,
                                            model=os.getenv("HF_TEXT_MODEL", "Lightricks/LTX-Video"))
            else:
                fn = getattr(client, "image_to_video", None)
                if fn is None:
                    raise ProviderError("Your huggingface_hub version has no image_to_video. Upgrade it.")
                data = fn(params.image_path.read_bytes(), prompt=params.prompt,
                          model=os.getenv("HF_IMAGE_MODEL", "Lightricks/LTX-Video"))
        except ProviderError:
            raise
        except Exception as e:  # quota, model unavailable, auth, etc.
            raise ProviderError(f"Hugging Face request failed: {e}")
        progress(90, "Saving video")
        out = out_dir / f"{job_id}.mp4"
        out.write_bytes(data)
        return {"video_url": f"/outputs/{out.name}", "is_demo": False}
