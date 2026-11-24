"""
End-to-End Verification Test Suite for GraphRAG Pipeline
Validates PDF parsing, Knowledge Graph extraction, ChromaDB vector indexing,
1-2 hop hybrid retrieval, synthesis with citations, and PyVis HTML rendering.
"""

import os
import shutil
import unittest
import networkx as nx

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

from utils.sample_papers import generate_sample_papers, SAMPLE_PAPERS_DIR
from core.pdf_parser import parse_pdf, store_chunks_in_chromadb, get_chroma_client
from core.graph_builder import GraphBuilder, normalize_entity_name
from core.retriever import HybridRetriever
from core.synthesizer import Synthesizer
from utils.graph_viz import render_knowledge_graph_html


class TestGraphRAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_dir = "./data/test_run"
        os.makedirs(cls.test_dir, exist_ok=True)
        cls.papers = generate_sample_papers()

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_dir):
            shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_01_sample_papers_generated(self):
        """Verify that all 3 academic benchmark PDFs are generated and valid."""
        self.assertEqual(len(self.papers), 3)
        for p in self.papers:
            self.assertTrue(os.path.exists(p))
            self.assertTrue(os.path.getsize(p) > 1000)

    def test_02_pdf_parser_page_accuracy(self):
        """Verify PyMuPDF page-accurate chunking and metadata preservation."""
        p1 = self.papers[0]
        chunks = parse_pdf(p1, "GraphRAG_Reasoning.pdf")
        self.assertGreater(len(chunks), 4)
        
        # Check metadata fields
        first_chunk = chunks[0]
        self.assertIn("chunk_id", first_chunk)
        self.assertIn("paper_name", first_chunk)
        self.assertIn("page_num", first_chunk)
        self.assertIn("text", first_chunk)
        self.assertEqual(first_chunk["page_num"], 1)
        self.assertTrue(first_chunk["chunk_id"].startswith("GraphRAG_Reasoning_p1_"))

    def test_03_chromadb_storage(self):
        """Verify storing and querying chunks in local ChromaDB."""
        chunks = parse_pdf(self.papers[0], "GraphRAG_Reasoning.pdf")
        chroma_dir = os.path.join(self.test_dir, "chroma")
        res = store_chunks_in_chromadb(chunks, collection_name="test_col", persist_directory=chroma_dir)
        self.assertEqual(res["status"], "success")
        self.assertGreaterEqual(res["stored_count"], len(chunks))
        
        # Test query
        col = res["collection"]
        q_res = col.query(query_texts=["multi-hop relational synthesis"], n_results=2)
        self.assertGreater(len(q_res["documents"][0]), 0)

    def test_04_graph_builder_citations_and_merging(self):
        """Verify Knowledge Graph extraction, mandatory edge citations, and cross-paper node merging."""
        gb = GraphBuilder()
        for p in self.papers:
            chunks = parse_pdf(p, p)
            gb.ingest_paper(chunks, p)
            
        stats = gb.get_stats()
        self.assertGreater(stats["total_nodes"], 10)
        self.assertGreater(stats["total_edges"], 15)
        
        # Verify mandatory edge citation attributes
        for u, v, d in gb.graph.edges(data=True):
            self.assertIn("source_paper", d)
            self.assertIn("page_num", d)
            self.assertIn("citation", d)
            self.assertTrue(d["citation"].startswith("["))
            self.assertTrue(d["citation"].endswith("]"))
            
        # Verify cross-paper node merging (HotpotQA should be connected to multiple papers)
        norm_ds = normalize_entity_name("HotpotQA")
        self.assertTrue(gb.graph.has_node(norm_ds))
        deg = gb.graph.degree(norm_ds)
        self.assertGreaterEqual(deg, 2)
        
        # Verify JSON save and load
        json_path = os.path.join(self.test_dir, "kg.json")
        gb.save_to_json(json_path)
        self.assertTrue(os.path.exists(json_path))
        
        gb2 = GraphBuilder()
        gb2.load_from_json(json_path)
        self.assertEqual(gb2.graph.number_of_nodes(), gb.graph.number_of_nodes())
        self.assertEqual(gb2.graph.number_of_edges(), gb.graph.number_of_edges())

    def test_05_hybrid_retriever(self):
        """Verify 1-2 hop subgraph expansion and hybrid prompt context packaging."""
        gb = GraphBuilder()
        all_chunks = []
        for p in self.papers:
            chunks = parse_pdf(p, p)
            all_chunks.extend(chunks)
            gb.ingest_paper(chunks, p)
            
        chroma_dir = os.path.join(self.test_dir, "chroma_ret")
        chroma_res = store_chunks_in_chromadb(all_chunks, collection_name="hybrid_col", persist_directory=chroma_dir)
        
        retriever = HybridRetriever(gb.graph, chroma_res["collection"])
        res = retriever.retrieve("What datasets are used by DenseRetriever and GraphRAG?")
        
        self.assertIn("DenseRetriever", res["entities"])
        self.assertGreater(len(res["triples"]), 0)
        self.assertGreater(len(res["chunks"]), 0)
        self.assertIn("KNOWLEDGE GRAPH RELATIONSHIPS", res["hybrid_prompt_context"])
        self.assertIn("RAW TEXT EVIDENCE CHUNKS", res["hybrid_prompt_context"])

    def test_06_synthesizer_matrix_and_quiz(self):
        """Verify comparison matrix, contradictions, Plotly data, and active-recall quizzes."""
        gb = GraphBuilder()
        for p in self.papers:
            chunks = parse_pdf(p, p)
            gb.ingest_paper(chunks, p)
            
        synth = Synthesizer()
        matrix = synth.generate_comparison_matrix(gb.graph)
        self.assertEqual(len(matrix["matrix_rows"]), 3)
        self.assertGreater(len(matrix["outperforms"]), 0)
        
        quiz = synth.generate_quiz(gb.graph, [])
        self.assertGreater(len(quiz["questions"]), 0)
        self.assertGreater(len(quiz["flashcards"]), 0)
        
        # Verify quiz question structure & citations
        q0 = quiz["questions"][0]
        self.assertIn("question", q0)
        self.assertIn("options", q0)
        self.assertIn("correct_index", q0)
        self.assertIn("explanation", q0)
        self.assertIn("citation", q0)

    def test_07_pyvis_visualization_rendering(self):
        """Verify interactive PyVis HTML generation with styled nodes and edges."""
        gb = GraphBuilder()
        gb.add_node_safe("GraphRAG", "Model/Method", "Knowledge graph RAG", "PaperA")
        gb.add_node_safe("HotpotQA", "Dataset", "Multi-hop QA", "PaperA")
        gb.add_edge_safe("GraphRAG", "HotpotQA", "USES_DATASET", "Benchmark", "PaperA", 2)
        
        html = render_knowledge_graph_html(gb.graph)
        self.assertIn("<html>", html)
        self.assertIn("GraphRAG", html)
        self.assertIn("HotpotQA", html)
        self.assertIn("#00A896", html)  # Teal color present


if __name__ == "__main__":
    unittest.main()
