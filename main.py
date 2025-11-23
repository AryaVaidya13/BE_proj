import os
from core.logger import log
from agents.literature_agent import LiteratureAgent
from agents.experiment_agent import ExperimentAgent
from agents.paper_agent import PaperAgent

def main():
    log("🚀 NLP Research Assistant v2.0 — Autonomous Mode")

    topic = input("Enter your NLP topic: ").strip()
    try:
        limit = int(input("How many papers do you want to fetch? (default 5): ") or 5)
    except ValueError:
        limit = 5

    # Step 1: Literature
    log("📚 Step 1: Fetching and summarizing literature...")
    lit_agent = LiteratureAgent(topic, model_name="facebook/bart-large-cnn")
    literature = lit_agent.run(limit=limit)

    # Step 2: Experiments
    log("🧪 Step 2: Extracting experiment details...")
    exp_agent = ExperimentAgent(summaries=literature, topic=topic)
    exp_results = exp_agent.run()

    # Step 3: Paper generation
    log("📝 Step 3: Generating paper from results...")

    paper_agent = PaperAgent(
        topic=topic,
        literature=literature,
        experiments_bundle=exp_results
    )

    paper_info = paper_agent.run()
    paper_path = paper_info["pdf_path"]

    log("📤 Pipeline complete.")
    log(f"Final paper saved: {paper_path}")

if __name__ == "__main__":
    main()
