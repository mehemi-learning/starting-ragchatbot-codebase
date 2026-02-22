# CLAUDE.md!!

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run the application (from repo root, requires Git Bash on Windows):**
```bash
./run.sh
```

**Or manually:**
```bash
cd backend && uv run uvicorn app:app --reload --port 8000
```

App runs at `http://localhost:8000`. API docs at `http://localhost:8000/docs`.

**Install dependencies:**
```bash
uv sync
```

**Environment setup:** Create `.env` in the repo root with `ANTHROPIC_API_KEY=...`

There is no test suite configured.

## Architecture

This is a full-stack RAG chatbot. The backend is a FastAPI app (`backend/`) that serves the vanilla JS frontend (`frontend/`) as static files on `/`.

### Backend component map

| File | Role |
|---|---|
| `app.py` | FastAPI entry point. Two routes: `POST /api/query`, `GET /api/courses`. Initializes `RAGSystem` at startup and loads `/docs/*.txt` into ChromaDB. |
| `rag_system.py` | Central orchestrator. Wires together all components and exposes `query()` and `add_course_folder()`. |
| `document_processor.py` | Parses `.txt` course files into `Course` + `CourseChunk` objects. Splits content by `Lesson N:` markers, then chunks lesson text into sentence-boundary chunks with overlap. |
| `vector_store.py` | ChromaDB wrapper. Maintains two collections: `course_catalog` (one doc per course, used for fuzzy course-name resolution) and `course_content` (one doc per chunk, used for semantic search). Embeddings via `all-MiniLM-L6-v2`. |
| `ai_generator.py` | Anthropic API wrapper. Sends a single user message with tool definitions to Claude. If Claude calls `search_course_content`, executes the tool, appends results, and makes a second API call (no tools) for the final answer. |
| `search_tools.py` | Defines `CourseSearchTool` and `ToolManager`. The tool calls `VectorStore.search()` and formats results for Claude. Sources (course + lesson) are stored on the tool instance and retrieved after generation. |
| `session_manager.py` | In-memory conversation history keyed by session ID. History is injected into the system prompt, not the messages array. Trims to last `MAX_HISTORY * 2` messages. |
| `config.py` | Single `Config` dataclass with all tuneable constants (chunk size, overlap, max results, max history, model name, ChromaDB path). |
| `models.py` | Pydantic/dataclass models: `Course`, `Lesson`, `CourseChunk`. |

### Key design decisions

**Tool-use loop is limited to one round.** Claude calls the search tool at most once. `_handle_tool_execution()` makes a second Claude call with tool results but does not loop — it always calls without tools, forcing a final text response.

**Course name resolution uses vector search.** When `course_name` is passed to `CourseSearchTool`, `VectorStore._resolve_course_name()` queries the `course_catalog` collection semantically, so partial or fuzzy names resolve to the correct full title before filtering `course_content`.

**Sessions are server-side in-memory.** There is no persistence — sessions reset on server restart. History is formatted as a string appended to the system prompt rather than added as separate messages.

**Document ingestion is idempotent.** `add_course_folder()` fetches existing course titles from ChromaDB and skips files whose parsed title already exists.

**ChromaDB is persisted to `backend/chroma_db/`** (relative to where uvicorn runs, i.e. the `backend/` directory). Deleting this folder resets all indexed content.

### Course document format

Files in `/docs/` must follow this structure for correct parsing:
```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <title>
Lesson Link: <url>
<lesson text...>

Lesson 1: <title>
...
```
