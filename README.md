# Agentic Academic Assistant — NIT Jalandhar

An agentic RAG chatbot for Dr. B.R. Ambedkar National Institute of Technology, Jalandhar. Students and admins log in and chat with an AI assistant that autonomously calls tools to answer questions about attendance, results, CGPA/SGPA, and institute documents (syllabus, calendars, hostel/scholarship policies).

## 🔗 Live Deployment

| Service | URL |
|---|---|
| Frontend (Next.js Dashboard) | https://agentic-academic-assistant-seven.vercel.app |
| Backend API (FastAPI) | https://assistant-fastapi.onrender.com |
| MCP Data Server (Spring Boot) | https://assistant-spring-mcp.onrender.com |

> Free-tier Render services spin down when idle — the first request after inactivity can take 30–60s to wake up. A [GitHub Actions cron job](.github/workflows/keep-alive.yml) pings both `/health` endpoints every 10 minutes to reduce cold starts.

## 🔑 Demo Login

Use the admin account on the login page to explore the admin dashboard (all-student data, semester metrics, registration):

```
Username: Admin
Password: admin123
```

> ⚠️ **Security note:** These are real working credentials for the live deployment above, checked into this README at the project owner's request. They are compared with `hmac.compare_digest` against `ADMIN_USERNAME`/`ADMIN_PASSWORD` in `.env` (see [api/chat_routes.py](api/chat_routes.py)) — anyone with this README can log in as admin against the live database. Treat this as a demo/portfolio deployment, not production, and rotate `ADMIN_PASSWORD` (and redeploy) if that ever changes.

Student login uses a real roll number + password stored (Argon2-hashed) in the `students` table — there's no public demo student account since that data is seeded per real student.

## 📖 What it does

- **Conversational student assistant** — students ask natural-language questions ("What's my CGPA?", "Am I detained for low attendance?", "When does the odd semester end?") and get answers grounded in their own academic records or institute documents.
- **Role-aware routing** — a supervisor LLM node classifies every query into one of three intents (academics / student / admin) and routes it to a specialist agent, so a student can never trigger an admin-only tool.
- **Retrieval-Augmented Generation (RAG)** — institute PDFs (academic calendars, hostel rules, scholarship notices, placement policy) are chunked, embedded, and retrieved via FAISS to ground answers about policy/curriculum questions.
- **Live data via MCP (Model Context Protocol)** — the Python agent never talks to the student database directly. Instead it calls tools over MCP against a separate Spring Boot service, which owns the Postgres schema (students, attendance, results, employees, payroll).
- **Admin dashboard** — bulk views of all students, semester-wide attendance/academic metrics, student registration, and attendance updates.
- **Data-minimization guardrails** — a column allow-list and field masking layer (`security/policy.py`, `security/filter.py`, `security/masking.py`) strip sensitive fields (roll number, password hash) and mask PII (email, phone) before anything reaches the LLM, plus an audit log (`security/audit_logger.py`) of every tool call.
- **Streaming chat** — answers stream back to the frontend over Server-Sent Events (SSE) as the agent works, instead of waiting for the full response.

## 🏗️ Architecture & structure

The system is three independently deployable pieces that talk over HTTP:

```
frontend/Dashboard  (Next.js)  ──HTTP/JWT──▶  FastAPI backend (this repo root)
                                                     │
                                          LangGraph agent (agents/agents.py)
                                          ├─ FAISS RAG over documents/ (rag/, ingestion/)
                                          └─ MCP client (tools/mcp_tool.py)
                                                     │  Streamable HTTP (MCP)
                                                     ▼
                                          demo/ (Spring Boot MCP server)
                                                     │  JPA
                                                     ▼
                                          Postgres (Neon) — students, attendance,
                                          results, employees, payroll
```

### Repository layout

```
.
├── app.py                  # FastAPI app entrypoint, CORS setup, /health
├── config.py                # Gemini LLM client factory
├── api/chat_routes.py        # /login, /ask-me/stream endpoints
├── agents/agents.py           # LangGraph state machine (supervisor + 3 specialist nodes)
├── tools/                    # Agent tools: mcp_tool.py (calls Spring MCP), document_tool.py (RAG)
├── rag/retriever.py           # FAISS retriever over Gemini embeddings
├── ingestion/                # loader.py, chunker.py, embed_store.py — PDF → vector store pipeline
├── ingest.py                  # One-off script: (re)build the FAISS index from documents/
├── documents/                 # Source PDFs (calendars, hostel rules, scholarships, placement policy)
├── vector_store/               # Persisted FAISS index (index.faiss, index.pkl)
├── database/db.py             # Postgres (psycopg) connection for login lookups
├── services/                 # auth_services.py (password hashing, JWT), security_service.py (JWT auth dependency)
├── security/                  # policy.py, filter.py, masking.py, audit_logger.py — data-minimization guardrails
├── tests/                     # pytest unit tests
├── demo/                      # Spring Boot MCP data server (Java/Maven)
│   └── src/main/java/com/example/demo/
│       ├── config/            # McpToolConfig (exposes @Tool methods over MCP), SecurityConfig (JWT + CORS)
│       ├── controller/        # EmployeeController, HealthController
│       ├── service/           # StudentToolService (MCP tools), EmployeeService, payroll logic
│       ├── model/ repository/  # JPA entities & Spring Data repositories
│       └── security/          # JwtAuthenticationFilter, JwtTokenService
└── frontend/Dashboard/         # Next.js 16 + React 19 chat UI and admin dashboard
    ├── app/                    # App Router pages: /, /login, /dashboard, /dashboard/admin
    └── components/             # Chat UI (polar/), shadcn/ui primitives (ui/), admin forms
```

