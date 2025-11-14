# Mock Trial AI - Project Blueprint

## 🎯 Project Overview

**Mock Trial AI** is an AI-powered legal case simulator where two sides submit evidence, and an AI judge delivers verdicts that evolve through argument rounds.

### Core Flow
```
Login → Create Case → Upload Docs (Side A & B) → Initial Verdict (Round 0)
→ Argument Round 1-5 → Finalize Verdict → Export Report
```

---

## 🛠️ Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Backend** | Python 3.11 + FastAPI | Fast async, auto API docs, great AI libraries |
| **Database** | PostgreSQL 15 | Reliable, JSONB support for verdicts |
| **ORM** | SQLAlchemy 2.0 | Type-safe, great for TDD |
| **AI** | OpenAI GPT-4o-mini | Document extraction & verdict generation |
| **Testing** | pytest + pytest-asyncio | Industry standard for Python TDD |
| **Frontend** | React 18 + Tailwind CSS | Modern, component-based |
| **Containerization** | Docker + Docker Compose | Easy local dev & deployment |

---

## 📊 Database Schema (SQLAlchemy Models)

### Core Tables

```python
# models/user.py
class User:
    id: UUID (PK)
    phone_hash: str (unique, indexed)
    full_name: str (nullable)
    created_at: datetime
    last_login: datetime

# models/case.py
class Case:
    id: UUID (PK)
    case_number: str (unique, auto: CAS-2025-001234)
    title: str
    case_type: str (civil, criminal, corporate, etc.)
    jurisdiction: str

    created_by: UUID (FK -> User)
    status: str (draft, ready, in_progress, finalized)
    current_round: int (default 0, max 5)

    created_at: datetime
    finalized_at: datetime (nullable)

# models/document.py
class Document:
    id: UUID (PK)
    case_id: UUID (FK -> Case)
    side: str ('A' or 'B')

    title: str
    file_name: str
    file_path: str
    file_type: str (pdf, docx, txt)

    full_text: text (extracted by GPT-4o-mini)
    page_count: int

    uploaded_by: UUID (FK -> User)
    uploaded_at: datetime

# models/argument.py
class Argument:
    id: UUID (PK)
    case_id: UUID (FK -> Case)
    round: int (1-5)
    side: str ('A' or 'B')

    argument_text: text
    submitted_by: UUID (FK -> User)
    submitted_at: datetime

# models/verdict.py
class Verdict:
    id: UUID (PK)
    case_id: UUID (FK -> Case)
    round: int (0 = initial, 1-5 = after arguments)

    verdict_json: JSONB
    # Structure:
    # {
    #   "summary": "...",
    #   "winner": "A" | "B" | "undecided",
    #   "confidence_score": 0.85,
    #   "issues": [
    #     {
    #       "issue": "Was contract valid?",
    #       "finding": "Yes",
    #       "reasoning": "..."
    #     }
    #   ],
    #   "final_decision": "...",
    #   "key_evidence_cited": ["Doc A - Contract", "Doc B - Email"]
    # }

    model_used: str (gpt-4o-mini)
    tokens_used: int
    created_at: datetime
```

---

## 🔌 API Endpoints (FastAPI)

### Authentication
```
POST   /api/auth/login              # Demo phone login → JWT
POST   /api/auth/logout             # Invalidate token
GET    /api/auth/me                 # Get current user
```

### Cases
```
GET    /api/cases                   # List user's cases
POST   /api/cases                   # Create new case
GET    /api/cases/{case_id}         # Get case details + all related data
DELETE /api/cases/{case_id}         # Delete case
```

### Documents
```
POST   /api/cases/{case_id}/documents        # Upload document (multipart/form-data)
                                             # Body: file, side ('A'/'B'), title
GET    /api/cases/{case_id}/documents        # List all docs for case
GET    /api/cases/{case_id}/documents/{doc_id}  # Get single document
DELETE /api/cases/{case_id}/documents/{doc_id}  # Delete document
```

### Verdicts
```
POST   /api/cases/{case_id}/verdict          # Generate initial verdict (Round 0)
                                             # Requires: both sides have docs
GET    /api/cases/{case_id}/verdicts         # Get all verdicts for case
GET    /api/cases/{case_id}/verdicts/{round} # Get verdict for specific round
```

### Arguments
```
POST   /api/cases/{case_id}/arguments        # Submit argument
                                             # Body: side, argument_text
                                             # Auto-generates new verdict for round+1
GET    /api/cases/{case_id}/arguments        # Get all arguments
```

### Reports
```
POST   /api/cases/{case_id}/finalize         # Finalize case → generate report
GET    /api/cases/{case_id}/report           # Download final report (PDF)
```

---

## 🗂️ Project Structure

