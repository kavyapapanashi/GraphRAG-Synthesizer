import os
import sys

# Antivirus fix
if "SSLKEYLOGFILE" in os.environ:
    os.environ.pop("SSLKEYLOGFILE", None)

from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# 1. Root HTML
r0 = client.get("/")
assert r0.status_code == 200, f"Root status {r0.status_code}"
assert "<!doctype html>" in r0.text.lower(), "Root didn't return HTML"
print("✓ Root / serves React frontend dist index.html")

# 2. Stats
r1 = client.get("/api/stats")
assert r1.status_code == 200
data1 = r1.json()
assert len(data1["papers"]) == 3, f"Expected 3 papers, got {len(data1['papers'])}"
assert data1["nodes_count"] >= 15, f"Expected >= 15 nodes, got {data1['nodes_count']}"
print(f"✓ Stats auto-populated: {len(data1['papers'])} papers, {data1['nodes_count']} nodes, {data1['edges_count']} edges")

# 3. Graph
r2 = client.get("/api/graph")
assert r2.status_code == 200
data2 = r2.json()
assert len(data2["nodes"]) >= 15
assert len(data2["edges"]) >= 30
print(f"✓ Graph endpoint verified: {len(data2['nodes'])} nodes, {len(data2['edges'])} edges")

# 4. Matrix
r3 = client.get("/api/matrix")
assert r3.status_code == 200
data3 = r3.json()
assert len(data3["matrix_rows"]) == 3, f"Expected 3 rows, got {len(data3['matrix_rows'])}"
print(f"✓ Matrix endpoint verified: {len(data3['matrix_rows'])} paper rows")

# 5. Quiz
r4 = client.post("/api/quiz")
assert r4.status_code == 200
data4 = r4.json()
assert len(data4["questions"]) >= 3, f"Expected >= 3 questions, got {len(data4['questions'])}"
assert len(data4["flashcards"]) >= 3, f"Expected >= 3 flashcards, got {len(data4['flashcards'])}"
print(f"✓ Quiz endpoint verified: {len(data4['questions'])} MCQs, {len(data4['flashcards'])} flashcards")

# 6. Chat
r5 = client.post("/api/chat", json={"query": "Compare methodologies across uploaded papers"})
assert r5.status_code == 200
data5 = r5.json()
assert len(data5["answer"]) > 50
assert len(data5["citations"]) > 0
print(f"✓ Chat endpoint verified: {len(data5['citations'])} citations returned")
print("\nALL 6 ENDPOINTS VERIFIED & 100% OPERATIONAL!")
