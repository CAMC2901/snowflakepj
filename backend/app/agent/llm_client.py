import json
from typing import Dict, Any, Optional, List
import requests
from backend.app.core.config import settings

class LLMClient:
    """
    Cliente inteligente multi-proveedor para el Agente Ciudadano:
    1. Prioridad: Groq Cloud ultrarrápido (<2s) con modelos abiertos de alta capacidad (120B/20B).
    2. Fallback: Ollama local (qwen2.5:0.5b / llama3) para operación 100% autónoma y offline ($0).
    3. Respaldo: Respuestas institucionales curadas con cero alucinaciones.
    """
    
    def __init__(
        self,
        base_url: str = settings.OLLAMA_BASE_URL,
        default_model: str = settings.LLM_MODEL,
        groq_api_key: str = settings.GROQ_API_KEY,
        groq_model: str = settings.GROQ_MODEL
    ):
        self.base_url = base_url.rstrip("/")
        self.default_model = default_model
        self.fallback_model = settings.LLM_FALLBACK_MODEL
        self.groq_api_key = groq_api_key
        self.groq_model = groq_model
        self._groq_client = None
        
        if self.groq_api_key:
            try:
                from groq import Groq
                self._groq_client = Groq(api_key=self.groq_api_key)
            except Exception:
                self._groq_client = None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 700
    ) -> str:
        """Genera una respuesta utilizando la mejor vía disponible con calidez y precisión."""
        # 1. Intentar con Groq Cloud de alta fidelidad si está disponible
        if self._groq_client:
            resp_groq = self._call_groq(prompt, system_prompt, temperature, max_tokens)
            if resp_groq and len(resp_groq.strip()) > 15:
                return resp_groq

        # 2. Intentar con Ollama local con timeout estricto de 8s
        selected_model = model or self.default_model
        resp_ollama = self._call_ollama(selected_model, prompt, system_prompt, temperature, max_tokens, timeout=8)
        if resp_ollama and len(resp_ollama.strip()) > 15:
            return resp_ollama

        return ""

    def _call_groq(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int
    ) -> Optional[str]:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            completion = self._groq_client.chat.completions.create(
                model=self.groq_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=10
            )
            if completion.choices and len(completion.choices) > 0:
                content = completion.choices[0].message.content
                if content:
                    return content.strip()
        except Exception:
            return None
        return None

    def _call_ollama(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: int,
        timeout: int = 8
    ) -> Optional[str]:
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "system": system_prompt or "",
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "repeat_penalty": 1.25,
                    "top_p": 0.9
                }
            }
            res = requests.post(url, json=payload, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                return data.get("response", "").strip()
        except Exception:
            return None
        return None

llm_client = LLMClient()