```
AIJudge/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings (env vars)
│   │   │
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── document.py
│   │   │   ├── argument.py
│   │   │   └── verdict.py
│   │   │
│   │   ├── schemas/                   # Pydantic schemas (request/response)
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── case.py
│   │   │   ├── document.py
│   │   │   ├── argument.py
│   │   │   └── verdict.py
│   │   │
│   │   ├── api/                       # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── cases.py
│   │   │   ├── documents.py
│   │   │   ├── verdicts.py
│   │   │   └── arguments.py
│   │   │
│   │   ├── services/                  # Business logic (CORE!)
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── document_service.py    # GPT-4o-mini extraction
│   │   │   ├── verdict_orchestrator.py # Main orchestrator
│   │   │   ├── argument_orchestrator.py
│   │   │   └── openai_service.py      # OpenAI API wrapper
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── database.py            # DB connection
│   │   │   └── session.py             # Session management
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── security.py            # JWT, password hashing
│   │   │   └── file_handler.py        # File upload/storage
│   │   │
│   │   └── dependencies.py            # FastAPI dependencies (get_db, get_current_user)
│   │
│   ├── tests/                         # TDD tests
│   │   ├── __init__.py
│   │   ├── conftest.py                # Pytest fixtures
│   │   ├── test_auth.py
│   │   ├── test_cases.py
│   │   ├── test_documents.py
│   │   ├── test_verdicts.py
│   │   ├── test_arguments.py
│   │   └── test_orchestrator.py       # Critical tests!
│   │
│   ├── alembic/                       # Database migrations
│   │   └── versions/
│   │
│   ├── uploads/                       # Uploaded files (local storage)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── pytest.ini
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── CasePage.jsx
│   │   ├── components/
│   │   │   ├── DocumentUpload.jsx
│   │   │   ├── VerdictDisplay.jsx
│   │   │   ├── ArgumentForm.jsx
│   │   │   └── RoundTimeline.jsx
│   │   ├── services/
│   │   │   └── api.js                 # Axios wrapper
│   │   └── App.jsx
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧪 TDD Approach

### Testing Philosophy
1. **Write test first** (Red)
2. **Write minimal code to pass** (Green)
3. **Refactor** (Refactor)

### Test Levels

#### 1. Unit Tests (Services)
```python
# tests/test_document_service.py
async def test_extract_text_from_pdf():
    # Test GPT-4o-mini extraction

async def test_chunk_text():
    # Test text chunking logic

# tests/test_verdict_orchestrator.py
async def test_build_initial_verdict_prompt():
    # Test prompt construction

async def test_parse_verdict_response():
    # Test JSON parsing
```

#### 2. Integration Tests (API)
```python
# tests/test_cases.py
async def test_create_case(client, auth_token):
    response = await client.post("/api/cases", ...)
    assert response.status_code == 201

async def test_upload_document(client, auth_token, test_case):
    # Test file upload endpoint
```

#### 3. E2E Tests (Full Flow)
```python
# tests/test_full_flow.py
async def test_complete_case_flow():
    # Login → Create Case → Upload → Verdict → Arguments → Finalize
```

### Test Fixtures (conftest.py)
```python
@pytest.fixture
async def db_session():
    # Create test database session

@pytest.fixture
async def test_user(db_session):
    # Create test user

@pytest.fixture
async def test_case(db_session, test_user):
    # Create test case

@pytest.fixture
def mock_openai():
    # Mock OpenAI responses for fast tests
```

---

## 🎭 Orchestrator Pattern (Core Logic)

### VerdictOrchestrator (services/verdict_orchestrator.py)

```python
class VerdictOrchestrator:
    """
    Coordinates verdict generation:
    1. Fetch documents for both sides
    2. Build structured prompt
    3. Call OpenAI GPT-4o-mini
    4. Parse & validate response
    5. Save verdict to DB
    """

    async def generate_initial_verdict(self, case_id: UUID) -> Verdict:
        # Round 0: No arguments yet

    async def generate_verdict_with_arguments(
        self,
        case_id: UUID,
        round: int
    ) -> Verdict:
        # Round 1-5: Include arguments in prompt
```

### Key Methods
```python
async def _fetch_case_context(self, case_id: UUID) -> dict:
    """
    Returns:
    {
        "case": Case object,
        "side_a_docs": [Document, ...],
        "side_b_docs": [Document, ...],
        "arguments": [Argument, ...],  # for current round
        "previous_verdict": Verdict or None
    }
    """

async def _build_prompt(self, context: dict, round: int) -> str:
    """
    Constructs prompt for GPT-4o-mini
    """

async def _call_openai(self, prompt: str) -> dict:
    """
    Calls OpenAI API, returns parsed JSON
    """

