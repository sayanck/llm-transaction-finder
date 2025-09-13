# LLM Transaction Pattern Finder

A hybrid rule-based + AI system to detect suspicious transaction patterns.

## Quick start (dev)
1. Place Transaction_data_All.xlsx in project root (or run in mock mode).
2. From project root run: ./run.sh  # on Git Bash / macOS / Linux
3. Frontend: http://localhost:3000
4. Backend:  http://localhost:8000 (API docs: /docs)

## Repo layout
- backend/  # FastAPI + data processing + llm analyzer
- frontend/ # React + TypeScript UI
- run.sh    # quick-start script
