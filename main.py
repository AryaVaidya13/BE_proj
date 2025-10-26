from agents.literature_agent import LiteratureAgent
from agents.summarizer_agent import SummarizerAgent

if __name__ == "__main__":
    print("🚀 NLP Research Assistant v1.2")
    
    mode = input("Choose mode: [1] Fetch papers, [2] Summarize papers: ").strip()
    
    if mode == "1":
        topic = input("Enter your NLP topic: ")
        try:
            limit = int(input("How many papers do you want to fetch? (default = 5): ") or 5)
        except ValueError:
            print("⚠️ Invalid input. Defaulting to 5.")
            limit = 5
        agent = LiteratureAgent()
        try:
            papers = agent.fetch_papers(topic, limit=limit)
            print(f"\n✅ Successfully fetched and saved {len(papers)} papers for topic: '{topic}'")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif mode == "2":
        summarizer = SummarizerAgent()
        summarizer.load_papers()
        summaries = summarizer.summarize_papers()
        summarizer.save_summaries(summaries)
    
    else:
        print("⚠️ Invalid mode selected.")
