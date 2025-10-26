import os
import time
import json
import requests

class LiteratureAgent:
    def __init__(self):
        self.semantic_scholar_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.arxiv_url = "http://export.arxiv.org/api/query"
        
        # Define data folder structure
        self.data_dir = os.path.join("data", "processed")
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_papers(self, topic, limit=5):
        print(f"[🔍] Searching for papers on: {topic}")
        papers = []

        try:
            papers = self._fetch_from_semantic_scholar(topic, limit)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                print("[⚠️] Too many requests. Retrying after 5 seconds...")
                time.sleep(5)
                papers = self._fetch_from_semantic_scholar(topic, limit)
            else:
                print(f"[⚠️] Semantic Scholar failed: {e}")

        if not papers:
            print("[🔄] Falling back to arXiv...")
            papers = self._fetch_from_arxiv(topic, limit)

        if papers:
            self.save_results(topic, papers)
        else:
            print("[❌] No papers found.")

        return papers


    def _fetch_from_semantic_scholar(self, topic, limit):
        params = {
            "query": topic,
            "limit": limit,
            "fields": "title,authors,url,year,abstract"
        }
        response = requests.get(self.semantic_scholar_url, params=params)
        response.raise_for_status()
        data = response.json()
        papers = data.get("data", [])
        print(f"[✅] Retrieved {len(papers)} papers from Semantic Scholar")
        return papers


    def _fetch_from_arxiv(self, topic, limit):
        query = f"search_query=all:{topic}&start=0&max_results={limit}"
        response = requests.get(f"{self.arxiv_url}?{query}")
        response.raise_for_status()
        print(f"[✅] Retrieved {limit} fallback papers from arXiv")
        return [{"title": f"arXiv paper {i+1} on {topic}"} for i in range(limit)]


    def save_results(self, topic, papers):
        # Ensure safe file naming
        safe_topic = topic.replace(" ", "_").lower()
        filename = os.path.join(self.data_dir, f"{safe_topic}.json")

        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(papers, f, indent=2, ensure_ascii=False)
            print(f"[💾] Saved {len(papers)} papers to {filename}")
        except OSError as e:
            print(f"[❌] Failed to save file: {e}")
            if "No space left" in str(e):
                print("⚠️ Please free up some disk space and try again.")
