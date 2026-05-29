import streamlit as st
import os
import time

from core.logger import log

# Gemini agents
from agents.literature_agent import LiteratureAgent
from agents.experiment_agent import ExperimentAgent
from agents.paper_agent import PaperAgent

# Groq agents
from agents.experiment_agent_groq import ExperimentAgentGroq
from agents.paper_agent_groq import PaperAgentGroq


# -----------------------------
# Streamlit Page Config
# -----------------------------
st.set_page_config(
    page_title="Autonomous Research Assistant",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Autonomous Research Assistant")
st.caption("NLP & ML Research Paper Generator")


# -----------------------------
# Sidebar Controls
# -----------------------------
st.sidebar.header("⚙️ Configuration")

mode = st.sidebar.radio(
    "Select Research Mode",
    ["NLP", "ML"]
)

# 🔥 NEW: Provider selection
provider = st.sidebar.radio(
    "Select LLM Provider",
    ["Gemini", "Groq"]
)

topic = st.sidebar.text_input(
    "Enter Research Topic",
    placeholder="e.g. Multilingual Sentiment Analysis"
)

limit = st.sidebar.number_input(
    "Number of Papers",
    min_value=1,
    max_value=30,
    value=5
)

run_button = st.sidebar.button("🚀 Run Pipeline")


# -----------------------------
# Helper Function (CLEAN DESIGN)
# -----------------------------
def get_experiment_agent(provider, literature, topic):
    if provider == "Gemini":
        return ExperimentAgent(
            summaries=literature,
            topic=topic
        )
    else:
        return ExperimentAgentGroq(
            summaries=literature,
            topic=topic
        )


def get_paper_agent(provider, literature, topic, experiments):
    if provider == "Gemini":
        return PaperAgent(
            topic=topic,
            literature=literature,
            experiments_bundle=experiments
        )
    else:
        return PaperAgentGroq(
            topic=topic,
            literature=literature,
            experiments_bundle=experiments
        )


# -----------------------------
# Main Execution
# -----------------------------
if run_button:
    if not topic.strip():
        st.error("Please enter a research topic.")
    else:
        st.success(f"Running {mode} pipeline using **{provider}** for topic: **{topic}**")

        # -----------------------------
        # Step 1: Literature
        # -----------------------------
        with st.spinner("📚 Fetching literature..."):
            lit_agent = LiteratureAgent(
                topic=topic,
                model_name="facebook/bart-large-cnn",
                mode=mode.lower()   # ✅ FIXED
            )
            literature = lit_agent.run(limit=limit)
            time.sleep(2)

        if not literature:
            st.error("No papers found. Try a different topic.")
        else:
            st.info(f"Literature analysis completed ({len(literature)} papers).")

            # -----------------------------
            # Step 2: Experiments
            # -----------------------------
            with st.spinner("🧪 Extracting experimental details..."):
                exp_agent = get_experiment_agent(provider, literature, topic)

                try:
                    experiments = exp_agent.run()

                # 🔥 AUTO FALLBACK (VERY IMPORTANT)
                except Exception as e:
                    st.warning(f"{provider} failed. Switching to Groq...")
                    exp_agent = ExperimentAgentGroq(
                        summaries=literature,
                        topic=topic
                    )
                    experiments = exp_agent.run()

                time.sleep(2)

            st.info("Experiment analysis completed.")

            # -----------------------------
            # Step 3: Paper Generation
            # -----------------------------
            with st.spinner("📝 Generating research paper..."):
                paper_agent = get_paper_agent(provider, literature, topic, experiments)

                try:
                    paper_info = paper_agent.run()

                except Exception as e:
                    st.warning(f"{provider} failed. Switching to Groq...")
                    paper_agent = PaperAgentGroq(
                        topic=topic,
                        literature=literature,
                        experiments_bundle=experiments
                    )
                    paper_info = paper_agent.run()

                pdf_path = paper_info["pdf_path"]
                txt_path = paper_info["text_path"]

            st.success("✅ Research paper generated successfully!")

            # -----------------------------
            # Downloads
            # -----------------------------
            docx_path = paper_info.get("docx_path")

            col1, col2 = st.columns(2)
            with col1:
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        st.download_button(
                            label="📥 Download PDF",
                            data=f,
                            file_name=os.path.basename(pdf_path),
                            mime="application/pdf",
                            use_container_width=True
                        )
                else:
                    st.error("PDF file not found.")
            
            with col2:
                if docx_path and os.path.exists(docx_path):
                    with open(docx_path, "rb") as f:
                        st.download_button(
                            label="📥 Download Word Doc",
                            data=f,
                            file_name=os.path.basename(docx_path),
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True
                        )
                else:
                    st.error("Word Doc not found.")

            # -----------------------------
            # Optional: Show References
            # -----------------------------
            if os.path.exists(txt_path):
                with open(txt_path, "r", encoding="utf-8") as f:
                    full_text = f.read()

                if "References" in full_text:
                    references = full_text.split("References")[-1].strip()
                    st.subheader("📚 References")
                    st.text(references)
                else:
                    st.info("No references section found.")