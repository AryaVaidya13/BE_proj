import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY
import re
import os

from core.utils import safe_generate


class ExperimentAgent:
    def __init__(self, summaries, topic, mode="nlp"):
        self.summaries = summaries
        self.topic = topic
        self.mode = mode

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")

    def extract_experiments(self):

        schema = """
{
  "papers": [
    {
      "paper_title": "",
      "methodology": "",
      "models_used": [],
      "dataset": "",
      "evaluation_metrics": [],
      "key_results": "",
      "key_contribution": "",
      "limitations": ""
    }
  ]
}
"""

        prompt = f"""
You are an expert research analyst.

Topic: {self.topic}

Your job is to extract DETAILED structured information for EACH paper.

IMPORTANT RULES:
- DO NOT summarize multiple papers together
- Each paper must have its own entry
- Be specific and descriptive
- Capture technical depth
- Include limitations and contributions

Input:
{json.dumps(self.summaries, indent=2)}

Return ONLY valid JSON in this format:
{schema}
"""

        response = safe_generate(self.model, prompt)

        cleaned = response.text.strip()
        cleaned = re.sub(r"```json|```", "", cleaned)

        try:
            return json.loads(cleaned)
        except Exception as e:
            print("⚠️ JSON parsing failed:", e)
            return {"papers": []}

    def run(self):
        print("🧪 Extracting detailed experimental insights...")

        data = self.extract_experiments()

        name = re.sub(r"\W+", "_", self.topic.lower())
        path = f"outputs/{name}_experiments.json"
        os.makedirs("outputs", exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"✔ Experiments saved → {path}")

        return data