## 🧩 Key components

| Component | Responsibility |
|---|---|
| **Supervisor agent** (`agents/agents.py`) | Classifies each query into `academics_node` / `student_node` / `admin_node` and routes accordingly, using Gemini and recent chat history. |
| **Student / Admin agents** | ReAct-style tool-calling agents (LangGraph `create_react_agent`) that autonomously decide which MCP tools to invoke, loop until they have enough data, then answer. |
| **Academics agent** | Pure RAG node — retrieves top-k chunks from FAISS and answers from institute documents only. |
| **MCP tool bridge** (`tools/mcp_tool.py`) | Talks to the Spring Boot service over Streamable-HTTP MCP, off the event loop via a daemon thread pool, with timeouts and structured error payloads. |
| **Spring Boot MCP server** (`demo/`) | Owns the Postgres schema and exposes student/admin data as MCP tools (`StudentToolService`) plus a REST API for employee/payroll management, secured with JWT + role-based access. |
| **Auth** | FastAPI issues its own HS256 JWTs (`services/auth_services.py`) after checking either the hardcoded admin env credentials or a hashed password in the `students` table; the Spring service independently validates JWTs (`JwtAuthenticationFilter`) for its protected routes. |
| **Data guardrails** (`security/`) | `ALLOWED_COLUMNS` allow-list, PII masking for email/phone, and an audit log of every RAG tool call — so the LLM only ever sees minimized data. |
| **Frontend** (`frontend/Dashboard/`) | Next.js App Router UI — chat interface, login, protected routes, and an admin dashboard for registering students and editing attendance. |

## 🛠️ Technologies used & why

**Backend (FastAPI service — this repo root)**
- **Python 3.12** — pinned in [Dockerfile](Dockerfile) for the deployed image (local dev used 3.14; no version-specific syntax is used, so either works).
- **FastAPI** + **Uvicorn** — async-first, minimal-boilerplate framework with native `StreamingResponse` support, needed for SSE token streaming to the chat UI.
- **LangGraph** — models the supervisor/specialist routing as an explicit state graph instead of a single monolithic prompt, so admin/student/academics logic stays isolated and independently testable, and `MemorySaver` gives per-session conversation memory for free.
- **LangChain (core, google-genai, community, text-splitters)** — standard tool-calling and document-loading abstractions (`@tool`, `create_react_agent`, `RecursiveCharacterTextSplitter`) so agent/tool code isn't hand-rolled against the raw Gemini API.
- **Google Gemini** (`gemini-2.5-flash` for chat, `gemini-2.5-flash-lite` for routing, `gemini-embedding-001` for embeddings) — cost-effective for a student-facing tool with generous free-tier quota; the lighter model is used for cheap intent routing, the fuller model for actual answers.
- **FAISS** (`faiss-cpu`) — local, dependency-light vector index; no external vector DB service needed for a document set this size.
- **psycopg (binary)** — direct Postgres access for the login/roll-number lookup that FastAPI itself owns.
- **passlib[argon2]** — Argon2 is the current OWASP-recommended password hash (memory-hard, GPU-resistant) for student password storage.
- **PyJWT** — signs/verifies the app's own HS256 access tokens.
- **python-dotenv** — loads `.env` locally; in deployment, Render injects real environment variables instead.

**Data server (`demo/` — Spring Boot MCP server)**
- **Java 17** + **Spring Boot 3.4.5** — LTS Java plus the current Boot line, required by `spring-ai` 1.1.0.
- **Spring AI MCP Server (WebMVC, Streamable HTTP)** — the reference way to expose Java methods as MCP tools consumable by the Python LangChain agent, keeping the database and business logic in one strongly-typed service instead of duplicating student/payroll logic in Python.
- **Spring Data JPA** + **PostgreSQL driver** — ORM over the same Neon Postgres instance the FastAPI service reads for login.
- **Spring Security** + **jjwt** (0.12.6) — validates the JWTs issued by FastAPI so admin-only endpoints (`/api/employees/**`) are enforced independently on this service too.
- **Lombok** — removes entity/DTO boilerplate.
- **Maven** (wrapper committed via `mvnw`) — standard build tool for the module; no local Maven install required.

