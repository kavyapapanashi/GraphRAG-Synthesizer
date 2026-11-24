# 🕸️ GraphRAG Multi-Paper Research & Study Synthesizer

A production-ready **GraphRAG (Knowledge Graph + Vector Store)** multi-paper research workspace combining a **FastAPI backend** with a **Gemini-Layout + Strict Neobrutalist React (Vite) + Tailwind CSS frontend** (and an optional Streamlit application).

---

## 🎨 Visual Design System: Strict Neobrutalism (Zero Emojis)
- **ZERO EMOJIS ANYWHERE** in buttons, tabs, headers, badges, or alerts. Uses clean typography and minimal `lucide-react` icons (`strokeWidth={2}`).
- **NO GRADIENTS, NO BLUR, NO ROUNDED PILLS.** Sharp corners (`rounded-none` or `rounded-[2px]`).
- **Color Palette:**
  - Main Canvas Background: Warm Off-White (`#F4F1EA`)
  - Sidebar & Cards Surface: Pure White (`#FFFFFF`)
  - Borders & Primary Text: Pure Black (`#000000`)
  - Primary Accent (Active states, Send button, Primary actions): Teal (`#00A896`)
  - Secondary Accent (Limitations, Contradictions, Reset/Warnings): Terracotta Red (`#C94A4A`)
  - Highlight Accent (Inline Citation Badges, Selected Items): Soft Ochre (`#F4D35E`)
- **Borders & Shadows:**
  - All containers, inputs, buttons, and tables use `border-2 border-black`.
  - Hard offset shadows: `shadow-[4px_4px_0px_0px_#000]`.
  - Button press-down active state: `active:translate-x-[2px] active:translate-y-[2px] active:shadow-none`.
- **Typography:**
  - `Space Grotesk` (bold headings, tabs, labels)
  - `Inter` (body prose, answers)
  - `JetBrains Mono` (exact citations like `[Paper 1, p. 4]`, stats, and graph metadata)

---

## 🖥️ Gemini Workspace Layout (Full Viewport)
1. **Collapsible Left Sidebar (`w-64`, `bg-white border-r-2 border-black`):**
   - Top bar: Sidebar collapse toggle + bold `+ NEW SESSION` button (`bg-[#00A896] text-white border-2 border-black shadow-[3px_3px_0px_0px_#000]`, calls `/api/reset`).
   - Sharp-edged navigation buttons:
     - `CHAT` (Default centered conversational view)
     - `KNOWLEDGE GRAPH` (Interactive visual network canvas)
     - `COMPARISON MATRIX` (Structured table + CSV export)
     - `STUDY QUIZ` (Active-recall MCQ & flashcards)
   - Sources list + 1-click `+ LOAD SAMPLES` button.
   - Monospace status footer (`PAPERS: X | NODES: Y | EDGES: Z`).

2. **Main Centered Chat Canvas (`max-w-3xl mx-auto w-full`):**
   - **Empty State:** Centered bold `Space Grotesk` greeting: `WHAT ARE WE RESEARCHING TODAY?` + 4 clickable Neobrutalist query cards.
   - **Conversation Thread:**
     - User message: right-aligned Teal block (`bg-[#00A896] text-white border-2 border-black shadow-[3px_3px_0px_0px_#000]`).
     - AI response: crisp white card (`bg-white border-2 border-black shadow-[4px_4px_0px_0px_#000] p-6`) with clean markdown formatting and clickable inline `JetBrains Mono` citation badges (`bg-[#F4D35E] border border-black px-1.5 py-0.5 text-xs`).
     - Collapsible drawers: `VIEW RETRIEVED GRAPH PATHS` (exact NetworkX triples used) and `VIEW RAW TEXT EVIDENCE` (ChromaDB passages with distances).
   - **Docked Bottom Prompt Bar:**
     - Fixed at bottom of chat view (`max-w-3xl mx-auto w-full mb-6`).
     - Sharp container (`bg-white border-2 border-black shadow-[5px_5px_0px_0px_#000]`):
       - Square `+` button (`border-2 border-black bg-[#F4F1EA]`) to upload 1–5 PDFs directly.
       - Center text input with keyboard `Enter` to send.
       - Sharp `SEND` button (`bg-[#00A896] text-white border-2 border-black font-bold px-5 py-2`).

3. **Secondary Workspace Views:**
   - **Knowledge Graph:** Full-area interactive canvas with Neobrutalist rectangular color-coded nodes (`Paper`, `Method`, `Dataset`, `Metric`, `Limitation`), categories filter bar, and side element inspector.
   - **Comparison Matrix:** High-contrast `border-2 border-black` table comparing `Paper Title`, `Methodology`, `Datasets`, `Key Metrics & Scores`, and `Known Limitations` (in Terracotta Red) + `EXPORT CSV` button in Soft Ochre + Contradiction & Outperformance cards.
   - **Study Quiz:** Sharp bordered MCQ cards with selectable option boxes, immediate scoring, Terracotta Red limitation warning tags, exact citations, and flip flashcards.

---

## 📁 Project Structure

```text
chatbot/
├── api/
│   ├── __init__.py
│   └── main.py                 # FastAPI backend REST API
├── core/
│   ├── __init__.py
│   ├── pdf_parser.py           # PyMuPDF parser + ChromaDB embedding storage
│   ├── graph_builder.py        # Gemini structured KG extraction + NetworkX graph
│   ├── retriever.py            # Hybrid 1-2 hop KG traversal + ChromaDB retrieval
│   └── synthesizer.py          # Grounded synthesis, matrix & active-recall quiz
├── frontend/                   # React (Vite) + Tailwind CSS Neobrutalist app
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx             # Main workspace orchestrator
│       ├── api.js              # FastAPI client
│       ├── index.css           # Tailwind + Neobrutalist design tokens
│       └── components/
│           ├── Sidebar.jsx     # Collapsible Neobrutalist sidebar
│           ├── ChatView.jsx    # Centered Gemini chat layout + bottom prompt bar
│           ├── GraphView.jsx   # Interactive knowledge graph canvas + inspector
│           ├── MatrixView.jsx  # Comparative table + CSV export
│           └── QuizView.jsx    # Active-recall MCQ quiz & flashcards
├── utils/
│   ├── __init__.py
│   ├── graph_viz.py            # PyVis visualizer
│   └── sample_papers.py        # Multi-page benchmark academic PDF generator
├── tests/
│   ├── test_pipeline.py        # Core pipeline tests (7 tests)
│   └── test_api.py             # FastAPI integration tests (6 tests)
├── start_backend.bat           # 1-click launch for FastAPI backend
├── start_frontend.bat          # 1-click launch for React frontend
└── start_all.bat               # 1-click launch for both servers
```

---

## 🚀 How to Run

### Method 1: 1-Click Launch (Recommended)
Double-click `start_all.bat` or run in terminal:
```cmd
start_all.bat
```
- **Backend:** `http://localhost:8000` (API docs at `http://localhost:8000/docs`)
- **Frontend:** `http://localhost:5173`

---

### Method 2: Manual Start

**Terminal 1 — FastAPI Backend:**
```powershell
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — React Frontend:**
```powershell
$env:PATH = "$pwd\tools\node-v20.18.0-win-x64;$env:PATH"
cd frontend
npm run dev
```
Open **`http://localhost:5173`** in your browser.

---

### Method 3: Optional Streamlit App
```powershell
streamlit run app.py
```

---

## 🧪 Running Verification Tests

Run the full integration test suite:
```powershell
python -m unittest tests/test_api.py tests/test_pipeline.py
```
*(All 13 tests pass cleanly in under 2 seconds).*
