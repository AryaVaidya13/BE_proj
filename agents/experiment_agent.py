import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY
import re
import os


class ExperimentAgent:
    def __init__(self, summaries, topic):
        self.summaries = summaries
        self.topic = topic

        # Configure Gemini client
        genai.configure(api_key=GEMINI_API_KEY)

        # Correct model
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract_experiments(self):
        schema = """
{
  "experiments": [
    {
      "paper_title": "",
      "datasets": [],
      "models_used": [],
      "training_setup": "",
      "metrics": [],
      "baseline_models": [],
      "ablation_studies": "",
      "key_results": ""
    }
  ]
}
"""

        prompt = f"""
You are an expert NLP research assistant.

Given the following paper summaries for the topic: {self.topic}

Extract ONLY experimental details in clean JSON format.

Summaries:
{json.dumps(self.summaries, indent=2)}

Return JSON **matching this exact format**:
{schema}

IMPORTANT:
- Return ONLY valid JSON.
- No extra comments or text.
"""

        response = self.model.generate_content(prompt)

        try:
            return json.loads(response.text)
        except Exception:
            cleaned = response.text.strip().replace("```json", "").replace("```", "")
            return json.loads(cleaned)

    def save_experiments(self, data):

        safe_topic = re.sub(r"[^a-zA-Z0-9]+", "_", self.topic).lower()
        path = f"outputs/{safe_topic}_experiments.json"

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

        print(f"[✔] Saved experiment details → {path}")

    def run(self):
        print("[🧪] Step 2: Extracting experiments from summaries...")

        data = self.extract_experiments()
        self.save_experiments(data)

        return data