**Frontend (`frontend/Dashboard/`)**
- **Next.js 16** (App Router) + **React 19** — modern React with server components/App Router for the dashboard, chat, and admin pages.
- **TypeScript 5** — type safety across API calls, JWT-derived user state, and form data.
- **Tailwind CSS 4** + **shadcn/ui (Radix UI primitives)** — accessible, unstyled component primitives (dialog, dropdown, tabs, etc.) styled with Tailwind, so most UI in `components/ui/` is generated rather than hand-built.
- **react-hook-form + zod** — typed form validation for login/admin forms.
- **react-markdown** — renders the assistant's markdown-formatted answers (tables, lists) in the chat.
- **recharts** — charts on the admin dashboard for semester metrics.
- **@vercel/analytics** — usage analytics on the Vercel-deployed frontend.

**Infra**
- **Render** — hosts both backend services (FastAPI + Spring Boot) as Docker/native web services with free-tier auto-sleep.
- **Vercel** — hosts the Next.js frontend.
- **Neon (serverless Postgres)** — shared Postgres database for both backend services.
- **GitHub Actions** (`keep-alive.yml`) — cron job every 10 minutes to ping both services' `/health` and reduce Render cold-start latency.

## ⚙️ Environment variables

**Root `.env`** (FastAPI service) — see [.env.example](.env.example):

| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key for chat/routing/embeddings |
| `DATABASE_URL` | Postgres connection string (Neon), used for student login lookups |
| `SECRET_KEY` | HS256 signing secret for JWTs issued by `/login` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime (default 60) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Hardcoded admin login (see [🔑 Demo Login](#-demo-login)) |
| `SPRING_MCP_URL` | URL of the Spring Boot MCP endpoint, e.g. `http://localhost:8080/mcp` |
| `FRONTEND_ORIGINS` | Comma-separated allowed CORS origins for the deployed frontend |

**`demo/` (Spring Boot)** — see `demo/.env.example` / `application.properties`: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASS` (or a single `JDBC_DATABASE_URL`), `PORT`.

**`frontend/Dashboard/.env`** — see [.env.example](frontend/Dashboard/.env.example): `NEXT_PUBLIC_API_URL` (FastAPI base URL), `NEXT_PUBLIC_SPRING_API_URL` (Spring Boot base URL, if called directly).

## 🚀 Running it locally

You need all three services running for the full flow (chat + admin data). The academics/RAG-only flow only needs the FastAPI service.

### 1. FastAPI backend (repo root)

```bash
python -m venv .venv
.venv\Scripts\activate          # PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

copy .env.example .env           # then fill in real values
python ingest.py                 # builds vector_store/ from documents/ (run once, or after adding PDFs)

uvicorn app:app --reload --port 8000
```
API docs available at `http://localhost:8000/docs`. Health check: `http://localhost:8000/health`.

### 2. Spring Boot MCP data server (`demo/`)

```bash
cd demo
copy .env.example .env           # fill in DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASS
./mvnw spring-boot:run            # Windows: mvnw.cmd spring-boot:run
```
Runs on `http://localhost:8080` (MCP endpoint at `/mcp`, health at `/health`).

### 3. Frontend (`frontend/Dashboard/`)

```bash
cd frontend/Dashboard
npm install
copy .env.example .env           # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
Open `http://localhost:3000`.

### Running tests

```bash
pytest tests/
```

### Building for production

```bash
# FastAPI (Docker, matches Render deployment)
docker build -t academic-assistant-api .
docker run -p 8000:8000 --env-file .env academic-assistant-api

# Spring Boot
cd demo && ./mvnw clean package && java -jar target/demo-0.0.1-SNAPSHOT.jar

# Frontend
cd frontend/Dashboard && npm run build && npm start
```

## 🔒 Security notes

- Student passwords are Argon2-hashed (`services/auth_services.py`); the admin login is the one hardcoded exception, documented above.
- Login username/password comparisons for the admin path use `hmac.compare_digest` to avoid timing attacks.
- The agent never queries the database directly — it only sees data returned by MCP tools, which are filtered through `security/policy.py`'s column allow-list and `security/masking.py` before reaching the LLM.
- Every RAG document search is written to `logs/ai_audit.log` via `security/audit_logger.py`.
- `.env` files are git-ignored and are **not** committed; only the values explicitly documented in this README (the demo admin credentials) are intentionally public.
