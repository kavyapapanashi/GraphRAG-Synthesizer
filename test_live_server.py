import urllib.request
import json

base = "http://127.0.0.1:8000"

print("\n--- TESTING LIVE SERVER (http://127.0.0.1:8000) ---")

# 1. Root HTML
with urllib.request.urlopen(f"{base}/") as r:
    html = r.read().decode("utf-8")
    assert r.status == 200
    assert "html" in html.lower()
    print("1. [PASS] Root / serves React frontend dist index.html")

# 2. Stats
with urllib.request.urlopen(f"{base}/api/stats") as r:
    s = json.loads(r.read().decode("utf-8"))
    assert len(s["papers"]) == 3
    print(f"2. [PASS] Ingested Papers: {s['papers']}")

# 3. Knowledge Graph
with urllib.request.urlopen(f"{base}/api/graph") as r:
    g = json.loads(r.read().decode("utf-8"))
    assert len(g["nodes"]) == 18
    assert len(g["edges"]) == 37
    print(f"3. [PASS] Knowledge Graph: {len(g['nodes'])} nodes, {len(g['edges'])} edges")

# 4. Comparison Matrix
with urllib.request.urlopen(f"{base}/api/matrix") as r:
    m = json.loads(r.read().decode("utf-8"))
    assert len(m["matrix_rows"]) == 3
    print(f"4. [PASS] Comparison Matrix: {len(m['matrix_rows'])} paper rows, {len(m['outperforms'])} outperformance pairs")

# 5. Study Quiz
req = urllib.request.Request(f"{base}/api/quiz", data=b"", method="POST")
with urllib.request.urlopen(req) as r:
    q = json.loads(r.read().decode("utf-8"))
    assert len(q["questions"]) >= 3
    assert len(q["flashcards"]) >= 3
    print(f"5. [PASS] Study Quiz Hub: {len(q['questions'])} active-recall MCQs, {len(q['flashcards'])} flashcards")

# 6. Chat Hybrid GraphRAG
payload = json.dumps({"query": "Compare methodologies across uploaded papers"}).encode("utf-8")
req = urllib.request.Request(
    f"{base}/api/chat",
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req) as r:
    c = json.loads(r.read().decode("utf-8"))
    assert len(c["citations"]) > 0
    assert len(c["answer"]) > 50
    print(f"6. [PASS] Chat Hybrid GraphRAG: {len(c['citations'])} citations ({', '.join(c['citations'])}), answer length: {len(c['answer'])} chars")

print("\n=======================================================")
print("  ALL MODULES (CHAT, KG, MATRIX, QUIZ) FULLY WORKING!  ")
print("=======================================================\n")
