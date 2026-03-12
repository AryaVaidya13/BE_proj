import json
import google.generativeai as genai
from core.config import GEMINI_API_KEY
import re
import os


class ExperimentAgent:
    def __init__(self, summaries, topic, mode="nlp"):
        self.summaries = summaries
        self.topic = topic
        self.mode = mode

        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def extract_experiments(self):
        if self.mode == "nlp":
            schema = """
{
  "experiments": [
    {
      "paper_title": "",
      "datasets": [],
      "models_used": [],
      "metrics": [],
      "key_results": ""
    }
  ]
}
"""
            instruction = "Extract NLP experimental details."

        else:
            schema = """
{
  "experiments": [
    {
      "paper_title": "",
      "datasets": [],
      "models": [],
      "evaluation_metrics": [],
      "reported_results": ""
    }
  ]
}
"""
            instruction = "Extract Machine Learning experimental setups."

        prompt = f"""
You are an expert research analyst.

Topic: {self.topic}

{instruction}

Input:
{json.dumps(self.summaries, indent=2)}

Return ONLY valid JSON matching:
{schema}
"""

        response = self.model.generate_content(prompt)
        cleaned = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)

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
