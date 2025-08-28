# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Project Agent is a multi-agent collaboration system for bid document generation and processing. It uses a FastAPI backend with LangGraph workflow orchestration and a Next.js 14 frontend. The system specializes in document parsing, key information extraction, and automated bid generation.

## Development Commands

### Backend (Python)
```bash
# Setup environment (in backend directory)
cd backend

# Option 1: Using uv sync (recommended modern approach)
uv venv --python 3.11
uv sync

# Start backend server (enhanced auto-reload)
source .venv/bin/activate  # Linux/Mac
python dev.py  # Optimized development server with faster reload

# Enhanced dev.py features:
# - Faster reload with reduced delay (0.25s)
# - Specific reload directories only
# - Excludes cache and session directories
# - Proper PYTHONPATH setup

# Alternative: Traditional uvicorn command
# uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info --reload

# Option 2: Using uv pip (traditional pip-compatible approach)
uv venv --python 3.11
source .venv/bin/activate  # Linux/Mac
uv pip install -e .
python dev.py  # Use enhanced dev server

# Option 3: Try uv run (may have build issues in some environments)
uv venv --python 3.11
uv sync
uv run python dev.py  # Enhanced auto-reload

# Option 4: Using conda + uv (hybrid approach)
conda create -n sln-agent python=3.11 -y
conda activate sln-agent

# Method A: Use uv sync (modern, but may create separate venv)
uv sync
source .venv/bin/activate  # uv sync creates its own .venv
uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info --reload

# Method B: Use uv pip (installs directly in conda env)
# Option B1: Install dependencies directly (recommended to avoid build issues)
uv pip install fastapi uvicorn[standard] langgraph langchain langchain-openai langchain-anthropic openai pydantic pydantic-settings python-multipart python-docx pypdf2 aiofiles httpx "python-jose[cryptography]" "passlib[bcrypt]"

# Option B2: Try editable install (may have build issues)
uv pip install -e .

uvicorn main:app --host 0.0.0.0 --port 8001 --log-level info --reload

# Fallback: Direct Python execution
PYTHONPATH=/root/project/git/project-agent/backend python main.py
```

### Frontend (Node.js)
```bash
cd frontend
npm install
npm run dev      # Development server with Turbopack (faster hot reload)
npm run dev:legacy  # Fallback: Standard Next.js dev server
npm run build    # Production build  
npm run start    # Production server
npm run lint     # ESLint
```

**注意**: 如果遇到热重载问题，尝试：
- 使用 `npm run dev` (Turbopack版本) 获得更快的热重载
- 如果有兼容性问题，使用 `npm run dev:legacy`
- 确保文件保存后浏览器会自动刷新（无需手动回车）

### Code Quality
```bash
# Python linting (configured in pyproject.toml)
cd backend
ruff check .
ruff format .

# Frontend linting
cd frontend && npm run lint

# Type checking (frontend)
cd frontend && npx tsc --noEmit
```

## Architecture

### Multi-Agent System
The system implements specialized AI agents with the following current implementations:

1. **Coordinator Agent** (`backend/agents/coordinator.py`) - Master orchestrator, dialogue management
2. **Document Parser Agent** (`backend/agents/document_parser.py`) - Document analysis and content extraction
3. **Key Extraction Agent** (`backend/agents/key_extraction.py`) - Information extraction from documents
4. **Bid Generator Agent** (`backend/agents/bid_generator.py`) - Bid document generation
5. **Bid Format Agent** (`backend/agents/bid_format_agent.py`) - Format optimization for bid documents

### Core Workflow
Built on LangGraph with state-driven workflow (`backend/workflow/`):
- State management in `state.py` with WorkflowState TypedDict
- Simplified workflow orchestration in `graph.py` with coordinator-based routing
- Session-based conversation management with iteration control
- Dynamic agent dispatch through coordinator node

### LLM Integration
- Uses OpenRouter as unified interface (`backend/app_core/llm_client.py`)
- Supports multiple providers: OpenAI, Anthropic, OpenRouter
- Default model assignments per agent type
- Temperature settings configured per agent

## Key Configuration

### Environment Variables
Required `.env` file in project root:
```
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

### Model Configuration
Agent-specific models defined in `backend/app_core/llm_client.py`:
- Coordinator: `anthropic/claude-3.5-sonnet` (temp: 0.3)
- Document Parser: `anthropic/claude-3-haiku` (temp: 0.1)
- Key Extraction: `anthropic/claude-3.5-sonnet` (temp: 0.2)
- Bid Generator: `openai/gpt-4-turbo` (temp: 0.5)
- All agents use OpenRouter as the unified interface

### File Processing
- Upload limit: 50MB per file
- Supported formats: PDF (PyPDF2), DOCX (python-docx), TXT, MD
- File processor service: `backend/services/file_processor.py`

## API Structure

### REST Endpoints (`backend/api/v1/endpoints/`)
- `/api/v1/chat/*` - Chat and messaging
- `/api/v1/files/*` - File upload and management  
- `/api/v1/sessions/*` - Session management
- `/api/v1/proposals/*` - Solution proposals

### Frontend Architecture (`frontend/`)
- Next.js 14 with App Router
- Three-panel interface: FileTree + MarkdownEditor + ChatPanel
- Custom hooks for chat and session management
- Real-time text optimization with selection popup

## Development Notes

### Virtual Environment
- Python venv created in `backend/` directory as `.venv/`
- Backend-specific dependency management
- Use `uv` for Python package management

### Code Standards  
- Python: Ruff linting (line length: 88), target Python 3.11+
- Frontend: ESLint with Next.js config, TypeScript strict mode
- No code comments unless explicitly requested

### Testing & Deployment
- Backend runs on localhost:8001 (API docs at /docs)
- Frontend runs on localhost:3000  
- CORS configured for development
- Async/await throughout for scalability
- uv.lock file for reproducible Python dependencies

### Environment Verification
```bash
# Check backend environment
cd backend
python -c "import sys; print(f'Python {sys.version}'); import fastapi; print('FastAPI OK')"

# Check frontend environment  
cd frontend
node -v
npm -v
```

### Workflow Understanding
1. User input → Coordinator analysis
2. Optional file upload → Document parsing and key extraction
3. Bid format analysis → Template identification
4. Bid generation → Complete document creation
5. Real-time text optimization available via selection
6. Session snapshots and state management

## Package Management

Backend uses `pyproject.toml` with uv for modern Python dependency management:
- Project name: `sln-agent` 
- Python 3.11+ requirement
- Core dependencies: FastAPI, LangGraph, LangChain, OpenAI, Anthropic
- Document processing: python-docx, PyPDF2
- Development tools: Ruff for linting and formatting
- Lock file (`uv.lock`) for reproducible builds

Frontend uses standard `package.json` with npm:
- Next.js 14.0.0 with React 18
- TypeScript and Tailwind CSS
- Document rendering: react-markdown with syntax highlighting
- File upload and real-time optimization features

## Troubleshooting

### Common Issues

**Backend won't start:**
```bash
# Check if virtual environment exists
cd backend && ls -la .venv/

# Recreate virtual environment if needed
uv venv --python 3.11 --force
uv sync
```

**Frontend build issues:**
```bash
# Clear node_modules and reinstall
cd frontend && rm -rf node_modules package-lock.json
npm install
```

**CORS errors:**
- Ensure backend is running on port 8001
- Check frontend is on port 3000
- Verify `BACKEND_CORS_ORIGINS` in config

**API Key issues:**
- Create `.env` file in project root
- Add `OPENROUTER_API_KEY=your-key-here`
- Restart backend server after changes