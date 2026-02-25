from __future__ import annotations

import httpx


class LLMService:
    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def answer(self, question: str, context_blocks: list[str]) -> str:
        context = "\n\n".join(context_blocks)
        prompt = (
            "You are a fraud analyst assistant. Answer ONLY using the supplied context. "
            "If information is missing, explicitly say you cannot determine from retrieved evidence.\n\n"
            f"Question: {question}\n\nContext:\n{context}"
        )
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.base_url}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False},
            )
            response.raise_for_status()
            return response.json().get("response", "")
