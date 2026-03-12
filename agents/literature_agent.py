import os
import json
import time
import requests
import re
from datetime import datetime
from transformers import BartTokenizer, BartForConditionalGeneration
import torch
import xml.etree.ElementTree as ET


class LiteratureAgent:
    """
    Hybrid Literature Agent
    NLP mode → paper fetching + BART summarization
    ML mode  → paper fetching + ML metadata extraction
    """

    def __init__(self, topic, model_name="facebook/bart-large-cnn", device=None, mode="nlp"):
        self.topic = topic
        self.model_name = model_name
        self.mode = mode
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.raw_dir = "data/processed"
        self.summary_dir = "data/summaries"
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)

        if self.mode == "nlp":
            print("📦 Loading summarization model:", self.model_name)
            self.tokenizer = BartTokenizer.from_pretrained(self.model_name)
            self.model = BartForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
            print("✅ Model loaded on:", self.device)

    # ---------------- Semantic Scholar ----------------
    def fetch_semantic_scholar(self, limit):
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": self.topic,
            "fields": "title,abstract,authors,year,url",
            "limit": limit
        }

        for _ in range(3):
            try:
                r = requests.get(url, params=params, timeout=25)
                r.raise_for_status()
                break
            except:
                time.sleep(3)
        else:
            return []

        papers = []
        for p in r.json().get("data", []):
            papers.append({
                "title": p.get("title"),
                "abstract": p.get("abstract") or "",
                "authors": [a["name"] for a in p.get("authors", [])],
                "year": p.get("year"),
                "url": p.get("url"),
                "source": "semantic_scholar"
            })
        return papers

    # ---------------- arXiv fallback ----------------
    def fetch_arxiv(self, needed):
        query = f"all:{self.topic} AND (cat:cs.CL OR cat:cs.AI OR cat:cs.LG)"
        url = f"https://export.arxiv.org/api/query?search_query={query}&max_results={needed}"

        try:
            r = requests.get(url, timeout=25)
            r.raise_for_status()
        except:
            return []

        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        papers = []

        for e in root.findall("atom:entry", ns):
            papers.append({
                "title": e.find("atom:title", ns).text.strip(),
                "abstract": e.find("atom:summary", ns).text.strip(),
                "authors": [a.find("atom:name", ns).text for a in e.findall("atom:author", ns)],
                "year": int(e.find("atom:published", ns).text[:4]),
                "url": e.find("atom:id", ns).text,
                "source": "arxiv"
            })
        return papers

    # ---------------- NLP summarization ----------------
    def summarize_abstract(self, abstract):
        inputs = self.tokenizer(
            abstract, max_length=1024, truncation=True, return_tensors="pt"
        ).to(self.device)

        ids = self.model.generate(
            inputs["input_ids"],
            num_beams=4,
            max_length=130,
            min_length=30,
            no_repeat_ngram_size=3,
            early_stopping=True
        )
        return self.tokenizer.decode(ids[0], skip_special_tokens=True)

    # ---------------- ML metadata extraction ----------------
    def extract_ml_metadata(self, papers):
        dataset_pat = r"(mnist|cifar|imagenet|uci|kaggle|imdb|coco)"
        model_pat = r"(svm|random forest|xgboost|cnn|rnn|transformer|resnet)"
        metric_pat = r"(accuracy|f1|precision|recall|auc|rmse)"

        results = []
        for p in papers:
            text = p["abstract"].lower()
            results.append({
                "paper_title": p["title"],
                "datasets": list(set(re.findall(dataset_pat, text))),
                "models": list(set(re.findall(model_pat, text))),
                "metrics": list(set(re.findall(metric_pat, text))),
                "year": p["year"],
                "source": p["source"]
            })
        return results

    # ---------------- Save raw ----------------
    def save_raw(self, data):
        name = re.sub(r"\W+", "_", self.topic.lower())
        path = f"{self.raw_dir}/{name}_raw.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"💾 Raw data saved → {path}")

    # ---------------- Run ----------------
    def run(self, limit=5):
        papers = self.fetch_semantic_scholar(limit)
        if len(papers) < limit:
            papers += self.fetch_arxiv(limit - len(papers))

        self.save_raw(papers)

        if self.mode == "nlp":
            for p in papers:
                p["summary"] = self.summarize_abstract(p["abstract"])
                p["timestamp"] = datetime.now().isoformat()
            return papers

        print("📊 Extracting ML metadata...")
        return self.extract_ml_metadata(papers)
