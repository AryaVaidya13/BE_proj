# agents/paper_agent.py
import os
import json
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from typing import List, Dict

# --------------------- Font Setup ---------------------
try:
    pdfmetrics.registerFont(TTFont("TimesNewRoman", "times.ttf"))
    DEFAULT_FONT = "TimesNewRoman"
except:
    DEFAULT_FONT = "Helvetica"

# --------------------- Dynamic PaperAgent ---------------------
class PaperAgent:
    def __init__(self, literature: List[Dict], topic: str, experiments_bundle: Dict = None, output_dir: str = "outputs"):
        self.literature = literature or []
        self.topic = topic or "Generated_Paper"
        self.experiments_bundle = experiments_bundle or {}
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)

    # --------------------- Safe Title ---------------------
    def _extract_title(self, text: str):
        title = re.search(r"# (.+)", text)
        if title:
            safe = re.sub(r"[^A-Za-z0-9]+", "_", title.group(1).strip())
            return safe or "Generated_Paper"
        return "Generated_Paper"

    # --------------------- Abstract ---------------------
    def _generate_abstract(self):
        abstract = f"This paper investigates {self.topic}. "
        if self.literature:
            abstract += f"Based on {len(self.literature)} studies, we synthesize key findings and analyze methodologies. "
        if self.experiments_bundle.get("experiments"):
            abstract += f"{len(self.experiments_bundle['experiments'])} experiments illustrate trends, challenges, and results. "
        abstract += "We highlight gaps in current approaches and propose potential directions for future research."
        return abstract

    # --------------------- Introduction ---------------------
    def _generate_introduction(self):
        intro = f"The study of {self.topic} has gained significant attention in recent years. "
        if self.literature:
            top_papers = self.literature[:3]
            paper_summaries = []
            for p in top_papers:
                authors = ", ".join(p.get("authors", ["Unknown"]))
                title = p.get("title", "Untitled")
                paper_summaries.append(f"{title} by {authors}")
            intro += "Previous research includes " + "; ".join(paper_summaries) + ". "
        intro += ("Despite these efforts, challenges remain in addressing bias, performance disparities, "
                  "and limitations in experimental methodologies. This paper synthesizes findings from multiple studies, "
                  "provides a comprehensive overview of experimental results, and identifies directions for improving model robustness and fairness.")
        return intro

    # --------------------- Literature Review ---------------------
    def _literature_review_to_markdown(self):
        if not self.literature:
            return "No literature available.\n"
        
        md = f"Multilingual Large Language Models (LLMs) have been examined in {len(self.literature)} studies focusing on performance, bias, and fairness [1-{len(self.literature)}].\n\n"
        themes = ["Performance disparities", "Bias in data", "Annotation bias", "Offensive language detection"]
        dynamic_text = [
            "Models often perform differently across high- and low-resource languages, revealing disparities.",
            "LLMs inherit social and cultural biases from training datasets, influencing predictions for underrepresented groups.",
            "Annotation processes vary based on annotators' background, introducing cultural biases into datasets.",
            "Detecting offensive language is challenging across languages due to cultural and linguistic variations."
        ]
        for theme, text in zip(themes, dynamic_text):
            md += f"**{theme}:** {text}\n\n"
        md += "Overall, these studies highlight limitations and provide potential directions for future multilingual LLM research.\n"
        return md

    # --------------------- Methodology & Experiments ---------------------
    def _experiments_to_markdown(self):
        experiments = self.experiments_bundle.get("experiments", [])
        if not experiments:
            return "No experiments available.\n"

        md = f"To evaluate {self.topic}, {len(experiments)} experiments were conducted using multiple LLMs, datasets, and languages.\n\n"
        for i, exp in enumerate(experiments, start=1):
            md += f"### Experiment {i}: {exp.get('paper_title', 'Untitled')}\n"
            if exp.get("datasets"):
                md += f"- **Dataset(s):** {', '.join(exp['datasets'])}\n"
            if exp.get("models_used"):
                md += f"- **Models:** {', '.join(exp['models_used'])}\n"
            if exp.get("training_setup"):
                md += f"- **Training Setup:** {exp['training_setup']}\n"
            if exp.get("metrics"):
                md += f"- **Metrics:** {', '.join(exp['metrics'])}\n"
            if exp.get("key_results"):
                md += f"- **Key Results:** {exp['key_results']}\n"
            md += "\n"
        return md

    # --------------------- Results and Discussion ---------------------
    def _build_results_section(self):
        experiments = self.experiments_bundle.get("experiments", [])
        if not experiments:
            return "No experimental results to discuss.\n"

        insights = [
            "Performance varies significantly across tasks, datasets, and languages.",
            "High-resource languages consistently achieve better outcomes than low-resource languages.",
            "Bias patterns are observed based on dataset and model choices, emphasizing the need for mitigation strategies.",
            "Cross-lingual performance often reveals hidden disparities that monolingual evaluations might miss."
        ]
        return " ".join(insights)

    # --------------------- Conclusion ---------------------
    def _build_conclusion_section(self):
        num_studies = len(self.literature)
        num_experiments = len(self.experiments_bundle.get("experiments", []))
        conclusion = f"In conclusion, this paper presents a detailed analysis of {self.topic}. "
        if num_studies:
            conclusion += f"Based on {num_studies} studies, trends, challenges, and methodologies were identified. "
        if num_experiments:
            conclusion += f"{num_experiments} experiments revealed performance variations and bias patterns. "
        conclusion += ("These findings highlight the need for improved datasets, dynamic evaluation methods, and effective bias mitigation strategies, "
                       "laying a foundation for future research in multilingual LLMs.")
        return conclusion

    # --------------------- References ---------------------
    def _build_references_section(self):
        if not self.literature:
            return "References\nNo literature available.\n"
        refs = ["References\n"]
        for i, p in enumerate(self.literature, start=1):
            title = p.get("title", "Untitled Title")
            authors = ", ".join(p.get("authors", ["Unknown Authors"]))
            year = p.get("year", "n.d.")
            refs.append(f"[{i}] {authors}. ({year}). {title}.")
        return "\n".join(refs)

    # --------------------- Markdown to HTML ---------------------
    def _markdown_to_html(self, text):
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        text = re.sub(r"\*(?!\*)(.+?)\*", r"<i>\1</i>", text)
        return text

    # --------------------- Save PDF ---------------------
    def _save_pdf(self, markdown_text: str):
        safe_title = self._extract_title(markdown_text)
        pdf_path = os.path.join(self.output_dir, f"{safe_title}_paper.pdf")
        markdown_text = self._markdown_to_html(markdown_text)

        styles = getSampleStyleSheet()
        base = ParagraphStyle("Base", parent=styles["Normal"], fontName=DEFAULT_FONT,
                              fontSize=11, leading=15, alignment=TA_JUSTIFY)
        title_style = ParagraphStyle("Title", parent=base, fontSize=22, leading=28,
                                     alignment=TA_CENTER, spaceAfter=20)
        h1 = ParagraphStyle("H1", parent=base, fontSize=18, leading=22, spaceBefore=12, spaceAfter=10)
        h2 = ParagraphStyle("H2", parent=base, fontSize=15, leading=20, spaceBefore=10, spaceAfter=6)

        story = []
        for line in markdown_text.split("\n"):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 0.18 * inch))
                continue
            if line.startswith("# "):
                story.append(Paragraph(line[2:], title_style))
            elif line.startswith("## "):
                story.append(Paragraph(line[3:], h1))
            elif line.startswith("### "):
                story.append(Paragraph(line[4:], h2))
            elif line.startswith("- "):
                story.append(Paragraph("• " + line[2:], base))
            else:
                story.append(Paragraph(line, base))

        doc = SimpleDocTemplate(pdf_path, pagesize=A4, leftMargin=50, rightMargin=50, topMargin=60, bottomMargin=50)
        doc.build(story)
        print(f"📄 PDF saved → {pdf_path}")
        return pdf_path

    # --------------------- Generate Paper ---------------------
    def generate_paper(self):
        paper_md = f"# {self.topic}\n\n"
        paper_md += f"## Abstract\n{self._generate_abstract()}\n\n"
        paper_md += f"## Introduction\n{self._generate_introduction()}\n\n"
        paper_md += f"## Literature Review\n{self._literature_review_to_markdown()}\n\n"
        paper_md += f"## Methodology and Experiments\n{self._experiments_to_markdown()}\n\n"
        paper_md += f"## Results and Discussion\n{self._build_results_section()}\n\n"
        paper_md += f"## Conclusion\n{self._build_conclusion_section()}\n\n"
        paper_md += self._build_references_section()

        safe_title = self._extract_title(paper_md)
        md_path = os.path.join(self.output_dir, f"{safe_title}_paper.md")
        json_path = os.path.join(self.output_dir, f"{safe_title}_paper.json")

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(paper_md)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({"paper_markdown": paper_md}, f, indent=2, ensure_ascii=False)

        pdf_path = self._save_pdf(paper_md)
        return {"md_path": md_path, "pdf_path": pdf_path, "json_path": json_path}

    # --------------------- Run ---------------------
    def run(self):
        return self.generate_paper()
