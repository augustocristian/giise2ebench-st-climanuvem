import httpx
import json
import logging
import os
from app.infrastructure.config import get_settings
from jinja2 import Template

logger = logging.getLogger(__name__)

class OllamaClient:
    """Cliente para interactuar con la API de Ollama de forma asíncrona."""

    PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
    
    def __init__(self):
        settings = get_settings()
        self.url = settings.ollama_url
        self.model = settings.ollama_model

    def _render_prompt(self, template_name: str, **context) -> str:
        template_path = os.path.join(self.PROMPTS_DIR, template_name)
        with open(template_path, encoding="utf-8") as f:
            template = Template(f.read())
        return template.render(**context)
        
    def _clean_and_parse_json(self, text: str) -> dict:
        """Limpia la respuesta del modelo e intenta parsearla como JSON."""
        # 1. Intentar encontrar el bloque JSON si el modelo incluyó texto extra o markdown
        cleaned = text.strip()
        
        # Si contiene bloques de código markdown, extraer el contenido
        if "```" in cleaned:
            opening_fence_idx = cleaned.find("```")
            content_start_idx = opening_fence_idx + 3

            newline_idx = cleaned.find("\n", content_start_idx)
            if newline_idx != -1:
                fence_label = cleaned[content_start_idx:newline_idx].strip().lower()
                if not fence_label or fence_label == "json":
                    content_start_idx = newline_idx + 1

            closing_fence_idx = cleaned.find("```", content_start_idx)
            if closing_fence_idx != -1:
                cleaned = cleaned[content_start_idx:closing_fence_idx].strip()
        
        # 2. Si todavía no es un JSON puro, intentar encontrar el primer '{' y el último '}'
        if not (cleaned.startswith('{') and cleaned.endswith('}')):
            start_idx = cleaned.find('{')
            end_idx = cleaned.rfind('}')
            if start_idx != -1 and end_idx != -1:
                cleaned = cleaned[start_idx:end_idx+1]

        # 3. Intentar parsear
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("Error parsing model JSON response: %s", e)
            logger.debug("Raw model response: %s", text)
            # Si falla, devolvemos un objeto vacío para evitar que el worker rompa
            return {"predictions": []}

    def _normalize_prediction(self, prediction):
        if isinstance(prediction, str):
            label = prediction.strip()
            if not label:
                return None
            return {"label": label, "confidence": 0.0}

        if not isinstance(prediction, dict):
            logger.warning("Ignoring malformed model prediction: %r", prediction)
            return None

        label = prediction.get("label")
        if not isinstance(label, str) or not label.strip():
            logger.warning("Ignoring model prediction without a valid label: %r", prediction)
            return None

        normalized = {"label": label.strip()}

        try:
            confidence = float(prediction.get("confidence", 0.0))
        except (TypeError, ValueError):
            confidence = 0.0
        normalized["confidence"] = max(0.0, min(1.0, confidence))

        box_2d = prediction.get("box_2d")
        if isinstance(box_2d, list) and len(box_2d) == 4:
            normalized["box_2d"] = box_2d

        return normalized

    def _extract_predictions(self, result: dict) -> list:
        predictions = result.get("predictions", [])

        if isinstance(predictions, (dict, str)):
            predictions = [predictions]

        if not isinstance(predictions, list):
            logger.warning("Ignoring malformed model predictions payload: %r", predictions)
            return []

        normalized_predictions = []
        for prediction in predictions:
            normalized = self._normalize_prediction(prediction)
            if normalized:
                normalized_predictions.append(normalized)

        return normalized_predictions

    async def analyze_image(self, base64_image: str) -> list:
        """Realiza un análisis simple de la imagen para clasificar las nubes."""
        payload = {
            "model": self.model,
            "prompt": self._render_prompt("classifier_simple.j2"),
            "images": [base64_image],
            "stream": False,
            "options": {
                "seed": 42,
                "temperature": 0,
                "top_p": 1
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(self.url, json=payload)
            response.raise_for_status()
            
            raw_output = response.json().get("response", "")
            result = self._clean_and_parse_json(raw_output)
            return self._extract_predictions(result)

    async def get_explainability_boxes(self, base64_image: str, labels: list) -> list:
        """Obtiene las bounding boxes para una lista específica de etiquetas de nubes."""
        labels_str = ", ".join(labels)
        prompt = self._render_prompt("explainer.j2", labels_str=labels_str)
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "images": [base64_image],
            "stream": False,
            "options": {
                "seed": 42,
                "temperature": 0,
                "top_p": 1
            }
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(self.url, json=payload)
            response.raise_for_status()
            
            raw_output = response.json().get("response", "")
            result = self._clean_and_parse_json(raw_output)
            return self._extract_predictions(result)
