# 🎯 Mock Trial AI - AI-Powered Legal Case Simulator

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.0-61dafb.svg)](https://reactjs.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)

An intelligent AI-powered mock trial system where two sides can submit evidence, present arguments, and receive AI-generated verdicts that evolve through multiple rounds of debate.

## 🌟 Features

### Core Functionality
- **📄 Document Upload & Processing**: Upload PDF, DOCX, and TXT files with automatic text extraction using GPT-4o-mini
- **⚖️ AI Judge System**: Intelligent verdict generation with structured reasoning and confidence scoring
- **🔄 Multi-Round Arguments**: Up to 5 rounds of arguments with dynamic verdict evolution
- **📊 Real-Time Updates**: See how arguments influence the AI judge's decision across rounds
- **🔒 Case Finalization**: Lock cases permanently after all rounds are complete
- **📱 Responsive UI**: Beautiful 3-column layout (Side A | Judge | Side B)

### Technical Highlights
- ✅ **87 Passing Tests** - Comprehensive test coverage with pytest
- ✅ **TDD Architecture** - Test-driven development from day one
- ✅ **RESTful API** - Auto-generated API documentation with FastAPI
- ✅ **Type Safety** - Pydantic schemas and SQLAlchemy 2.0 ORM
- ✅ **JWT Authentication** - Secure phone-based authentication
- ✅ **Async Support** - Fast, concurrent request handling

---

## 🏗️ Architecture

### Tech Stack

**Backend:**
- **FastAPI** 0.104 - Modern Python web framework
- **PostgreSQL** 15 - Reliable relational database
- **SQLAlchemy** 2.0 - Type-safe ORM
- **OpenAI** GPT-4o-mini - AI verdict generation & document extraction
- **Alembic** - Database migration management
- **pytest** - Testing framework

**Frontend:**
- **React** 18 - Modern UI library
- **Vite** 5.4 - Lightning-fast build tool
- **Tailwind CSS** 3.4 - Utility-first styling
- **React Router** - Client-side routing
- **Axios** - HTTP client with interceptors

### Project Structure

```
AIJudge/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   │   ├── argument_orchestrator.py
│   │   │   ├── verdict_orchestrator.py
│   │   │   ├── document_service.py
│   │   │   └── openai_service.py
│   │   ├── db/               # Database connection
│   │   ├── utils/            # Utilities
│   │   └── main.py           # FastAPI app
│   ├── tests/                # 87 passing tests
│   ├── alembic/              # Migrations
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── CasePage.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   └── App.jsx
│   └── package.json
├── test_documents/           # Sample test cases
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11+
- **Node.js** 18+
- **PostgreSQL** 15+
- **OpenAI API Key**

### 1. Clone Repository

```bash
git clone git@github.com:Shrutii-ti/Vaquill.git
cd Vaquill
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/mocktrialai
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
OPENAI_API_KEY=sk-your-openai-api-key
ENVIRONMENT=development
DEBUG=True
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=10
EOF

# Start PostgreSQL (ensure it's running)
# Create database
createdb mocktrialai

# Run migrations
alembic upgrade head

# Run tests
pytest

# Start backend server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be running at: **http://localhost:8000**

API Docs: **http://localhost:8000/docs**

### 3. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Frontend will be running at: **http://localhost:5173**

---

## 📖 Usage Guide

### 1. **Login**
- Enter a phone number (demo mode - any number works)
- Optionally provide name and email
- Receive JWT token for authentication

### 2. **Create Case**
- Click "New Case" on dashboard
- Fill in case details:
  - Title (e.g., "State vs. Martinez - Armed Robbery")
  - Case Number (auto-generated)
  - Case Type (Criminal, Civil, Corporate, etc.)
  - Jurisdiction
  - Max Rounds (1-5)

### 3. **Upload Documents**
- Click "Upload Document" for Side A (Plaintiff/Prosecution)
- Click "Upload Document" for Side B (Defendant/Defense)
- Supported formats: PDF, DOCX, TXT
- AI extracts text automatically

### 4. **Generate Initial Verdict (Round 0)**
- Once both sides have documents, click "Generate Initial Verdict"
- AI analyzes evidence and provides:
  - Summary
  - Current Leader (Side A / Side B / Undecided)
  - Confidence Score
  - Key Issues with reasoning
  - Final Decision

### 5. **Submit Arguments (Rounds 1-5)**
- Both sides submit arguments in each round
- After both sides submit, AI generates new verdict
- Verdict evolves based on arguments
- See real-time updates

### 6. **Finalize Case**
- After max rounds reached, click "Finalize Case"
- Case is locked permanently
- Final verdict is stored

---

## 🧪 Testing

### Backend Tests (87 passing)

```bash
cd backend
source venv/bin/activate
pytest -v

# Run specific test files
pytest tests/test_cases.py -v
pytest tests/test_arguments.py -v
pytest tests/test_verdicts.py -v

# With coverage
pytest --cov=app --cov-report=html
```

### Test Coverage Areas
- ✅ Authentication (JWT, phone login)
- ✅ Case CRUD operations
- ✅ Document upload & extraction
- ✅ Verdict generation
- ✅ Argument submission
- ✅ Multi-round flow
- ✅ Case finalization
- ✅ Edge cases & error handling

---

## 📊 Database Schema

### Core Models

**User**
- `id` (UUID, PK)
- `phone_hash` (unique, indexed)
- `full_name`, `email`
- `created_at`, `last_login`

**Case**
- `id` (UUID, PK)
- `case_number` (unique, auto: CAS-2025-001234)
- `title`, `case_type`, `jurisdiction`
- `status` (draft, ready, in_progress, finalized)
- `current_round` (0-5), `max_rounds`
- `created_by` (FK -> User)

**Document**
- `id` (UUID, PK)
- `case_id` (FK -> Case)
- `side` ('A' or 'B')
- `title`, `file_name`, `file_path`
- `full_text` (extracted by AI)
- `page_count`, `uploaded_at`

**Argument**
- `id` (UUID, PK)
- `case_id` (FK -> Case)
- `round` (1-5), `side` ('A' or 'B')
- `argument_text`
- `submitted_by` (FK -> User)
- `submitted_at`

**Verdict**
- `id` (UUID, PK)
- `case_id` (FK -> Case)
- `round` (0-5)
- `verdict_json` (JSONB with structured verdict)
- `model_used` (gpt-4o-mini)
- `tokens_used`, `created_at`

---

## 🎯 API Endpoints

### Authentication
- `POST /api/auth/login` - Login with phone number
- `GET /api/auth/me` - Get current user
- `POST /api/auth/logout` - Logout

### Cases
- `GET /api/cases` - List user's cases
- `POST /api/cases` - Create new case
- `GET /api/cases/{case_id}` - Get case details
- `DELETE /api/cases/{case_id}` - Delete case
- `POST /api/cases/{case_id}/finalize` - Finalize case

### Documents
- `POST /api/cases/{case_id}/documents` - Upload document
- `GET /api/cases/{case_id}/documents` - List documents
- `DELETE /api/cases/{case_id}/documents/{doc_id}` - Delete document

### Verdicts
- `POST /api/cases/{case_id}/verdict` - Generate initial verdict
- `GET /api/cases/{case_id}/verdicts` - Get all verdicts

### Arguments
- `POST /api/cases/{case_id}/arguments` - Submit argument
- `GET /api/cases/{case_id}/arguments` - Get all arguments

**Full API Documentation:** http://localhost:8000/docs

---

## 🎨 UI Screenshots

### Dashboard
- Case list with status badges
- Create new case button
- Quick access to recent cases

### Case Page (3-Column Layout)
- **Left:** Side A (Plaintiff) - Documents & Arguments
- **Center:** AI Judge - Verdict Display
- **Right:** Side B (Defendant) - Documents & Arguments

### Features
- Document upload modal
- Real-time argument submission
- Success/error message banners
- Round progress tracker
- Finalize case button when max rounds reached

---

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-your-api-key
ACCESS_TOKEN_EXPIRE_MINUTES=43200
ENVIRONMENT=development
DEBUG=True
```

**Frontend:**
- API Base URL: `http://localhost:8000/api`
- Configured in `src/services/api.js`

---

## 🚢 Deployment

### Docker Deployment (Coming Soon)

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

### Production Considerations
- Use proper PostgreSQL instance (not local)
- Store secrets in environment variables
- Enable CORS properly
- Use CDN for frontend static assets
- Implement rate limiting
- Add monitoring (Prometheus/Grafana)
- Set up logging (ELK stack)

---

## 💡 Key Design Decisions

### 1. **Orchestrator Pattern**
Business logic separated from API routes:
- `VerdictOrchestrator` - Verdict generation
- `ArgumentOrchestrator` - Argument submission & round management

### 2. **Multi-Round System**
- Round 0: Initial verdict (no arguments)
- Rounds 1-5: Argument-based verdicts
- Both sides must submit before new verdict generates
- Prevents exceeding max rounds

### 3. **Waiting State**
When one side submits, shows: "Waiting for Side B to submit..."
- Prevents confusion
- Clear user feedback
- No premature verdict generation

### 4. **Separate Success/Error Messages**
- Success messages use green banners (don't trigger error page)
- Error messages use red banners
- Dismissible with "×" button

---

## 🐛 Known Issues & Limitations

### Current Limitations
- Single-user mode (no collaboration)
- No real-time WebSocket updates
- Document size limited to 10MB
- No PDF export for final verdicts yet
- No email notifications

### Future Enhancements
- [ ] Real-time collaboration (multiple users per side)
- [ ] WebSocket for live updates
- [ ] PDF report generation
- [ ] Email notifications
- [ ] Evidence strength meter
- [ ] Bias detection in AI reasoning
- [ ] Legal precedent references
- [ ] Chat-based argument interface

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Commit changes: `git commit -m "Add amazing feature"`
6. Push to branch: `git push origin feature/amazing-feature`
7. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Authors

**Ayush** - Initial development & architecture

---

## 🙏 Acknowledgments

- OpenAI for GPT-4o-mini API
- FastAPI team for excellent documentation
- React & Tailwind CSS communities

---

## 📞 Support

For questions or issues:
- Open an issue on GitHub
- Contact: [Your email]

---

## 🎓 Use Cases

### Educational
- **Law Students**: Practice moot court arguments
- **Debate Teams**: Develop argumentation skills
- **Legal Writing**: Learn structured legal reasoning

### Professional
- **Legal Aid**: Quick case evaluation
- **Judges**: Pre-hearing analysis
- **Attorneys**: Case strength assessment

### Accessibility
- AI legal assistance for underserved communities
- Simplified legal process understanding
- Cost-effective case analysis

---

**Built with ❤️ for justice and innovation**