async def _save_verdict(self, case_id: UUID, round: int, verdict_data: dict) -> Verdict:
    """
    Saves verdict to database
    """
```

---

## 🚀 Development Workflow

### Phase 1: Setup (Day 1)
```bash
# 1. Initialize project
cd AIJudge/backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary alembic pytest pytest-asyncio openai python-multipart python-jose[cryptography] passlib[bcrypt]

# 3. Setup Docker Compose
docker-compose up -d postgres

# 4. Run migrations
alembic upgrade head

# 5. Run tests
pytest

# 6. Run dev server
uvicorn app.main:app --reload
```

### Phase 2: TDD Loop
```
1. Write test for feature (RED)
2. Run: pytest tests/test_xxx.py -v
3. Write minimal code (GREEN)
4. Run tests again
5. Refactor
6. Commit
```

### Phase 3: API Testing
```
# Auto-generated docs at:
http://localhost:8000/docs  (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

---

## 🔐 Environment Variables (.env)

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mocktrialai

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days for demo

# OpenAI
OPENAI_API_KEY=sk-...

# App
ENVIRONMENT=development
DEBUG=True
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
```

---

## 📝 Git Workflow

```bash
# Feature branches
git checkout -b feature/auth-system
git checkout -b feature/document-upload
git checkout -b feature/verdict-generation

# Commit format
git commit -m "test: add document upload endpoint tests"
git commit -m "feat: implement document extraction service"
git commit -m "fix: handle edge case in verdict parsing"
```

---

## 🎯 MVP Features Checklist

### Backend
- [ ] User authentication (phone-based demo login)
- [ ] Case CRUD operations
- [ ] Document upload & extraction (GPT-4o-mini)
- [ ] Initial verdict generation (Round 0)
- [ ] Argument submission (max 5 rounds)
- [ ] Verdict regeneration after arguments
- [ ] Case finalization
- [ ] All endpoints tested (pytest)

### Frontend (after backend)
- [ ] Login page
- [ ] Dashboard (case list)
- [ ] Case page (split layout: Side A | Judge | Side B)
- [ ] Document upload component
- [ ] Verdict display component
- [ ] Argument form
- [ ] Round timeline/history

---

## 🚢 Deployment Strategy (for Interview)

### Docker
```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15

  backend:
    build: ./backend
    depends_on:
      - postgres

  frontend:
    build: ./frontend
    depends_on:
      - backend
```

### Production (Kubernetes)
```
- Backend: 3 replicas (auto-scaling)
- PostgreSQL: StatefulSet with persistent volume
- Ingress: NGINX for routing
- Secrets: Kubernetes Secrets for API keys
- Monitoring: Prometheus + Grafana
- Logging: ELK stack
- CI/CD: GitHub Actions → Build → Test → Deploy to GKE/EKS
```

---

## 🎤 Interview Talking Points

### Scalability (1000s of users)
1. **Horizontal scaling**: Add more backend pods
2. **Database connection pooling**: SQLAlchemy pool_size=20
3. **Rate limiting**: Per-user API rate limits (5 verdicts/hour)
4. **Async processing**: FastAPI's async for concurrent requests
5. **File storage**: Move to S3/GCS for production

### Caching Strategy
1. **Application level**: LRU cache for repeated prompts (functools.lru_cache)
2. **Database**: Proper indexes on case_id, user_id, round
3. **HTTP**: Cache-Control headers for static assets

### Why This Architecture?
1. **FastAPI**: Auto API docs, async support, type safety
2. **SQLAlchemy**: Prevents SQL injection, easy migrations
3. **Orchestrator pattern**: Separates business logic from API routes
4. **TDD**: Catches bugs early, enables refactoring

---

## 🧠 Product Differentiation Ideas

### Core Features (MVP)
✅ Side A/B document upload
✅ AI judge verdict (structured JSON)
✅ 5 argument rounds
✅ Verdict evolution tracking

### Bonus Features (if time allows)
- **Evidence strength meter**: Visual bar showing Side A vs B strength
- **Bias detection**: Flag potential biases in AI reasoning
- **Legal precedent references**: AI cites similar cases
- **Collaboration mode**: Multiple users per side
- **Real-time typing indicators**: WebSocket notifications

### Real-World Impact
- **Law students**: Practice for moot courts
- **Legal aid organizations**: Quick case evaluation
- **Judges**: Pre-hearing analysis tool
- **Accessibility**: AI legal assistance for underserved communities

---

## 📚 Key Dependencies

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
openai==1.3.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1  # for testing FastAPI
```

---

## ✅ Next Steps

1. **Setup project structure**
2. **Configure Docker Compose**
3. **Write first test** (auth login)
4. **Implement feature** (TDD loop)
5. **Repeat** for each endpoint

---

**Ready to start building! 🚀**
