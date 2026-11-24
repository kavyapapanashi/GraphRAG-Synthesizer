"""
Sample Academic PDF Generator
Generates 3 realistic research PDFs with multi-page academic layouts, citations,
benchmark metrics, and limitations for instant testing and evaluation of GraphRAG.
"""

import os
import pymupdf

SAMPLE_PAPERS_DIR = "./data/sample_papers"


def create_page_with_text(doc: pymupdf.Document, title: str, sections: list):
    """Utility to format and insert an academic page with header, columns, and footer."""
    page = doc.new_page(width=595, height=842)  # Standard A4
    page_num = len(doc)
    
    # Header
    page.insert_text((50, 45), title.upper(), fontsize=8, color=(0.4, 0.4, 0.4))
    page.draw_line((50, 52), (545, 52), color=(0.7, 0.7, 0.7), width=0.5)
    
    y = 75
    for heading, text_body in sections:
        if heading:
            page.insert_text((50, y), heading, fontsize=12, color=(0.0, 0.2, 0.35))
            y += 18
            
        # Insert text block with wrapping
        rect = pymupdf.Rect(50, y, 545, min(y + 260, 780))
        page.insert_textbox(rect, text_body, fontsize=9.5, lineheight=1.3, color=(0.15, 0.15, 0.15))
        y += min(len(text_body) // 2.5 + 45, 270)
        if y >= 750:
            break
            
    # Page Footer
    page.draw_line((50, 795), (545, 795), color=(0.8, 0.8, 0.8), width=0.5)
    page.insert_text((280, 812), f"- {page_num} -", fontsize=9, color=(0.4, 0.4, 0.4))


def generate_sample_papers():
    """Generates 3 benchmark research PDFs in ./data/sample_papers/."""
    os.makedirs(SAMPLE_PAPERS_DIR, exist_ok=True)
    
    # 1. GraphRAG Paper
    path1 = os.path.join(SAMPLE_PAPERS_DIR, "GraphRAG_Reasoning.pdf")
    if not os.path.exists(path1):
        doc1 = pymupdf.open()
        # Page 1
        create_page_with_text(doc1, "GraphRAG: Knowledge-Augmented Generation", [
            ("GraphRAG: Knowledge-Augmented Generation for Complex Reasoning",
             "Abstract—Classical Retrieval-Augmented Generation (RAG) relies on flat vector similarity searches over isolated chunks, frequently failing when questions require multi-hop relational synthesis. In this paper, we propose GraphRAG, a neuro-symbolic framework that builds a dynamic Knowledge Graph from ingested documents. GraphRAG links entities into a structured relational network, allowing queries to traverse multi-hop paths across disparate papers."),
            ("1. Introduction",
             "As large language models encounter multi-document scientific corpora, standard dense retrievers struggle to reconstruct fragmented arguments. GraphRAG extracts canonical academic entities (Model/Method, Dataset, Metric, Limitation) and models their relational dependencies. By combining 1-hop and 2-hop graph neighborhood traversals with dense vector embeddings, GraphRAG achieves unprecedented groundedness.")
        ])
        # Page 2
        create_page_with_text(doc1, "GraphRAG: Knowledge-Augmented Generation", [
            ("2. Relational Knowledge Graph Pipeline",
             "Our pipeline parses text page-by-page preserving strict citation metadata. The extraction module identifies entities and relations including USES_DATASET, ACHIEVES_METRIC, and HAS_LIMITATION. To evaluate cross-document multi-hop reasoning, we benchmark GraphRAG on the HotpotQA dataset and the MultiHop-RAG corpus."),
            ("3. Experimental Setup",
             "All experiments evaluate end-to-end question answering and retrieval precision against competitive baselines including BM25 and DenseRetriever. We record Recall@10, Mean Reciprocal Rank (MRR@10), and exact match F1-Score across 5,000 multi-hop queries.")
        ])
        # Page 3
        create_page_with_text(doc1, "GraphRAG: Knowledge-Augmented Generation", [
            ("4. Benchmark Results and Comparisons",
             "Empirical evaluation demonstrates that GraphRAG significantly outperforms traditional methods. On the HotpotQA benchmark, GraphRAG achieves a Recall@10 of 86.4%, an MRR@10 of 0.78, and an F1-Score of 81.2%. In direct head-to-head evaluation, GraphRAG outperforms DenseRetriever by 12.3% on multi-hop questions where relational bridges are required."),
            ("5. Qualitative Analysis",
             "Unlike pure vector search which retrieves surface-level lexical matches, GraphRAG traces explicit fact chains from papers, providing traceable citations for every assertion made by the generative LLM.")
        ])
        # Page 4
        create_page_with_text(doc1, "GraphRAG: Knowledge-Augmented Generation", [
            ("6. Computational Limitations and Bottlenecks",
             "Despite its superior reasoning capacity, GraphRAG exhibits notable limitations. First, Index Build Time is a major bottleneck: offline entity extraction and graph synthesis require substantial LLM inference overhead during preprocessing. Second, GraphRAG has a significant Memory Overhead, requiring approximately 24GB of RAM to maintain the in-memory graph index for large corpora."),
            ("7. Conclusion",
             "GraphRAG demonstrates that structured knowledge graph synthesis is essential for multi-hop scientific reasoning, opening promising directions for hybrid vector-graph retrieval.")
        ])
        doc1.save(path1)
        doc1.close()

    # 2. DenseRetriever Paper
    path2 = os.path.join(SAMPLE_PAPERS_DIR, "DenseRetriever_Scale.pdf")
    if not os.path.exists(path2):
        doc2 = pymupdf.open()
        # Page 1
        create_page_with_text(doc2, "DenseRetriever: Dual-Encoder Retrieval", [
            ("DenseRetriever: Dual-Encoder Passage Retrieval at Scale",
             "Abstract—Dense neural retrieval has become the foundational paradigm for modern open-domain question answering. In this work, we present DenseRetriever, an optimized bi-encoder architecture that maps questions and passage chunks into a continuous 768-dimensional latent vector space."),
            ("1. Dual-Encoder Architecture",
             "DenseRetriever employs twin transformer encoders trained with contrastive negative mining. At inference time, approximate nearest neighbor search via HNSW enables sub-30ms query processing over millions of documents.")
        ])
        # Page 2
        create_page_with_text(doc2, "DenseRetriever: Dual-Encoder Retrieval", [
            ("2. Empirical Benchmarking",
             "We conduct extensive evaluations on two primary benchmarks: MS-MARCO and HotpotQA. On the MS-MARCO passage ranking task, DenseRetriever achieves a Recall@10 of 74.1% and an MRR@10 of 0.69. Furthermore, DenseRetriever achieves an ultra-low Latency of 28ms per query, demonstrating remarkable efficiency. In empirical comparisons, DenseRetriever outperforms BM25 on semantic paraphrasing tasks."),
            ("3. Single-Passage Matching",
             "For single-fact retrieval queries where answer spans reside entirely within a single paragraph, DenseRetriever retrieves the gold target passage with 91.5% accuracy.")
        ])
        # Page 3
        create_page_with_text(doc2, "DenseRetriever: Dual-Encoder Retrieval", [
            ("4. Limitations and Vulnerabilities",
             "We identify two critical limitations in DenseRetriever. First, Hallucination Risk: when faced with complex multi-hop questions, DenseRetriever fails to link interdependent reasoning steps, leading downstream generation models to hallucinate answers. Second, DenseRetriever suffers from a strict Context Window Limit of 512 tokens per chunk, causing cross-boundary information loss."),
            ("5. Future Directions",
             "Future work will investigate hybrid indexing structures to address multi-step reasoning bottlenecks.")
        ])
        doc2.save(path2)
        doc2.close()

    # 3. HybridSearch Paper
    path3 = os.path.join(SAMPLE_PAPERS_DIR, "HybridSearch_Fusion.pdf")
    if not os.path.exists(path3):
        doc3 = pymupdf.open()
        # Page 1
        create_page_with_text(doc3, "HybridSearch: Lexical and Neural Fusion", [
            ("HybridSearch: Fusing Sparse BM25 and Dense Neural Embeddings",
             "Abstract—While dense neural retrieval has dominated recent literature, pure dense encoders suffer catastrophic failure modes when matching exact alphanumeric identifiers, scientific acronyms, and rare terms. We introduce HybridSearch, an efficient hybrid search framework that dynamically fuses sparse BM25 scores with dense neural representations using reciprocal rank fusion."),
            ("1. Motivation and Method",
             "HybridSearch computes an optimal linear combination of sparse inverted-index scores and dense vector cosine similarities. This allows the system to preserve exact lexical precision while retaining deep semantic matching.")
        ])
        # Page 2
        create_page_with_text(doc3, "HybridSearch: Lexical and Neural Fusion", [
            ("2. Evaluation on Open-Domain Benchmarks",
             "We evaluate HybridSearch across MS-MARCO and NaturalQuestions. On MS-MARCO, HybridSearch achieves a Recall@10 of 79.8% and an MRR@10 of 0.73 with a fast Latency of 42ms. HybridSearch consistently outperforms standalone BM25 and standalone dense retrievers across diverse query distributions.")
        ])
        # Page 3
        create_page_with_text(doc3, "HybridSearch: Lexical and Neural Fusion", [
            ("3. Empirical Contradiction of Dense-Only Claims",
             "Crucially, our experiments CONTRADICTS DenseRetriever: whereas previous work claimed dense embeddings render lexical matching obsolete, our ablation study proves that pure dense retrieval accuracy drops by 34.6% on rare entity and serial number lookups. Lexical sparse matching remains essential."),
            ("4. Limitations",
             "A stated bottleneck of HybridSearch is Tuning Complexity: the reciprocal rank fusion weights (alpha, beta) require extensive hyperparameter tuning across domain shifts, creating operational deployment friction.")
        ])
        doc3.save(path3)
        doc3.close()

    return [path1, path2, path3]


if __name__ == "__main__":
    generated = generate_sample_papers()
    print("Sample papers generated:", generated)
