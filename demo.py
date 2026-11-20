import time
import zlib
from .base import Provider, GenParams

# Public sample clips. They are NOT generated from the user's prompt.
SAMPLES = [
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerJoyrides.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
    "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
]


class DemoProvider(Provider):
    name = "demo"
    label = "Demo mode (sample videos)"
    is_demo = True
    durations = [4, 8]
    reports_progress = True

    def generate(self, params: GenParams, out_dir, job_id, progress):
        for i in range(1, 6):          # short simulated wait so the UI flow can be tested
            progress(i * 18, "Preparing demo sample")
            time.sleep(0.4)
        url = SAMPLES[zlib.crc32(params.prompt.encode()) % len(SAMPLES)]
        return {"video_url": url, "is_demo": True}
