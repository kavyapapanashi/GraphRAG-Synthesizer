@echo off
title GraphRAG Frontend Dev
echo Starting GraphRAG React Dev Server on http://localhost:5173 ...
set "PATH=%CD%\tools\node-v20.18.0-win-x64;%PATH%"
cd frontend
npm run dev
pause
