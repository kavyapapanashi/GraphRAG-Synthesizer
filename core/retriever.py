"""
Hybrid GraphRAG Retriever Module
Extracts query entities, fetches 1-2 hop subgraphs from NetworkX with exact citations,
retrieves top-k raw chunks from ChromaDB, and prepares a unified hybrid context.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple, Set
import networkx as nx

# Antivirus proxy fix for Windows ssl module
if "SSLKEYLOGFILE" in os.environ and ("aswMonFltProxy" in os.environ["SSLKEYLOGFILE"] or not os.path.exists(os.environ["SSLKEYLOGFILE"])):
    os.environ.pop("SSLKEYLOGFILE", None)

from core.graph_builder import normalize_entity_name


class HybridRetriever:
    """
    Hybrid retriever combining structured Knowledge Graph traversals (1-2 hop neighborhood)
    with dense vector semantic chunk retrieval from ChromaDB.
    """
    def __init__(
        self,
        graph: nx.DiGraph,
        chroma_collection: Optional[Any] = None,
        api_key: Optional[str] = None
    ):
        self.graph = graph
        self.collection = chroma_collection
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._gemini_client = None
        
        if self.api_key and not self.api_key.startswith("your_") and not self.api_key.endswith("...") and len(self.api_key) > 20:
            try:
                from google import genai
                self._gemini_client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[HybridRetriever] Gemini client note: {e}")

    def extract_query_entities(self, query: str) -> List[str]:
        """
        Extracts key academic entities present in the user's query
        matching nodes in the Knowledge Graph.
        """
        matched_entities: Set[str] = set()
        clean_query = query.lower()
        
        # 1. Exact and substring matching against graph nodes
        for node in self.graph.nodes():
            node_str = str(node).lower()
            # Match word boundary or multi-word substring
            if len(node_str) >= 3 and re.search(rf"\b{re.escape(node_str)}\b", clean_query):
                matched_entities.add(str(node))
            elif node_str in clean_query and len(node_str) >= 4:
                matched_entities.add(str(node))

        # 2. Key phrases and capitalized acronyms (e.g. RAG, BM25, MRR)
        acronyms = re.findall(r"\b[A-Z0-9\-\@]{2,}\b", query)
        for acr in acronyms:
            norm_acr = normalize_entity_name(acr)
            if self.graph.has_node(norm_acr):
                matched_entities.add(norm_acr)
                
        # 3. If no entities matched and we have Gemini client, ask for semantic entity alignment
        if not matched_entities and self._gemini_client and self.graph.number_of_nodes() > 0:
            try:
                all_nodes = list(self.graph.nodes())[:100]
                prompt = f"""Given the user question: "{query}"
