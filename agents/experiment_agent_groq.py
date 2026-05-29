import json
import re
import os

from groq import Groq
from core.config import GROQ_API_KEY


class ExperimentAgentGroq:
    def __init__(self, summaries, topic, mode="nlp"):
        self.summaries = summaries
        self.topic = topic
        self.mode = mode

        self.client = Groq(api_key=GROQ_API_KEY)

    def _prepare_input(self):
        """
        Reduce noise but KEEP useful info.
        """
        cleaned = []

        for p in self.summaries:
            cleaned.append({
                "title": p.get("title"),
                "text": (
                    p.get("summary")
                    or p.get("abstract", "")[:500]
                )
            })

        return cleaned

    def extract_experiments(self):

        compact_input = self._prepare_input()

        prompt = f"""
You are an expert research analyst.

Task:
Extract OR INFER experimental details from research summaries.

Return STRICT JSON ONLY.

FORMAT:
{{
  "experiments": [
    {{
      "paper_title": "",
      "datasets": [],
      "models_used": [],
      "metrics": [],
      "key_results": ""
    }}
  ]
}}

RULES:
- ONLY return JSON
- NO explanation
- If dataset/model not explicitly mentioned, infer from context
- Extract metrics like accuracy, F1, etc.
- Keep key_results short and meaningful

INPUT:
{json.dumps(compact_input, indent=2)}
"""

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        text = response.choices[0].message.content.strip()

        # Clean formatting
        text = re.sub(r"```json|```", "", text).strip()

        # DEBUG (important)
        print("\n🔍 RAW LLM OUTPUT:\n", text)

        try:
            return json.loads(text)
        except Exception as e:
            print("⚠️ JSON parsing failed:", e)

            # fallback: try extracting JSON manually
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass

            return {"experiments": []}

    def run(self):
        print("🧪 Extracting experimental insights...")

        data = self.extract_experiments()

        name = re.sub(r"\W+", "_", self.topic.lower())
        path = f"outputs/{name}_experiments.json"
        os.makedirs("outputs", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✔ Experiments saved → {path}")

        return data