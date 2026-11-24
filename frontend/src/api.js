/**
 * GraphRAG Frontend API Client
 * Connects to the FastAPI backend at http://localhost:8000
 */

const API_BASE = (typeof window !== "undefined" && window.location.port === "5173") 
  ? "http://localhost:8000" 
  : "";

export async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error("Failed to fetch stats");
    return await res.json();
  } catch (err) {
    console.error("fetchStats error:", err);
    return { papers: [], total_pages: 0, chunks_count: 0, nodes_count: 0, edges_count: 0 };
  }
}

export async function ingestFiles(fileList) {
  const formData = new FormData();
  for (let i = 0; i < fileList.length; i++) {
    formData.append("files", fileList[i]);
  }
  const res = await fetch(`${API_BASE}/api/ingest`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({}));
    throw new Error(errData.detail || "Ingestion failed");
  }
  return await res.json();
}

export async function loadSamplePapers() {
  const res = await fetch(`${API_BASE}/api/sample`, {
    method: "POST",
  });
  if (!res.ok) {
    throw new Error("Failed to load benchmark sample papers");
  }
  return await res.json();
}

export async function fetchGraph() {
  const res = await fetch(`${API_BASE}/api/graph`);
  if (!res.ok) throw new Error("Failed to fetch graph data");
  return await res.json();
}

export async function sendChatQuery(query, top_k = 5, max_hops = 2) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k, max_hops }),
  });
  if (!res.ok) throw new Error("Chat query failed");
  return await res.json();
}

export async function fetchMatrix() {
  const res = await fetch(`${API_BASE}/api/matrix`);
  if (!res.ok) throw new Error("Failed to fetch matrix");
  return await res.json();
}

export async function fetchQuiz(paper = null, session_topics = []) {
  const res = await fetch(`${API_BASE}/api/quiz`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paper, session_topics }),
  });
  if (!res.ok) throw new Error("Failed to fetch quiz");
  return await res.json();
}

export async function resetSession() {
  const res = await fetch(`${API_BASE}/api/reset`, {
    method: "POST",
  });
  if (!res.ok) throw new Error("Failed to reset session");
  return await res.json();
}
