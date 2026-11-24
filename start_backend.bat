@echo off
title GraphRAG Backend
echo Starting GraphRAG FastAPI Backend on http://localhost:8000 ...
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
pause
