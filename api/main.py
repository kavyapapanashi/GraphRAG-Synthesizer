"""
FastAPI Backend for GraphRAG Research & Study Synthesizer
Wraps core/ GraphRAG logic and serves endpoints for ingestion, graph retrieval,
grounded multi-hop Q&A, comparative matrix, active-recall quizzes, and reset.
"""

import os
import sys
import glob
import shutil
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from core.pdf_parser import parse_pdf, store_chunks_in_chromadb, get_chroma_client, GeminiHybridEmbeddingFunction
from core.graph_builder import GraphBuilder
from core.retriever import HybridRetriever
from core.synthesizer import Synthesizer
from utils.sample_papers import generate_sample_papers

app = FastAPI(
    title="GraphRAG Multi-Paper Synthesizer API",
    description="Backend API for Neobrutalist Multi-Paper Research Workspace",
    version="1.0.0"
)

# Enable CORS for Vite dev server and common frontend ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_graph_data(graph) -> Dict[str, Any]:
    """Helper to convert NetworkX graph into clean JSON for frontend visualization."""
    nodes = []
    for n, d in graph.nodes(data=True):
        nodes.append({
            "id": str(n),
            "label": str(n),
            "type": d.get("type", "Model/Method"),
            "description": d.get("description", ""),
            "papers": d.get("papers", [])
        })
        
    edges = []
    for u, v, d in graph.edges(data=True):
        edges.append({
            "source": str(u),
            "target": str(v),
            "relation": d.get("relation", "RELATES_TO"),
            "details": d.get("details", ""),
            "citation": d.get("citation", f"[{d.get('source_paper', 'Paper')}, p. {d.get('page_num', 1)}]"),
            "source_paper": d.get("source_paper", ""),
            "page_num": d.get("page_num", 1)
        })
        
    return {"nodes": nodes, "edges": edges}


# Global In-Memory Pipeline State
class PipelineState:
    def __init__(self, autoload: bool = True):
        self.reset(autoload=autoload)
        
    def reset(self, autoload: bool = False):
        api_key = os.getenv("GEMINI_API_KEY")
        self.graph_builder = GraphBuilder(api_key=api_key)
        self.chroma_collection = None
        self.ingested_papers: List[str] = []
        self.all_chunks: List[Dict[str, Any]] = []
        self.total_pages: int = 0
        self.chroma_dir = "./data/chroma_db"
        # Re-initialize ChromaDB collection
        try:
            client = get_chroma_client(self.chroma_dir)
            self.chroma_collection = client.get_or_create_collection(
                name="academic_papers",
                embedding_function=GeminiHybridEmbeddingFunction(api_key=api_key)
            )
        except Exception:
            pass

        if autoload:
            self.load_benchmarks()

    def load_benchmarks(self) -> Dict[str, Any]:
        """Loads and indexes the 3 benchmark academic PDFs into state."""
        try:
            sample_paths = generate_sample_papers()
            new_chunks = []
            paper_names = []
            total_pages_added = 0

            for p in sample_paths:
                clean_name = os.path.basename(p).replace(".pdf", "")
                chunks = parse_pdf(p, clean_name)
                new_chunks.extend(chunks)
                paper_names.append(clean_name)
                
                pages_in_paper = max([c["page_num"] for c in chunks], default=1)
                total_pages_added += pages_in_paper
                
                self.graph_builder.ingest_paper(chunks, clean_name)

            api_k = os.getenv("GEMINI_API_KEY")
            chroma_res = store_chunks_in_chromadb(
                new_chunks,
                collection_name="academic_papers",
                persist_directory=self.chroma_dir,
                api_key=api_k
            )
            self.chroma_collection = chroma_res.get("collection")

            self.ingested_papers = list(set(self.ingested_papers + paper_names))
            self.all_chunks = self.all_chunks + new_chunks
            self.total_pages += total_pages_added
            print(f"[PipelineState] Ingested {len(self.ingested_papers)} papers: {len(self.all_chunks)} chunks, {self.graph_builder.graph.number_of_nodes()} nodes, {self.graph_builder.graph.number_of_edges()} edges.")
        except Exception as e:
            print(f"[PipelineState] Auto-load benchmarks note: {e}")

        return format_graph_data(self.graph_builder.graph)

