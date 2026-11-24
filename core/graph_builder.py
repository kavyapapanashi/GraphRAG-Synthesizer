"""
Knowledge Graph Extraction Module for GraphRAG
Uses Gemini Structured Outputs (Pydantic schema) to extract academic entities & relationships
into a NetworkX graph with mandatory citation tracking and cross-paper node merging.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional, Literal, Tuple
import networkx as nx
from pydantic import BaseModel, Field

# Prevent Windows SSLKEYLOGFILE antivirus permission error
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

# Strict Schemas for LLM Extraction
NodeType = Literal["Paper", "Model/Method", "Dataset", "Metric", "Limitation"]
EdgeType = Literal["USES_DATASET", "PROPOSES_METHOD", "ACHIEVES_METRIC", "HAS_LIMITATION", "OUTPERFORMS", "CONTRADICTS"]

VALID_NODE_TYPES = {"Paper", "Model/Method", "Dataset", "Metric", "Limitation"}
VALID_EDGE_TYPES = {"USES_DATASET", "PROPOSES_METHOD", "ACHIEVES_METRIC", "HAS_LIMITATION", "OUTPERFORMS", "CONTRADICTS"}


class ExtractedEntity(BaseModel):
    id: str = Field(description="Normalized canonical identifier for the entity, e.g. 'Transformer', 'HotpotQA', 'Recall@10', 'High Computational Cost'")
    type: NodeType = Field(description="Entity type: Paper, Model/Method, Dataset, Metric, or Limitation")
    description: Optional[str] = Field(default="", description="Concise definition or context of this entity")


class ExtractedRelation(BaseModel):
    source: str = Field(description="Source entity ID (must match an extracted entity id)")
    target: str = Field(description="Target entity ID (must match an extracted entity id)")
    relation: EdgeType = Field(description="Relation: USES_DATASET, PROPOSES_METHOD, ACHIEVES_METRIC, HAS_LIMITATION, OUTPERFORMS, CONTRADICTS")
    details: Optional[str] = Field(default="", description="Specific facts or quantitative scores (e.g. '82.4% Recall@10', 'Requires 32GB VRAM')")
    page_num: int = Field(description="Page number (1-indexed) where this fact is stated in the paper")


class PaperGraphExtraction(BaseModel):
    paper_title: str = Field(description="Standardized title of the paper")
    entities: List[ExtractedEntity] = Field(description="List of academic entities extracted from the paper")
    relations: List[ExtractedRelation] = Field(description="List of academic relations between entities with exact page citations")


def normalize_entity_name(name: str) -> str:
    """Normalize entity names across papers to enable seamless cross-paper node merging."""
    clean = name.strip()
    # Normalize common acronyms and casing
    acronym_map = {
        "hotpotqa": "HotpotQA",
        "hotpot qa": "HotpotQA",
        "ms marco": "MS-MARCO",
        "msmarco": "MS-MARCO",
        "ms-marco": "MS-MARCO",
        "squad": "SQuAD",
        "squad v2": "SQuAD 2.0",
        "squad 2.0": "SQuAD 2.0",
        "glue": "GLUE",
        "superglue": "SuperGLUE",
        "bleu": "BLEU",
        "bleu-4": "BLEU-4",
        "rouge": "ROUGE",
        "rouge-l": "ROUGE-L",
        "mrr": "MRR",
        "mrr@10": "MRR@10",
        "recall@10": "Recall@10",
        "recall@20": "Recall@20",
        "f1": "F1-Score",
        "f1 score": "F1-Score",
        "accuracy": "Accuracy",
        "graphrag": "GraphRAG",
        "bm25": "BM25",
        "denseretriever": "DenseRetriever",
        "colbert": "ColBERT",
        "transformer": "Transformer",
        "bert": "BERT",
        "roberta": "RoBERTa",
        "gpt-4": "GPT-4",
    }
    lower = clean.lower()
    if lower in acronym_map:
        return acronym_map[lower]
    
    # Capitalize first letter of words if all lower
    if clean.islower() and len(clean) > 3:
        return clean.title()
    return clean


class GraphBuilder:
    """
    Constructs, merges, and manages an academic NetworkX DiGraph across papers.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.graph = nx.DiGraph()
        self._gemini_client = None
        
        if self.api_key and not self.api_key.startswith("your_") and not self.api_key.endswith("...") and len(self.api_key) > 20:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[GraphBuilder] Gemini Client notice: {e}")

    def add_node_safe(self, node_id: str, node_type: str, description: str = "", paper_name: str = ""):
        """Add or update an entity node, merging attributes across papers."""
        norm_id = normalize_entity_name(node_id)
        if not norm_id:
            return
            
        validated_type = node_type if node_type in VALID_NODE_TYPES else "Model/Method"
        
        if self.graph.has_node(norm_id):
            curr_data = self.graph.nodes[norm_id]
            papers = set(curr_data.get("papers", []))
            if paper_name:
                papers.add(paper_name)
            curr_data["papers"] = list(papers)
            if description and not curr_data.get("description"):
                curr_data["description"] = description
        else:
            self.graph.add_node(
                norm_id,
                type=validated_type,
                description=description,
                papers=[paper_name] if paper_name else []
            )

    def add_edge_safe(
        self,
        source: str,
        target: str,
        relation: str,
        details: str = "",
        source_paper: str = "",
        page_num: int = 1
    ):
        """
        Add a directed edge with mandatory citation tracking attributes:
        source_paper, page_num, and human-readable citation string.
        """
        norm_source = normalize_entity_name(source)
        norm_target = normalize_entity_name(target)
        
        if not norm_source or not norm_target or norm_source == norm_target:
            return
            
        validated_relation = relation if relation in VALID_EDGE_TYPES else "USES_DATASET"
        
        # Ensure nodes exist
        if not self.graph.has_node(norm_source):
            self.add_node_safe(norm_source, "Model/Method", paper_name=source_paper)
        if not self.graph.has_node(norm_target):
            self.add_node_safe(norm_target, "Dataset" if "DATASET" in validated_relation else "Metric", paper_name=source_paper)
            
        citation_str = f"[{source_paper}, p. {page_num}]"
        
        # In a directed graph, if the edge exists, we can store list of citations or details
        if self.graph.has_edge(norm_source, norm_target):
            edge_data = self.graph[norm_source][norm_target]
            # Accumulate citations
            citations = edge_data.get("citations", [])
            if citation_str not in citations:
                citations.append(citation_str)
            edge_data["citations"] = citations
            if details and details not in edge_data.get("details", ""):
                edge_data["details"] = f"{edge_data.get('details', '')} | {details}".strip(" | ")
        else:
            self.graph.add_edge(
                norm_source,
                norm_target,
                relation=validated_relation,
                details=details,
                source_paper=source_paper,
                page_num=page_num,
                citation=citation_str,
                citations=[citation_str]
            )

    def extract_with_gemini(self, chunks: List[Dict[str, Any]], paper_name: str) -> PaperGraphExtraction:
        """
        Extract knowledge graph nodes & edges from paper chunks using Gemini Structured Outputs.
        """
        from google.genai import types
        
        # Synthesize representative sample of text chunks across pages
        # Include pages in order with page numbers
        text_by_page: Dict[int, List[str]] = {}
        for c in chunks:
            p = c.get("page_num", 1)
            text_by_page.setdefault(p, []).append(c.get("text", ""))
            
        formatted_context_list = []
        for p in sorted(text_by_page.keys()):
            p_text = " ".join(text_by_page[p])
            # Keep up to 1500 chars per page to fit context gracefully
            formatted_context_list.append(f"--- PAGE {p} ---\n{p_text[:2000]}")
            
        full_paper_text = "\n\n".join(formatted_context_list)
        
        prompt = f"""
You are an expert academic research synthesizer extracting a rigorous Knowledge Graph from an academic paper.

PAPER NAME: {paper_name}

INSTRUCTIONS:
Extract academic entities and relationships following these strict constraints:
1. Node Types MUST be one of:
   - "Paper": The paper itself
   - "Model/Method": Architectures, algorithms, prompting strategies (e.g., 'Transformer', 'DenseRetriever', 'GraphRAG')
   - "Dataset": Evaluation benchmarks and corpora (e.g., 'HotpotQA', 'MS-MARCO', 'SQuAD')
   - "Metric": Quantitative evaluations (e.g., 'Recall@10', 'Accuracy', 'Latency', 'F1-Score')
   - "Limitation": Bottlenecks, failure modes, trade-offs (e.g., 'High Memory Footprint', 'Slow Indexing', 'Hallucination on Multi-Hop')

2. Edge Types MUST be one of:
   - "PROPOSES_METHOD": Paper proposes or introduces a Model/Method
   - "USES_DATASET": Model/Method or Paper evaluates on a Dataset
   - "ACHIEVES_METRIC": Model/Method achieves a Metric on a Dataset (include quantitative score in details)
   - "HAS_LIMITATION": Model/Method or Paper exhibits a Limitation
   - "OUTPERFORMS": Model A outperforms Model B on a benchmark
   - "CONTRADICTS": Paper or Method contradicts an earlier finding or baseline

3. CITATION ACCURACY:
   - Every relation MUST record the exact page number (1-indexed) where the claim is made in the text.
   - Do NOT invent facts.

PAPER CONTENT:
{full_paper_text}
"""
        response = self._gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PaperGraphExtraction,
                temperature=0.1
            )
        )
        
        raw_json = response.text
        parsed = json.loads(raw_json)
        return PaperGraphExtraction(**parsed)

    def extract_heuristics(self, chunks: List[Dict[str, Any]], paper_name: str) -> PaperGraphExtraction:
        """
        High-accuracy rule-based academic knowledge graph extraction fallback
        when Gemini API key is not present or offline.
        """
        entities: List[ExtractedEntity] = []
        relations: List[ExtractedRelation] = []
        seen_entities = set()
        
        paper_node_id = paper_name.replace(".pdf", "").strip()
        entities.append(ExtractedEntity(id=paper_node_id, type="Paper", description=f"Academic paper: {paper_name}"))
        seen_entities.add(paper_node_id)
        
        # Academic Entity Matcher Patterns
        known_methods = [
            ("GraphRAG", "Knowledge Graph augmented retrieval-generation architecture"),
            ("DenseRetriever", "Dual-encoder dense passage retrieval model"),
            ("HybridSearch", "Fusion of sparse BM25 and dense embedding retrieval"),
            ("ColBERT", "Late-interaction token-level retrieval model"),
            ("BM25", "Classical probabilistic lexical matching algorithm"),
            ("Transformer", "Self-attention based neural sequence architecture"),
            ("BERT", "Bidirectional Encoder Representations from Transformers"),
            ("Cross-Encoder", "Full attention query-document re-ranking model")
        ]
        
        known_datasets = [
            ("HotpotQA", "Multi-hop question answering benchmark dataset"),
            ("MS-MARCO", "Large scale real-world search ranking dataset"),
            ("SQuAD", "Stanford Question Answering Dataset"),
            ("MultiHop-RAG", "Complex multi-hop reasoning corpus for RAG"),
            ("NaturalQuestions", "Google search query and Wikipedia answer dataset")
        ]
        
        known_metrics = [
            ("Recall@10", "Fraction of relevant documents retrieved in top 10"),
            ("MRR@10", "Mean Reciprocal Rank of first relevant document"),
            ("F1-Score", "Harmonic mean of precision and recall"),
            ("Latency", "Query processing and inference time per request"),
            ("Accuracy", "Overall exact answer accuracy percentage")
        ]
        
        known_limitations = [
            ("High Latency", "Substantial query latency caused by multi-hop graph traversals"),
            ("Index Build Time", "Time-consuming offline entity extraction and graph synthesis"),
            ("Memory Overhead", "High RAM and GPU VRAM footprint required for graph indices"),
            ("Hallucination Risk", "Tendency to produce ungrounded assertions when context is ambiguous")
        ]
        
        # Scan through chunks
        for chunk in chunks:
            text = chunk.get("text", "")
            page_num = chunk.get("page_num", 1)
            
            # Detect methods
            found_methods = []
            for m_name, m_desc in known_methods:
                if re.search(rf"\b{re.escape(m_name)}\b", text, re.IGNORECASE):
                    norm = normalize_entity_name(m_name)
                    found_methods.append(norm)
                    if norm not in seen_entities:
                        entities.append(ExtractedEntity(id=norm, type="Model/Method", description=m_desc))
                        seen_entities.add(norm)
                    # Relate to paper
                    relations.append(ExtractedRelation(
                        source=paper_node_id,
                        target=norm,
                        relation="PROPOSES_METHOD",
                        details=f"Discussed in {paper_name}",
                        page_num=page_num
                    ))
                    
            # Detect datasets
            found_datasets = []
            for d_name, d_desc in known_datasets:
                if re.search(rf"\b{re.escape(d_name)}\b", text, re.IGNORECASE):
                    norm = normalize_entity_name(d_name)
                    found_datasets.append(norm)
                    if norm not in seen_entities:
                        entities.append(ExtractedEntity(id=norm, type="Dataset", description=d_desc))
                        seen_entities.add(norm)
                    if found_methods:
                        for m in found_methods:
                            relations.append(ExtractedRelation(
                                source=m,
                                target=norm,
                                relation="USES_DATASET",
                                details=f"Evaluated on {norm}",
                                page_num=page_num
                            ))
                            
            # Detect metrics & quantitative scores
            for met_name, met_desc in known_metrics:
                if re.search(rf"\b{re.escape(met_name)}\b", text, re.IGNORECASE):
                    norm = normalize_entity_name(met_name)
                    if norm not in seen_entities:
                        entities.append(ExtractedEntity(id=norm, type="Metric", description=met_desc))
                        seen_entities.add(norm)
                    # Extract quantitative number if near
                    score_match = re.search(rf"{re.escape(met_name)}[:\s\-=]+(\d+(\.\d+)?%?)", text, re.IGNORECASE)
                    score_str = score_match.group(1) if score_match else "Quantitative evaluation reported"
                    target_method = found_methods[0] if found_methods else paper_node_id
                    relations.append(ExtractedRelation(
                        source=target_method,
                        target=norm,
                        relation="ACHIEVES_METRIC",
                        details=score_str,
                        page_num=page_num
                    ))
                    
            # Detect limitations
            for lim_name, lim_desc in known_limitations:
                if re.search(rf"\b{re.escape(lim_name)}\b", text, re.IGNORECASE) or any(w in text.lower() for w in ["limitation", "bottleneck", "drawback"]):
                    norm = normalize_entity_name(lim_name)
                    if norm not in seen_entities:
                        entities.append(ExtractedEntity(id=norm, type="Limitation", description=lim_desc))
                        seen_entities.add(norm)
                    target_method = found_methods[0] if found_methods else paper_node_id
                    relations.append(ExtractedRelation(
                        source=target_method,
                        target=norm,
                        relation="HAS_LIMITATION",
                        details=f"Identified bottleneck in {paper_name}",
                        page_num=page_num
                    ))
                    break

            # Detect outperforms or contradicts
            if re.search(r"\boutperforms\b|\bsuperior to\b|\bsurpasses\b", text, re.IGNORECASE) and len(found_methods) >= 2:
                relations.append(ExtractedRelation(
                    source=found_methods[0],
                    target=found_methods[1],
                    relation="OUTPERFORMS",
                    details=f"Reported outperformance on evaluation benchmark",
                    page_num=page_num
                ))
            elif re.search(r"\bcontradicts\b|\bcontrary to\b|\bdisproves\b", text, re.IGNORECASE) and len(found_methods) >= 2:
                relations.append(ExtractedRelation(
                    source=found_methods[0],
                    target=found_methods[1],
                    relation="CONTRADICTS",
                    details=f"Conflicting empirical result documented",
                    page_num=page_num
                ))
                
        # Deduplicate relations
        dedup_relations: List[ExtractedRelation] = []
        seen_rels = set()
        for r in relations:
            key = (r.source, r.target, r.relation, r.page_num)
            if key not in seen_rels:
                seen_rels.add(key)
                dedup_relations.append(r)
                
        return PaperGraphExtraction(
            paper_title=paper_node_id,
            entities=entities,
            relations=dedup_relations
        )

    def ingest_paper(self, chunks: List[Dict[str, Any]], paper_name: str) -> PaperGraphExtraction:
        """
        Extracts entities and relations from a paper and integrates them into the NetworkX graph.
        Merges nodes across papers with normalized IDs.
        """
        clean_paper_name = os.path.basename(paper_name).replace(".pdf", "")
        
        extraction: Optional[PaperGraphExtraction] = None
        if self._gemini_client:
            try:
                extraction = self.extract_with_gemini(chunks, clean_paper_name)
            except Exception as e:
                print(f"[GraphBuilder] Gemini extraction fallback for {paper_name}: {e}")
                extraction = self.extract_heuristics(chunks, clean_paper_name)
        else:
            extraction = self.extract_heuristics(chunks, clean_paper_name)
            
        # Ensure paper node is in graph
        self.add_node_safe(clean_paper_name, "Paper", f"Academic Paper: {clean_paper_name}", clean_paper_name)
        
        # Add extracted entities
        for entity in extraction.entities:
            self.add_node_safe(entity.id, entity.type, entity.description or "", clean_paper_name)
            
        # Add extracted relations
        for rel in extraction.relations:
            self.add_edge_safe(
                source=rel.source,
                target=rel.target,
                relation=rel.relation,
                details=rel.details or "",
                source_paper=clean_paper_name,
                page_num=rel.page_num
            )
            
        return extraction

    def get_stats(self) -> Dict[str, Any]:
        """Return comprehensive Knowledge Graph analytics."""
        node_types: Dict[str, int] = {}
        for _, data in self.graph.nodes(data=True):
            t = data.get("type", "Unknown")
            node_types[t] = node_types.get(t, 0) + 1
            
        edge_types: Dict[str, int] = {}
        for _, _, data in self.graph.edges(data=True):
            r = data.get("relation", "Unknown")
            edge_types[r] = edge_types.get(r, 0) + 1
            
        degrees = dict(self.graph.degree())
        top_hubs = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": node_types,
            "edge_types": edge_types,
            "density": round(nx.density(self.graph), 4) if self.graph.number_of_nodes() > 1 else 0.0,
            "top_hubs": top_hubs
        }

    def save_to_json(self, filepath: str = "./data/knowledge_graph.json"):
        """Save graph to JSON preserving all node & edge attributes and citations."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        nodes_data = []
        for n, d in self.graph.nodes(data=True):
            nodes_data.append({"id": n, **d})
            
        edges_data = []
        for u, v, d in self.graph.edges(data=True):
            edges_data.append({"source": u, "target": v, **d})
            
        data = {
            "nodes": nodes_data,
            "edges": edges_data
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filepath: str = "./data/knowledge_graph.json"):
        """Load graph from JSON."""
        if not os.path.exists(filepath):
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        self.graph.clear()
        for n in data.get("nodes", []):
            nid = n.pop("id")
            self.graph.add_node(nid, **n)
            
        for e in data.get("edges", []):
            u = e.pop("source")
            v = e.pop("target")
            self.graph.add_edge(u, v, **e)
