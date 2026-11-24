"""
FastAPI Backend Integration Test Suite
Validates all endpoints for root, stats, sample loading, graph retrieval,
hybrid Q&A, comparison matrix, active-recall quiz, and session reset.
"""

import os
import unittest

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

from api.main import (
    root,
    api_status,
    get_stats,
    load_sample_papers,
    get_graph,
    chat_hybrid_rag,
    get_comparison_matrix,
    get_study_quiz,
    reset_session,
    ChatRequest,
    state
)


class TestFastAPIBackend(unittest.TestCase):
    def setUp(self):
        state.reset()

    def test_01_root_and_stats(self):
        """Test initial root and stats functions."""
        r = api_status()
        self.assertEqual(r["status"], "online")
        self.assertEqual(r["papers_ingested"], 0)

        # root() returns FileResponse when frontend is built
        html_res = root()
        self.assertTrue(hasattr(html_res, "path") or isinstance(html_res, dict))

        s = get_stats()
        self.assertEqual(s["papers"], [])
        self.assertEqual(s["nodes_count"], 0)

    def test_02_load_sample_papers(self):
        """Test loading benchmark sample papers."""
        res = load_sample_papers()
        self.assertEqual(len(res.papers), 3)
        self.assertGreater(res.chunks_count, 10)
        self.assertGreater(res.nodes_count, 10)
        self.assertGreater(res.edges_count, 15)
        self.assertIn("nodes", res.graph)
        self.assertIn("edges", res.graph)

    def test_03_get_graph(self):
        """Test retrieving the knowledge graph."""
        load_sample_papers()
        graph_res = get_graph()
        self.assertGreater(len(graph_res.nodes), 10)
        self.assertGreater(len(graph_res.edges), 15)
        
        # Verify node fields
        node0 = graph_res.nodes[0]
        self.assertIn("id", node0)
        self.assertIn("type", node0)

        # Verify edge fields
        edge0 = graph_res.edges[0]
        self.assertIn("source", edge0)
        self.assertIn("target", edge0)
        self.assertIn("citation", edge0)

    def test_04_chat_hybrid_retrieval(self):
        """Test hybrid GraphRAG Q&A."""
        load_sample_papers()
        req = ChatRequest(query="What are the computational limitations of GraphRAG?", top_k=3, max_hops=2)
        chat_res = chat_hybrid_rag(req)
        self.assertGreater(len(chat_res.answer), 30)
        self.assertIn("triples", chat_res.__dict__)
        self.assertIn("chunks", chat_res.__dict__)

    def test_05_matrix_and_quiz(self):
        """Test comparative matrix and active-recall quiz."""
        load_sample_papers()
        mat = get_comparison_matrix()
        self.assertEqual(len(mat["matrix_rows"]), 3)
        self.assertGreater(len(mat["outperforms"]), 0)

        quiz = get_study_quiz()
        self.assertIn("questions", quiz)
        self.assertIn("flashcards", quiz)
        self.assertGreater(len(quiz["questions"]), 0)

    def test_06_reset(self):
        """Test resetting pipeline session."""
        load_sample_papers()
        reset_res = reset_session()
        self.assertEqual(reset_res["status"], "success")
        s = get_stats()
        self.assertEqual(s["papers"], [])
        self.assertEqual(s["nodes_count"], 0)


if __name__ == "__main__":
    unittest.main()
