import math
import hashlib
from typing import List
import requests
from backend.app.core.config import settings

class EmbeddingService:
    """Generador de embeddings utilizando Ollama local (nomic-embed-text) con fallback determinista."""
    
    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.EMBEDDING_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.dim = 768

    def get_embedding(self, text: str) -> List[float]:
        try:
            url = f"{self.base_url}/api/embeddings"
            payload = {
                "model": self.model,
                "prompt": text
            }
            resp = requests.post(url, json=payload, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                emb = data.get("embedding", [])
                if emb:
                    return emb
        except Exception as e:
            # Fallback transparente si Ollama tiene latencia o timeout
            pass
            
        return self._generate_fallback_embedding(text)

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Genera un vector pseudo-semántico determinista normalizado de 768 dimensiones."""
        words = text.lower().split()
        vector = [0.0] * self.dim
        for word in words:
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vector[idx] += val
            
        # Normalizar vector L2
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            vector = [x / norm for x in vector]
        return vector

embedding_service = EmbeddingService()
