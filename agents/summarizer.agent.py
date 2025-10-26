# agents/summarizer_agent.py
import json
from pathlib import Path
from some_summarization_library import summarize_text  # can be GPT, HuggingFace, etc.

class SummarizerAgent:
    def __init__(self, input_file="data/processed/papers.json", output_file="data/processed/summaries.json"):
        self.input_file = Path(input_file)
        self.output_file = Path(output_file)
        self.papers = []

    def load_papers(self):
        if not self.input_file.exists():
            raise FileNotFoundError(f"{self.input_file} not found.")
        with open(self.input_file, "r", encoding="utf-8") as f:
            self.papers = json.load(f)

    def summarize_papers(self):
        summaries = []
        for paper in self.papers:
            abstract = paper.get("abstract", "")
            if abstract:
                summary = summarize_text(abstract)  # your summarization function
            else:
                summary = "No abstract available."
            summaries.append({
                "paperId": paper.get("paperId"),
                "title": paper.get("title"),
                "year": paper.get("year"),
                "summary": summary,
                "url": paper.get("url")
            })
        return summaries

    def save_summaries(self, summaries):
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(summaries, f, indent=2)
        print(f"\n✅ Summaries saved to {self.output_file}")