And this list of known entities: {all_nodes}
Return a comma-separated list of the 1 to 4 entities from the list most relevant to the question.
If none are relevant, reply "NONE"."""
                resp = self._gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
                text = resp.text.strip()
                if "NONE" not in text:
                    for item in text.split(","):
                        item_clean = item.strip().strip("'\"")
                        if self.graph.has_node(item_clean):
                            matched_entities.add(item_clean)
            except Exception:
                pass
                
        # 4. Fallback: If still empty, pick top connected hub nodes or nodes matching query keywords
        if not matched_entities and self.graph.number_of_nodes() > 0:
            query_words = set(re.findall(r"\w+", clean_query)) - {"what", "how", "why", "which", "is", "the", "in", "and", "or", "of", "to", "for", "with", "does", "can"}
            for node in self.graph.nodes():
                node_words = set(re.findall(r"\w+", str(node).lower()))
                if query_words & node_words:
                    matched_entities.add(str(node))
                    if len(matched_entities) >= 5:
                        break

        return sorted(list(matched_entities))

    def retrieve_subgraph(
        self,
        entities: List[str],
        max_hops: int = 2
    ) -> Tuple[nx.DiGraph, List[Dict[str, Any]], str]:
        """
        Retrieves the 1-hop and 2-hop neighborhood around matched entities from NetworkX.
        Returns:
        - subgraph: nx.DiGraph induced on retrieved nodes
        - triples: structured list of fact dicts with citations
        - formatted_text: human-readable text for LLM injection
        """
        if not entities or self.graph.number_of_nodes() == 0:
            return nx.DiGraph(), [], "No matching graph entities found."
            
        nodes_to_include: Set[str] = set()
        
        # 1-Hop Expansion
        for ent in entities:
            if self.graph.has_node(ent):
                nodes_to_include.add(ent)
                # Successors and Predecessors
                nodes_to_include.update(self.graph.successors(ent))
                nodes_to_include.update(self.graph.predecessors(ent))
                
        # 2-Hop Expansion if requested
        if max_hops >= 2:
            first_hop_nodes = list(nodes_to_include)
            for n in first_hop_nodes:
                if self.graph.has_node(n):
                    nodes_to_include.update(self.graph.successors(n))
                    nodes_to_include.update(self.graph.predecessors(n))
                    
        # Induced subgraph
        subgraph = self.graph.subgraph(nodes_to_include).copy()
        
        triples: List[Dict[str, Any]] = []
        formatted_lines: List[str] = []
        
        for u, v, data in subgraph.edges(data=True):
            u_type = subgraph.nodes[u].get("type", "Entity")
            v_type = subgraph.nodes[v].get("type", "Entity")
            relation = data.get("relation", "RELATES_TO")
            details = data.get("details", "").strip()
            citation = data.get("citation", "")
            if not citation:
                paper = data.get("source_paper", "Unknown Paper")
                page = data.get("page_num", 1)
                citation = f"[{paper}, p. {page}]"
                
            details_str = f" ({details})" if details else ""
            line = f"• [{u_type}: {u}] --{relation}--> [{v_type}: {v}]{details_str} {citation}"
            formatted_lines.append(line)
            
            triples.append({
                "source": u,
                "source_type": u_type,
                "target": v,
                "target_type": v_type,
                "relation": relation,
                "details": details,
                "citation": citation,
                "formatted": line
            })
            
        formatted_text = "\n".join(formatted_lines) if formatted_lines else "No direct graph relationship paths found for matched entities."
        return subgraph, triples, formatted_text

    def retrieve_chunks(
        self,
        query: str,
        top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], str]:
        """
        Retrieves top-k raw chunks from ChromaDB with metadata and exact citations.
        """
        if self.collection is None or self.collection.count() == 0:
            return [], "No vector database chunks available."
            
        results = self.collection.query(
            query_texts=[query],
            n_results=min(top_k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        
        chunks: List[Dict[str, Any]] = []
        formatted_lines: List[str] = []
        
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0] if "distances" in results else [0.0] * len(docs)
        
        for idx, (doc, meta, dist) in enumerate(zip(docs, metas, dists), 1):
            paper_name = meta.get("paper_name", "Unknown Paper")
            page_num = meta.get("page_num", 1)
            chunk_id = meta.get("chunk_id", f"chunk_{idx}")
            citation = f"[{paper_name}, p. {page_num}]"
            
            chunk_obj = {
                "chunk_id": chunk_id,
                "paper_name": paper_name,
                "page_num": page_num,
                "text": doc,
                "distance": float(dist),
                "citation": citation
            }
            chunks.append(chunk_obj)
            
            formatted_lines.append(
                f"[Chunk {idx}] Source: {citation} (ID: {chunk_id})\n\"{doc}\"\n"
            )
            
        formatted_text = "\n".join(formatted_lines) if formatted_lines else "No text chunks retrieved."
        return chunks, formatted_text

    def retrieve(
        self,
        query: str,
        top_k_chunks: int = 5,
        max_hops: int = 2
    ) -> Dict[str, Any]:
        """
        Executes unified Hybrid GraphRAG retrieval:
        1. Identifies entities in query
        2. Traverses 1-2 hop neighborhood in NetworkX
        3. Fetches top-k raw text chunks from ChromaDB
        4. Packages hybrid context for synthesis
        """
        entities = self.extract_query_entities(query)
        subgraph, triples, graph_context_str = self.retrieve_subgraph(entities, max_hops=max_hops)
        chunks, text_context_str = self.retrieve_chunks(query, top_k=top_k_chunks)
        
        hybrid_prompt_context = f"""=== KNOWLEDGE GRAPH RELATIONSHIPS (1-2 HOP TRACEABLE FACTS) ===
{graph_context_str}

=== RAW TEXT EVIDENCE CHUNKS (EXACT PASSAGES) ===
{text_context_str}
"""
        return {
            "query": query,
            "entities": entities,
            "subgraph": subgraph,
            "triples": triples,
            "graph_context": graph_context_str,
            "chunks": chunks,
            "text_context": text_context_str,
            "hybrid_prompt_context": hybrid_prompt_context
        }
