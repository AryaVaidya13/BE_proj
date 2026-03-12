import streamlit as st
import os

from core.logger import log
from agents.literature_agent import LiteratureAgent
from agents.experiment_agent import ExperimentAgent
from agents.paper_agent import PaperAgent

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
# Main Execution
# -----------------------------
if run_button:
    if not topic.strip():
        st.error("Please enter a research topic.")
    else:
        st.success(f"Running {mode} pipeline for topic: **{topic}**")

        # -----------------------------
        # Step 1: Literature
        # -----------------------------
        with st.spinner("📚 Fetching literature..."):
            lit_agent = LiteratureAgent(
                topic=topic,
                model_name="facebook/bart-large-cnn"
            )
            literature = lit_agent.run(limit=limit)

        if not literature:
            st.error("No papers found. Try a different topic.")
        else:
            st.info(f"Literature analysis completed ({len(literature)} papers).")

            # -----------------------------
            # Step 2: Experiments
            # -----------------------------
            with st.spinner("🧪 Extracting experimental details..."):
                exp_agent = ExperimentAgent(
                    summaries=literature,
                    topic=topic
                )
                experiments = exp_agent.run()

            st.info("Experiment analysis completed.")

            # -----------------------------
            # Step 3: Paper Generation
            # -----------------------------
            with st.spinner("📝 Generating research paper..."):
                paper_agent = PaperAgent(
                    topic=topic,
                    literature=literature,
                    experiments_bundle=experiments
                )
                paper_info = paper_agent.run()
                pdf_path = paper_info["pdf_path"]
                txt_path = paper_info["text_path"]

            st.success("✅ Research paper generated successfully!")

            # -----------------------------
            # PDF Download
            # -----------------------------
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download Research Paper (PDF)",
                        data=f,
                        file_name=os.path.basename(pdf_path),
                        mime="application/pdf"
                    )
            else:
                st.error("PDF file not found.")

            # -----------------------------
            # Display References
            # -----------------------------
            # if os.path.exists(txt_path):
            #     with open(txt_path, "r", encoding="utf-8") as f:
            #         full_text = f.read()

            #     if "References" in full_text:
            #         references = full_text.split("References")[-1].strip()
            #         st.subheader("📚 References")
            #         st.text(references)
            #     else:
            #         st.info("No references section found in the generated paper.")
