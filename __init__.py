from .base import Provider, GenParams, ProviderError
from .demo import DemoProvider
from .huggingface import HuggingFaceProvider
from .gradio_space import GradioSpaceProvider

REGISTRY = {p.name: p for p in (DemoProvider(), HuggingFaceProvider(), GradioSpaceProvider())}
# To add a model: subclass Provider, implement generate(), and add it to REGISTRY.