state = PipelineState(autoload=True)


# Request / Response Schemas
class ChatRequest(BaseModel):
    query: str
    top_k: int = 5
    max_hops: int = 2

class QuizRequest(BaseModel):
    paper: Optional[str] = None
    session_topics: Optional[List[str]] = None
    num_questions: int = 5

class ChatResponse(BaseModel):
    answer: str
    citations: List[str]
    graph_paths: List[str]
    triples: List[Dict[str, Any]]
    chunks: List[Dict[str, Any]]

class IngestResponse(BaseModel):
    papers: List[str]
    chunks_count: int
    total_pages: int
    nodes_count: int
    edges_count: int
    graph: Dict[str, Any]

class GraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    stats: Dict[str, Any]


dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

# ------------------------------------------------------------------------------
# ENDPOINTS
# ------------------------------------------------------------------------------

@app.get("/")
def root():
    """Serves the Neobrutalist React web workspace."""
    dist_index = os.path.join(dist_dir, "index.html")
    if os.path.exists(dist_index):
        return FileResponse(dist_index, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {
        "status": "online",
        "service": "GraphRAG Multi-Paper Synthesizer API",
        "papers_ingested": len(state.ingested_papers),
        "nodes": state.graph_builder.graph.number_of_nodes(),
        "edges": state.graph_builder.graph.number_of_edges()
    }


@app.get("/api")
@app.get("/api/health")
def api_status():
    """API health and statistics status."""
    return {
        "status": "online",
        "service": "GraphRAG Multi-Paper Synthesizer API",
        "papers_ingested": len(state.ingested_papers),
        "nodes": state.graph_builder.graph.number_of_nodes(),
        "edges": state.graph_builder.graph.number_of_edges()
    }


@app.get("/api/stats")
def get_stats():
    """Returns current counts and ingested paper titles."""
    return {
        "papers": state.ingested_papers,
        "total_pages": state.total_pages,
        "chunks_count": len(state.all_chunks),
        "nodes_count": state.graph_builder.graph.number_of_nodes(),
        "edges_count": state.graph_builder.graph.number_of_edges()
    }


@app.post("/api/ingest", response_model=IngestResponse)
async def ingest_papers(files: List[UploadFile] = File(...)):
    """
    Upload 1 to 5 academic PDFs.
    Extracts text page-by-page, adds to ChromaDB, and builds the Knowledge Graph.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")
    if len(files) > 5:
        files = files[:5]

    new_chunks = []
    paper_names = []
    total_pages_added = 0

    for f in files:
        contents = await f.read()
        paper_name = f.filename or "paper.pdf"
        clean_name = os.path.basename(paper_name).replace(".pdf", "")
        
        chunks = parse_pdf(contents, paper_name)
        new_chunks.extend(chunks)
        paper_names.append(clean_name)
        
        pages_in_paper = max([c["page_num"] for c in chunks], default=1)
        total_pages_added += pages_in_paper
        
        # Ingest into NetworkX graph
        state.graph_builder.ingest_paper(chunks, clean_name)

    # Store chunks in ChromaDB
    api_k = os.getenv("GEMINI_API_KEY")
    chroma_res = store_chunks_in_chromadb(
        new_chunks,
        collection_name="academic_papers",
        persist_directory=state.chroma_dir,
        api_key=api_k
    )
    state.chroma_collection = chroma_res.get("collection")

    # Update state
    state.ingested_papers = list(set(state.ingested_papers + paper_names))
    state.all_chunks = state.all_chunks + new_chunks
    state.total_pages += total_pages_added

    graph_data = format_graph_data(state.graph_builder.graph)

    return IngestResponse(
        papers=state.ingested_papers,
        chunks_count=len(state.all_chunks),
        total_pages=state.total_pages,
        nodes_count=state.graph_builder.graph.number_of_nodes(),
        edges_count=state.graph_builder.graph.number_of_edges(),
        graph=graph_data
    )


@app.post("/api/sample", response_model=IngestResponse)
def load_sample_papers():
    """
    Loads and indexes the 3 benchmark academic PDFs:
    GraphRAG, DenseRetriever, and HybridSearch.
    """
    graph_data = state.load_benchmarks()

    return IngestResponse(
        papers=state.ingested_papers,
        chunks_count=len(state.all_chunks),
        total_pages=state.total_pages,
        nodes_count=state.graph_builder.graph.number_of_nodes(),
        edges_count=state.graph_builder.graph.number_of_edges(),
        graph=graph_data
    )


@app.get("/api/graph", response_model=GraphResponse)
def get_graph():
    """Returns the current Knowledge Graph nodes, edges, and statistics."""
    graph_data = format_graph_data(state.graph_builder.graph)
    stats = state.graph_builder.get_stats()
    return GraphResponse(
        nodes=graph_data["nodes"],
        edges=graph_data["edges"],
        stats=stats
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat_hybrid_rag(req: ChatRequest):
    """
    Performs hybrid GraphRAG retrieval (entity extraction -> 1-2 hop KG subgraph
    + top-k ChromaDB chunks) and returns a grounded synthesized response.
    """
    if state.graph_builder.graph.number_of_nodes() == 0 and not state.all_chunks:
        return ChatResponse(
            answer="No papers have been uploaded yet. Please upload 1–5 academic PDFs or click 'Load Sample Papers' to begin research.",
            citations=[],
            graph_paths=[],
            triples=[],
            chunks=[]
        )

    api_k = os.getenv("GEMINI_API_KEY")
    retriever = HybridRetriever(
        graph=state.graph_builder.graph,
        chroma_collection=state.chroma_collection,
        api_key=api_k
    )
    ret_res = retriever.retrieve(req.query, top_k_chunks=req.top_k, max_hops=req.max_hops)

    synth = Synthesizer(api_key=api_k)
    ans_res = synth.answer_query(req.query, ret_res)

    graph_paths = [t.get("formatted", "") for t in ret_res.get("triples", [])]

    return ChatResponse(
        answer=ans_res.get("answer", ""),
        citations=ans_res.get("citations", []),
        graph_paths=graph_paths,
        triples=ret_res.get("triples", []),
        chunks=ret_res.get("chunks", [])
    )


@app.get("/api/matrix")
def get_comparison_matrix():
    """
    Generates a structured side-by-side comparative table across all ingested papers,
    including metrics, limitations, and empirical contradiction/outperformance claims.
    """
    synth = Synthesizer(api_key=os.getenv("GEMINI_API_KEY"))
    matrix = synth.generate_comparison_matrix(state.graph_builder.graph, state.ingested_papers)
    return matrix


@app.post("/api/quiz")
def get_study_quiz(req: Optional[QuizRequest] = None):
    """
    Generates active-recall multiple-choice questions and study flashcards
    focused strictly on a specific paper or session topics, with exact page citations.
    """
    paper = req.paper if req else None
    session_topics = req.session_topics if req else None
    num_q = req.num_questions if req and req.num_questions else 5

    synth = Synthesizer(api_key=os.getenv("GEMINI_API_KEY"))
    quiz = synth.generate_quiz(
        state.graph_builder.graph,
        state.all_chunks,
        paper=paper,
        session_topics=session_topics,
        num_questions=num_q
    )
    return quiz


@app.post("/api/reset")
def reset_session():
    """
    Clears the current chat session and re-initializes the benchmark state
    so the new session is immediately ready to query with active knowledge graph.
    """
    state.reset(autoload=True)
    return {
        "status": "success", 
        "message": "New session created successfully.",
        "papers": state.ingested_papers,
        "nodes_count": state.graph_builder.graph.number_of_nodes(),
        "edges_count": state.graph_builder.graph.number_of_edges()
    }


# Mount static assets for React build
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_frontend(full_path: str):
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        target_file = os.path.join(dist_dir, full_path)
        if full_path and os.path.exists(target_file) and os.path.isfile(target_file):
            return FileResponse(target_file)
        return FileResponse(os.path.join(dist_dir, "index.html"))

