"""
GraphRAG Multi-Paper Research & Study Synthesizer
Main Streamlit Application
Ingests 1–5 academic PDFs, constructs an academic Knowledge Graph + ChromaDB Vector Store,
and provides an interactive research, comparison, and active-recall study workspace.
"""

import os
import io
import glob
import networkx as nx
import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

load_dotenv()

from core.pdf_parser import parse_pdf, store_chunks_in_chromadb, get_chroma_client
from core.graph_builder import GraphBuilder
from core.retriever import HybridRetriever
from core.synthesizer import Synthesizer
from utils.graph_viz import render_knowledge_graph_html
from utils.sample_papers import generate_sample_papers, SAMPLE_PAPERS_DIR

# Page Configuration
st.set_page_config(
    page_title="GraphRAG Multi-Paper Synthesizer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Light Neutral, Teal (#00A896), and Terracotta Red (#C94A4A) Palette
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header & Branding */
    .gr-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        border-radius: 12px;
        padding: 24px 28px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        border-left: 6px solid #00A896;
    }
    .gr-header h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        letter-spacing: -0.5px;
        color: #FFFFFF;
    }
    .gr-header p {
        margin: 6px 0 0 0;
        font-size: 14px;
        color: #94A3B8;
    }
    
    /* Custom Metric Badges */
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .badge-teal { background: #E6F7F5; color: #00A896; border: 1px solid #A7E8DE; }
    .badge-terracotta { background: #FDF2F2; color: #C94A4A; border: 1px solid #F8B4B4; }
    .badge-navy { background: #EDF2F7; color: #1D3557; border: 1px solid #CBD5E1; }
    .badge-amber { background: #FFFBEB; color: #D97706; border: 1px solid #FDE68A; }
    
    /* Card Container */
    .gr-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Grounded Citation Pill */
    .citation-pill {
        display: inline-block;
        background: #00A896;
        color: #FFFFFF;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
        margin: 0 2px;
    }
    
    /* Warning Box for Limitations / Contradictions */
    .warning-box {
        background: #FFF5F5;
        border-left: 4px solid #C94A4A;
        padding: 12px 16px;
        border-radius: 6px;
        color: #7B1E1E;
        font-size: 13px;
        margin: 10px 0;
    }
    
    /* Button Tweaks */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    
    /* Active Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #E6F7F5 !important;
        color: #00A896 !important;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Initialize Session State
if "graph_builder" not in st.session_state:
    st.session_state.graph_builder = GraphBuilder()
if "chroma_collection" not in st.session_state:
    st.session_state.chroma_collection = None
if "ingested_papers" not in st.session_state:
    st.session_state.ingested_papers = []
if "all_chunks" not in st.session_state:
    st.session_state.all_chunks = []
if "total_pages" not in st.session_state:
    st.session_state.total_pages = 0
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_score" not in st.session_state:
    st.session_state.quiz_score = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = {}
if "flashcard_idx" not in st.session_state:
    st.session_state.flashcard_idx = 0
if "show_flashcard_back" not in st.session_state:
    st.session_state.show_flashcard_back = False


# Sidebar: Pipeline Status & Configuration
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/tree-structure.png", width=54)
    st.title("GraphRAG Pipeline")
    st.caption("Neuro-Symbolic Multi-Paper Synthesis")
    
    # API Key Configuration
    st.subheader("🔑 Gemini API Key")
    env_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "API Key (Optional)",
        value=env_key,
        type="password",
        help="Used for Gemini Structured Outputs and generative synthesis. If empty, the pipeline runs using deterministic semantic vector and rule-based extraction."
    )
    if api_key_input != env_key:
        os.environ["GEMINI_API_KEY"] = api_key_input
        st.session_state.graph_builder = GraphBuilder(api_key=api_key_input)
        
    api_status = "Active (Gemini 2.5 Flash)" if api_key_input else "Offline / Heuristic Engine Active"
    st.caption(f"Status: **{api_status}**")
    
    st.divider()
    
    # Pipeline Metrics Counter
    st.subheader("📊 Knowledge Base Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Papers", len(st.session_state.ingested_papers))
        st.metric("Pages", st.session_state.total_pages)
    with col2:
        st.metric("Chunks", len(st.session_state.all_chunks))
        st.metric("KG Nodes", st.session_state.graph_builder.graph.number_of_nodes())
    st.metric("KG Edges (Fact Triples)", st.session_state.graph_builder.graph.number_of_edges())
    
    if st.session_state.ingested_papers:
        st.write("**Ingested Papers:**")
        for p in st.session_state.ingested_papers:
            st.markdown(f"- 📄 `{p}`")
            
    st.divider()
    
    # Clear / Reset Pipeline
    if st.button("🗑️ Reset Pipeline & Clear Data", use_container_width=True):
        st.session_state.graph_builder = GraphBuilder(api_key=api_key_input)
        st.session_state.chroma_collection = None
        st.session_state.ingested_papers = []
        st.session_state.all_chunks = []
        st.session_state.total_pages = 0
        st.session_state.quiz_data = None
        st.session_state.user_answers = {}
        st.session_state.flashcard_idx = 0
        st.success("Pipeline reset successfully.")
        st.rerun()


# Ingestion Helper Function
def process_uploaded_files(files_or_paths, is_file_objects=True):
    """Processes 1–5 PDF papers, chunks text with page indices, builds KG and updates ChromaDB."""
    gb = st.session_state.graph_builder
    api_k = os.getenv("GEMINI_API_KEY")
    new_chunks = []
    paper_names = []
    total_pages_added = 0
    
    progress_bar = st.progress(0, text="Initializing ingestion pipeline...")
    total_files = len(files_or_paths)
    
    for idx, f in enumerate(files_or_paths):
        paper_name = f.name if is_file_objects else os.path.basename(f)
        progress_bar.progress((idx) / total_files, text=f"Parsing PDF: {paper_name}...")
        
        # Parse PDF page-by-page
        chunks = parse_pdf(f, paper_name)
        new_chunks.extend(chunks)
        paper_names.append(paper_name.replace(".pdf", ""))
        
        # Count pages
        pages_in_paper = max([c["page_num"] for c in chunks], default=1)
        total_pages_added += pages_in_paper
        
        # Ingest into Knowledge Graph with cross-paper merging
        progress_bar.progress((idx + 0.5) / total_files, text=f"Extracting Knowledge Graph triples for {paper_name}...")
        gb.ingest_paper(chunks, paper_name)
        
    progress_bar.progress(0.9, text="Upserting raw chunks into ChromaDB vector store...")
    chroma_res = store_chunks_in_chromadb(
        new_chunks,
        collection_name="academic_papers",
        persist_directory="./data/chroma_db",
        api_key=api_k
    )
    
    # Update Session State
    st.session_state.ingested_papers = list(set(st.session_state.ingested_papers + paper_names))
    st.session_state.all_chunks = st.session_state.all_chunks + new_chunks
    st.session_state.total_pages += total_pages_added
    st.session_state.chroma_collection = chroma_res.get("collection")
    
    # Pre-generate active-recall study quiz
    synth = Synthesizer(api_key=api_k)
    st.session_state.quiz_data = synth.generate_quiz(gb.graph, st.session_state.all_chunks)
    
    progress_bar.progress(1.0, text="Ingestion complete!")
    st.toast(f"Successfully indexed {len(paper_names)} papers and {len(new_chunks)} chunks!", icon="✅")


# App Header Banner
st.markdown("""
<div class="gr-header">
    <h1>🕸️ GraphRAG Multi-Paper Research & Study Synthesizer</h1>
    <p>Hybrid Knowledge Graph + Vector Store Retrieval for Multi-Hop Academic Literature Synthesis with Strict Citation Grounding.</p>
</div>
""", unsafe_allow_html=True)


# Main Tabs Navigation
tab1, tab2, tab3, tab4 = st.tabs([
    "📚 Tab 1: Ingestion & KG Studio",
    "🔍 Tab 2: Hybrid GraphRAG Q&A",
    "⚖️ Tab 3: Comparative Matrix",
    "🧠 Tab 4: Active-Recall Study Hub"
])


# ==============================================================================
# TAB 1: INGESTION & KNOWLEDGE GRAPH STUDIO
# ==============================================================================
with tab1:
    st.subheader("📚 Multi-Paper Ingestion & Knowledge Graph Studio")
    st.write("Upload 1 to 5 academic research PDFs or load pre-bundled benchmark papers to construct the traceable Knowledge Graph.")
    
    col_upload, col_sample = st.columns([2.2, 1.2])
    
    with col_upload:
        st.markdown('<div class="gr-card">', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Upload Academic PDFs (1–5 papers):",
            type=["pdf"],
            accept_multiple_files=True,
            help="PyMuPDF will extract page-accurate paragraphs with exact citation metadata."
        )
        
        if uploaded_files:
            if len(uploaded_files) > 5:
                st.warning("⚠️ Maximum 5 papers allowed. Only the first 5 will be ingested.")
                uploaded_files = uploaded_files[:5]
                
            if st.button("🚀 Ingest Uploaded Papers", type="primary", use_container_width=True):
                with st.spinner("Ingesting PDFs and constructing Knowledge Graph..."):
                    process_uploaded_files(uploaded_files, is_file_objects=True)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_sample:
        st.markdown('<div class="gr-card">', unsafe_allow_html=True)
        st.markdown("##### ⚡ Quick Benchmark Test")
        st.caption("Load 3 multi-page benchmark AI/NLP papers (`GraphRAG`, `DenseRetriever`, `HybridSearch`) with metrics, datasets, and contradictions.")
        if st.button("📥 Load 3 Sample Benchmark Papers", use_container_width=True):
            with st.spinner("Generating and ingesting benchmark PDFs..."):
                sample_pdf_paths = generate_sample_papers()
                process_uploaded_files(sample_pdf_paths, is_file_objects=False)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    # Knowledge Graph Interactive Viewer
    st.subheader("🕸️ Traceable Knowledge Graph Viewer")
    
    # Legend & Filters Bar
    col_filter, col_legend = st.columns([1.5, 2.5])
    with col_filter:
        node_type_filter = st.multiselect(
            "Filter by Node Category:",
            options=["Paper", "Model/Method", "Dataset", "Metric", "Limitation"],
            default=["Paper", "Model/Method", "Dataset", "Metric", "Limitation"],
            help="Toggle specific entity types to focus your graph exploration."
        )
        physics_toggle = st.toggle("Enable Dynamic Physics Simulation", value=True)
        
    with col_legend:
        st.markdown("""
        **Entity Legend & Color Coding:**  
        <span class="metric-badge badge-navy">■ Paper (Navy Box)</span>
        <span class="metric-badge badge-teal">● Model/Method (Teal Circle)</span>
        <span class="metric-badge badge-amber">⛁ Dataset (Amber Database)</span>
        <span class="metric-badge" style="background:#E6F7F0; color:#2A9D8F; border:1px solid #A3E0D8;">◆ Metric (Mint Diamond)</span>
        <span class="metric-badge badge-terracotta">▲ Limitation (Terracotta Triangle)</span>
        """, unsafe_allow_html=True)
        st.caption("💡 **Tip:** Hover over nodes and edges to inspect exact page citations e.g. `[Paper_Name, p. 3]`, quantitative scores, and source papers.")

    # Render Graph Component
    graph = st.session_state.graph_builder.graph
    filter_set = set(node_type_filter) if node_type_filter else None
    
    kg_html = render_knowledge_graph_html(
        graph=graph,
        filter_node_types=filter_set,
        height="560px",
        physics_enabled=physics_toggle
    )
    components.html(kg_html, height=580, scrolling=False)

    # Graph Statistics Breakdown
    if graph.number_of_nodes() > 0:
        stats = st.session_state.graph_builder.get_stats()
        with st.expander("📈 Detailed Knowledge Graph Topology & Hub Entities", expanded=False):
            col_s1, col_s2, col_s3 = st.columns(3)
            with col_s1:
                st.write("**Entity Distribution:**")
                st.json(stats["node_types"])
            with col_s2:
                st.write("**Relation Distribution:**")
                st.json(stats["edge_types"])
            with col_s3:
                st.write("**Top Hub Entities (Highest Degree):**")
                for hub, deg in stats["top_hubs"]:
                    st.write(f"- `{hub}`: **{deg}** connections")


# ==============================================================================
# TAB 2: HYBRID GRAPHRAG SEARCH & Q&A
# ==============================================================================
with tab2:
    st.subheader("🔍 Hybrid GraphRAG Retrieval & Grounded Q&A")
    st.write("Ask complex multi-hop research questions across your ingested papers. Every response strictly enforces inline citations `[Paper, p. X]`.")
    
    # Query Input & Options
    col_q, col_opts = st.columns([3, 1.2])
    with col_q:
        preset_queries = [
            "Select or write your own research question...",
            "What datasets are evaluated across the papers and what metrics were achieved?",
            "What are the stated computational limitations and bottlenecks of GraphRAG?",
            "Compare the latency and retrieval accuracy of DenseRetriever vs GraphRAG.",
            "Are there any contradictory findings or outperformance claims between the methods?"
        ]
        selected_preset = st.selectbox("Quick Query Presets:", preset_queries)
        
        initial_val = "" if selected_preset.startswith("Select or write") else selected_preset
        user_query = st.text_input(
            "Enter Research Question:",
            value=initial_val,
            placeholder="e.g. Which model achieves the highest Recall@10 on HotpotQA and what are its memory limitations?"
        )
        
    with col_opts:
        st.markdown('<div class="gr-card">', unsafe_allow_html=True)
        st.markdown("##### ⚙️ Retrieval Parameters")
        top_k = st.slider("ChromaDB Chunks (top-k):", min_value=1, max_value=10, value=5)
        max_hops = st.radio("KG Subgraph Hops:", options=[1, 2], index=1, horizontal=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    search_clicked = st.button("🔎 Run Hybrid GraphRAG Query", type="primary", use_container_width=False)
    
    if (search_clicked or user_query) and user_query:
        if st.session_state.graph_builder.graph.number_of_nodes() == 0:
            st.warning("⚠️ No papers have been ingested yet. Please ingest PDFs in Tab 1 first.")
        else:
            with st.spinner("Extracting query entities, traversing 1-2 hop Knowledge Graph, and querying ChromaDB..."):
                retriever = HybridRetriever(
                    graph=st.session_state.graph_builder.graph,
                    chroma_collection=st.session_state.chroma_collection,
                    api_key=os.getenv("GEMINI_API_KEY")
                )
                ret_res = retriever.retrieve(user_query, top_k_chunks=top_k, max_hops=max_hops)
                
                synth = Synthesizer(api_key=os.getenv("GEMINI_API_KEY"))
                ans_res = synth.answer_query(user_query, ret_res)
                
            # Grounded Answer Presentation
            st.markdown('<div class="gr-card">', unsafe_allow_html=True)
            st.markdown("### 💬 Grounded Synthesizer Response")
            st.markdown(ans_res["answer"])
            
            # Citation Badges
            if ans_res["citations"]:
                st.markdown("---")
                st.markdown("**Exact Verification Citations:**")
                for cit in ans_res["citations"]:
                    st.markdown(f'<span class="citation-pill">📌 {cit}</span>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Traceable Evidence Breakdown
            st.subheader("🔬 Retrieved Evidence Inspection")
            col_ev1, col_ev2 = st.columns([1.3, 1])
            
            with col_ev1:
                st.markdown("##### 🕸️ Retrieved 1-2 Hop Subgraph Facts")
                st.caption(f"Matched Query Entities: **{', '.join(ret_res['entities']) if ret_res['entities'] else 'Semantic traversal'}**")
                if ret_res["triples"]:
                    # Mini PyVis Subgraph Viewer
                    subgraph_html = render_knowledge_graph_html(
                        graph=ret_res["subgraph"],
                        height="320px",
                        physics_enabled=False
                    )
                    components.html(subgraph_html, height=330, scrolling=False)
                    
                    with st.expander("📋 View Structured Fact Triples List", expanded=False):
                        for t in ret_res["triples"]:
                            st.markdown(f"{t['formatted']}")
                else:
                    st.info("No explicit 1-2 hop graph connections for this specific entity query.")
                    
            with col_ev2:
                st.markdown(f"##### 📄 Retrieved ChromaDB Chunks ({len(ret_res['chunks'])})")
                st.caption("Top passages ranked by dense vector semantic similarity distance:")
                for idx, c in enumerate(ret_res["chunks"], 1):
                    with st.expander(f"Chunk {idx}: {c['citation']} (dist: {c['distance']:.3f})", expanded=(idx==1)):
                        st.markdown(f"> \"{c['text']}\"")
                        st.caption(f"Chunk ID: `{c['chunk_id']}` | Page: `{c['page_num']}`")


# ==============================================================================
# TAB 3: COMPARATIVE MATRIX & BENCHMARKS
# ==============================================================================
with tab3:
    st.subheader("⚖️ Multi-Paper Comparative Matrix & Empirical Benchmarks")
    st.write("Side-by-side synthesis comparing proposed architectures, evaluation datasets, empirical scores, and critical limitations.")
    
    if st.session_state.graph_builder.graph.number_of_nodes() == 0:
        st.info("💡 Ingest papers in Tab 1 to generate the multi-paper comparative matrix.")
    else:
        synth = Synthesizer(api_key=os.getenv("GEMINI_API_KEY"))
        matrix_data = synth.generate_comparison_matrix(st.session_state.graph_builder.graph)
        
        # 1. Comparative Matrix Table
        st.markdown("##### 📋 Cross-Paper Comparison Matrix")
        df_matrix = pd.DataFrame(matrix_data["matrix_rows"])
        if not df_matrix.empty:
            st.dataframe(df_matrix, use_container_width=True, hide_index=True)
        else:
            st.info("No comparative rows could be constructed from current graph.")
            
        st.divider()
        
        # 2. Plotly Benchmark Metrics Chart
        col_chart, col_conflicts = st.columns([1.6, 1.2])
        
        with col_chart:
            st.markdown("##### 📊 Benchmark Metric Scores Comparison")
            metrics_plot = matrix_data["metrics_plot_data"]
            if metrics_plot:
                df_plot = pd.DataFrame(metrics_plot)
                fig = px.bar(
                    df_plot,
                    x="Metric",
                    y="Score",
                    color="Model",
                    barmode="group",
                    text="Score",
                    hover_data=["Paper", "Details", "Citation"],
                    color_discrete_sequence=["#00A896", "#1D3557", "#F4A261", "#C94A4A"],
                    title="Empirical Metric Comparison Across Models & Papers"
                )
                fig.update_layout(
                    paper_bgcolor="#FAFAFB",
                    plot_bgcolor="#FFFFFF",
                    font=dict(family="Inter, sans-serif", size=12),
                    margin=dict(l=40, r=40, t=50, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quantitative metric values detected for plotting.")
                
        with col_conflicts:
            st.markdown("##### ⚠️ Outperformance & Contradiction Tracker")
            
            # Contradictions
            contradictions = matrix_data["contradictions"]
            if contradictions:
                st.markdown("**Empirical Contradictions / Divergent Findings:**")
                for c in contradictions:
                    st.markdown(f"""
                    <div class="warning-box">
                        <b>🚨 {c['source']} CONTRADICTS {c['target']}</b><br/>
                        <span>{c['details']}</span><br/>
                        <small><b>Citation:</b> {c['citation']}</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.caption("No explicit contradictory claims recorded in the knowledge graph.")
                
            # Outperformance Claims
            outperforms = matrix_data["outperforms"]
            if outperforms:
                st.markdown("**Documented Outperformance Relations:**")
                for o in outperforms:
                    st.markdown(f"""
                    <div style="background:#F0FDF4; border-left:4px solid #2A9D8F; padding:8px 12px; border-radius:6px; margin-bottom:8px; font-size:13px;">
                        <b>🏆 {o['source']} OUTPERFORMS {o['target']}</b><br/>
                        <span>{o['details']}</span><br/>
                        <small><b>Citation:</b> {o['citation']}</small>
                    </div>
                    """, unsafe_allow_html=True)


# ==============================================================================
# TAB 4: ACTIVE-RECALL STUDY HUB & QUIZ GENERATOR
# ==============================================================================
with tab4:
    st.subheader("🧠 Active-Recall Study Hub & Quiz Generator")
    st.write("Reinforce retention and test your research understanding using grounded flashcards and active-recall multiple choice quizzes.")
    
    if not st.session_state.quiz_data or (not st.session_state.quiz_data.get("questions") and not st.session_state.quiz_data.get("flashcards")):
        st.info("💡 Ingest research papers in Tab 1 or click the button below to generate study materials.")
        if st.button("✨ Generate Active-Recall Study Materials", type="primary"):
            with st.spinner("Generating grounded study quiz from Knowledge Graph..."):
                synth = Synthesizer(api_key=os.getenv("GEMINI_API_KEY"))
                st.session_state.quiz_data = synth.generate_quiz(
                    st.session_state.graph_builder.graph,
                    st.session_state.all_chunks
                )
                st.rerun()
    else:
        study_mode = st.radio(
            "Select Study Mode:",
            options=["📝 Multiple-Choice Quiz", "🗂️ Interactive Flashcards"],
            horizontal=True
        )
        
        # MODE 1: MULTIPLE-CHOICE QUIZ
        if study_mode == "📝 Multiple-Choice Quiz":
            questions = st.session_state.quiz_data.get("questions", [])
            st.markdown(f"#### 📝 Active-Recall Quiz ({len(questions)} Questions)")
            
            for idx, q in enumerate(questions):
                st.markdown('<div class="gr-card">', unsafe_allow_html=True)
                
                # Limitation warning badge if question touches on limitations
                if q.get("is_limitation_warning"):
                    st.markdown('<span class="metric-badge badge-terracotta">⚠️ Limitation & Caveat Focus</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="metric-badge badge-teal">📖 Empirical Fact</span>', unsafe_allow_html=True)
                    
                st.markdown(f"**Q{idx + 1}: {q['question']}**")
                
                options = q.get("options", [])
                radio_key = f"q_{idx}"
                user_choice = st.radio(
                    f"Select your answer for Q{idx + 1}:",
                    options=options,
                    key=radio_key,
                    index=None,
                    label_visibility="collapsed"
                )
                
                check_btn = st.button(f"Submit Answer Q{idx + 1}", key=f"btn_{idx}")
                if check_btn and user_choice:
                    user_idx = options.index(user_choice)
                    correct_idx = q.get("correct_index", 0)
                    
                    if user_idx == correct_idx:
                        st.success(f"✅ **Correct!** {q['explanation']}")
                    else:
                        st.error(f"❌ **Incorrect.** The correct answer is: **{options[correct_idx]}**\n\n{q['explanation']}")
                        
                    st.markdown(f'<span class="citation-pill">Source Citation: {q.get("citation", "Ground Truth")}</span>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

        # MODE 2: INTERACTIVE FLASHCARDS
        else:
            flashcards = st.session_state.quiz_data.get("flashcards", [])
            st.markdown(f"#### 🗂️ Knowledge Graph Flashcards ({len(flashcards)} Cards)")
            
            if flashcards:
                cur_idx = st.session_state.flashcard_idx % len(flashcards)
                card = flashcards[cur_idx]
                
                col_nav1, col_center, col_nav2 = st.columns([1, 4, 1])
                
                with col_nav1:
                    if st.button("⬅️ Previous", use_container_width=True):
                        st.session_state.flashcard_idx = (st.session_state.flashcard_idx - 1) % len(flashcards)
                        st.session_state.show_flashcard_back = False
                        st.rerun()
                        
                with col_nav2:
                    if st.button("Next ➡️", use_container_width=True):
                        st.session_state.flashcard_idx = (st.session_state.flashcard_idx + 1) % len(flashcards)
                        st.session_state.show_flashcard_back = False
                        st.rerun()
                        
                with col_center:
                    st.markdown(f"<div style='text-align:center; color:#64748B; font-size:12px; margin-bottom:6px;'>Card {cur_idx + 1} of {len(flashcards)}</div>", unsafe_allow_html=True)
                    
                    # Flashcard Box
                    st.markdown(f"""
                    <div style="background:#FFFFFF; border:2px solid {'#C94A4A' if card.get('tag')=='Limitation' else '#00A896'}; 
                                border-radius:12px; padding:32px 24px; text-align:center; min-height:180px; 
                                display:flex; flex-direction:column; justify-content:center; align-items:center; box-shadow:0 4px 6px rgba(0,0,0,0.05);">
                        <span class="metric-badge {'badge-terracotta' if card.get('tag')=='Limitation' else 'badge-teal'}" style="margin-bottom:12px;">
                            {card.get('tag', 'Concept')}
                        </span>
                        <h3 style="color:#0F172A; margin:0 0 12px 0;">{card.get('front', '')}</h3>
                        {'<div style="margin-top:16px; padding-top:16px; border-top:1px dashed #CBD5E1; color:#334155; font-size:16px;"><b>Answer:</b> ' + card.get('back', '') + '</div>' if st.session_state.show_flashcard_back else ''}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Flip Button
                    btn_label = "Hide Answer 🔄" if st.session_state.show_flashcard_back else "Reveal Answer 🔍"
                    if st.button(btn_label, type="primary", use_container_width=True):
                        st.session_state.show_flashcard_back = not st.session_state.show_flashcard_back
                        st.rerun()
                        
                    if st.session_state.show_flashcard_back and card.get("citation"):
                        st.markdown(f"<div style='text-align:center; margin-top:8px;'><span class='citation-pill'>Citation: {card['citation']}</span></div>", unsafe_allow_html=True)
