import os
from typing import Optional

import vertexai
from vertexai.generative_models import GenerativeModel, Part, Image

from backend.app.core.config import settings

class AIClient:
    def __init__(self):
        if settings.ENABLE_AI_FEATURES:
            if not settings.VERTEX_AI_PROJECT_ID or not settings.VERTEX_AI_LOCATION:
                raise ValueError(
                    "Vertex AI project ID and location must be set if AI features are enabled."
                )
            vertexai.init(
                project=settings.VERTEX_AI_PROJECT_ID,
                location=settings.VERTEX_AI_LOCATION
            )
            self.model = GenerativeModel("gemini-pro")
            self.vision_model = GenerativeModel("gemini-pro-vision")
        else:
            self.model = None
            self.vision_model = None

    def _check_ai_enabled(self):
        if not settings.ENABLE_AI_FEATURES or self.model is None:
            raise RuntimeError("AI features are not enabled.")

    def generate_text(self, prompt: str) -> str:
        self._check_ai_enabled()
        response = self.model.generate_content([prompt])
        return response.text

    def generate_manim_guidelines_from_image(self, image_bytes: bytes, prompt: str) -> str:
        self._check_ai_enabled()
        image_part = Part.from_data(image_bytes, mime_type="image/jpeg") # Assuming JPEG for now
        response = self.vision_model.generate_content([image_part, prompt])
        return response.text

# Initialize AI client globally
ai_client = AIClient()
