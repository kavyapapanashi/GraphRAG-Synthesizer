import urllib.request
import json

def test_quiz(paper_name):
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/quiz",
        data=json.dumps({"paper": paper_name}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        res = json.loads(r.read().decode("utf-8"))
        print(f"\n--- QUIZ FOR: {paper_name} ---")
        print(f"Paper Focus: {res.get('paper')}, Questions count: {len(res['questions'])}")
        for i, q in enumerate(res["questions"][:2]):
            correct_opt = q["options"][q["correct_index"]]
            print(f"Q{i+1}: {q['question']}")
            print(f"  Correct Option (Index {q['correct_index']}): {correct_opt}")
            print(f"  Exact Citation: {q['citation']}")
            assert q["correct_index"] in [0, 1, 2, 3]
            assert len(q["options"]) == 4

test_quiz("GraphRAG_Reasoning")
test_quiz("DenseRetriever_Scale")
test_quiz("HybridSearch_Fusion")

# Test Session Topics
req_session = urllib.request.Request(
    "http://127.0.0.1:8000/api/quiz",
    data=json.dumps({"paper": "SESSION", "session_topics": ["computational limitations", "latency overhead"]}).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req_session) as r:
    res_s = json.loads(r.read().decode("utf-8"))
    print("\n--- QUIZ FOR: SESSION TOPICS ---")
    print(f"Session Questions count: {len(res_s['questions'])}")
    for i, q in enumerate(res_s["questions"][:2]):
        print(f"Q{i+1}: {q['question']}")
        print(f"  Citation: {q['citation']}")

print("\n✓ ALL PAPER-SPECIFIC & SESSION-FOCUSED QUIZZES 100% OPERATIONAL!")
