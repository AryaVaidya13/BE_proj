# agents/literature_agent.py
import os
import json
import time
import requests
from datetime import datetime
from transformers import BartTokenizer, BartForConditionalGeneration
import torch
import xml.etree.ElementTree as ET


class LiteratureAgent:
    """
    Hybrid Paper Fetcher:
    1. Try Semantic Scholar (with retries)
    2. If fewer than LIMIT → fallback to arXiv (cs.CL, cs.AI, cs.LG)
    3. Summarize abstracts using BART
    """

    def __init__(self, topic, model_name="facebook/bart-large-cnn", device=None):
        self.topic = topic
        self.model_name = model_name
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        # Folder structure
        self.raw_dir = "data/processed"
        self.summary_dir = "data/summaries"
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.summary_dir, exist_ok=True)

        print("📦 Loading summarization model:", self.model_name)
        self.tokenizer = BartTokenizer.from_pretrained(self.model_name)
        self.model = BartForConditionalGeneration.from_pretrained(self.model_name).to(self.device)
        print("✅ Model loaded on:", self.device)

    # ============================================================
    # 1. Semantic Scholar (with retry + year only)
    # ============================================================
    def fetch_semantic_scholar(self, limit):
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": self.topic,
            "fields": "title,abstract,authors,year,url",
            "limit": limit
        }

        retries = 3
        delay = 3

        for attempt in range(1, retries + 1):
            try:
                r = requests.get(url, params=params, timeout=25)
                r.raise_for_status()
                data = r.json().get("data", [])
                break

            except Exception as e:
                print(f"❌ Semantic Scholar error (attempt {attempt}/{retries}):", e)
                if attempt == retries:
                    return []
                time.sleep(delay)
                delay *= 2  # exponential backoff

        papers = []
        for p in data:
            authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]

            # year only
            yr = p.get("year")
            yr = int(yr) if isinstance(yr, (int, float)) else None

            papers.append({
                "title": p.get("title") or "Untitled",
                "abstract": p.get("abstract") or "",
                "authors": authors,
                "year": yr,
                "url": p.get("url"),
                "source": "semantic_scholar"
            })

        return papers

    # ============================================================
    # 2. arXiv fallback (cs.CL + cs.AI + cs.LG)
    # ============================================================
    def fetch_arxiv(self, needed_count):
        print(f"📡 Fetching {needed_count} fallback papers from arXiv…")

        query = (
            f"all:{self.topic} AND (cat:cs.CL OR cat:cs.AI OR cat:cs.LG)"
        )
        url = f"https://export.arxiv.org/api/query?search_query={query}&start=0&max_results={needed_count}"

        try:
            r = requests.get(url, timeout=25)
            r.raise_for_status()
        except Exception as e:
            print("❌ arXiv request failed:", e)
            return []

        root = ET.fromstring(r.text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        papers = []

        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text.strip()
            abstract = entry.find("atom:summary", ns).text.strip()

            # authors
            authors = [a.find("atom:name", ns).text.strip()
                       for a in entry.findall("atom:author", ns)]

            # year only
            date = entry.find("atom:published", ns).text[:4]
            year = int(date) if date.isdigit() else None

            # URL
            url_link = entry.find("atom:id", ns).text

            papers.append({
                "title": title,
                "abstract": abstract,
                "authors": authors,
                "year": year,
                "url": url_link,
                "source": "arxiv"
            })

        return papers[:needed_count]

    # ============================================================
    # 3. Summarization
    # ============================================================
    def summarize_abstract(self, abstract, max_tokens=130, min_tokens=30):
        if not abstract.strip():
            return "No abstract available."

        inputs = self.tokenizer(
            abstract,
            max_length=1024,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        try:
            ids = self.model.generate(
                inputs["input_ids"],
                num_beams=4,
                max_length=max_tokens,
                min_length=min_tokens,
                early_stopping=True,
                no_repeat_ngram_size=3
            )
            summary = self.tokenizer.decode(ids[0], skip_special_tokens=True)
        except Exception as e:
            summary = f"[Error summarizing: {e}]"

        return summary

    # ============================================================
    # NEW → Save raw metadata in data/processed
    # ============================================================
    def save_raw_metadata(self, papers):
        safe_topic = "".join(c if c.isalnum() else "_" for c in self.topic).lower()
        out_path = os.path.join(self.raw_dir, f"{safe_topic}_raw.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved RAW metadata → {out_path}")

    # ============================================================
    # 4. Summarize all results
    # ============================================================
    def summarize_papers(self, papers):
        print("🧠 Summarizing all papers...")

        results = []
        for i, p in enumerate(papers, start=1):
            print(f"📝 ({i}/{len(papers)}) {p['title']}")
            summary = self.summarize_abstract(p["abstract"])
            p["summary"] = summary
            p["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results.append(p)

        safe_topic = "".join(c if c.isalnum() else "_" for c in self.topic).lower()
        out_path = os.path.join(self.summary_dir, f"{safe_topic}_summaries.json")

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved summarized papers → {out_path}")
        return results

    # ============================================================
    # 5. Complete pipeline
    # ============================================================
    def run(self, limit=10):
        print("🌐 Fetching main papers from Semantic Scholar…")
        ss_papers = self.fetch_semantic_scholar(limit)

        if len(ss_papers) < limit:
            needed = limit - len(ss_papers)
            print(f"⚠️ Only {len(ss_papers)} found → Need {needed} more from arXiv.")
            arxiv_papers = self.fetch_arxiv(needed)
        else:
            arxiv_papers = []

        combined = ss_papers + arxiv_papers

        if not combined:
            print("❌ No papers found from any source!")
            return []

        # ✨ NEW: save raw metadata
        self.save_raw_metadata(combined)

        # Summaries saved separately
        return self.summarize_papers(combined)
