from core.logger import log
from agents.literature_agent import LiteratureAgent
from agents.experiment_agent import ExperimentAgent
from agents.paper_agent import PaperAgent

def main():
    log("🚀 Research Assistant v2.0")

    mode = input("Select mode (nlp/ml): ").strip().lower() or "nlp"
    topic = input("Enter your topic: ").strip()

    try:
        limit = int(input("How many papers? (default 5): ") or 5)
    except:
        limit = 5

    log("📚 Step 1: Literature analysis")
    lit = LiteratureAgent(topic, mode=mode)
    literature = lit.run(limit=limit)

    log("🧪 Step 2: Experiment analysis")
    exp = ExperimentAgent(literature, topic, mode=mode)
    experiments = exp.run()

    log("📝 Step 3: Paper generation")
    paper = PaperAgent(topic=topic, literature=literature, experiments_bundle=experiments)
    info = paper.run()

    log("📄 Final paper saved:")
    log(info["pdf_path"])

if __name__ == "__main__":
    main()
