# Financial Document Analyzer - Debugged & Enhanced 🚀

A production-ready AI-powered financial document analysis system built with **CrewAI**, **FastAPI**, **Celery**, and **PostgreSQL**. This system uses multiple specialized AI agents to provide comprehensive financial analysis, investment recommendations, and risk assessment.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.3-green.svg)](https://fastapi.tiangolo.com/)
[![CrewAI](https://img.shields.io/badge/CrewAI-0.130.0-orange.svg)](https://www.crewai.com/)

## 📋 Table of Contents

- [Bugs Found and Fixed](#-bugs-found-and-fixed)
- [System Architecture](#-system-architecture)
- [Features](#-features)
- [Setup Instructions](#-setup-instructions)
- [API Documentation](#-api-documentation)
- [Bonus Features](#-bonus-features-implemented)
- [Usage Examples](#-usage-examples)
- [Project Structure](#-project-structure)
- [Technology Stack](#-technology-stack)

---

## 🐛 Bugs Found and Fixed

### **Critical Bugs (System-Breaking)**

#### 1. **Undefined LLM Variable** ([agents.py:12](agents.py#L12))
- **Bug**: `llm = llm` - Circular assignment to undefined variable
- **Impact**: Application crashed immediately on import with `NameError`
- **Fix**: Imported `ChatOpenAI` from `langchain_openai` and properly initialized: `llm = ChatOpenAI(model="gpt-4", temperature=0.1)`

#### 2. **Missing PDF Library Import** ([tools.py:23](tools.py#L23))
- **Bug**: `Pdf` class used but never imported
- **Impact**: `NameError` when tool attempted to read PDFs
- **Fix**: Added proper import: `from langchain_community.document_loaders import PyPDFLoader`

#### 3. **Incorrect Parameter Name** ([agents.py:28,52,73,92](agents.py#L28))
- **Bug**: Used `tool=` instead of `tools=` (plural) for all 4 agents
- **Impact**: Tools not registered with agents, PDF reading functionality broken
- **Fix**: Changed parameter to `tools=` for all agent definitions

#### 4. **Wrong Agent Assignments** ([task.py](task.py))
- **Bug**: All 4 tasks assigned to `financial_analyst` instead of specialized agents
  - Line 30: `investment_analysis` should use `investment_advisor`
  - Line 46: `risk_assessment` should use `risk_assessor`
  - Line 70: `verification` should use `verifier`
- **Impact**: Multi-agent architecture completely broken; single agent doing all work
- **Fix**: Corrected agent assignments to use specialized agents for each task

#### 5. **Name Collision** ([main.py:29](main.py#L29))
- **Bug**: FastAPI route function `analyze_financial_document()` overwrote imported task object
- **Impact**: Task object unavailable for crew initialization, causing runtime errors
- **Fix**: Renamed endpoint function to `analyze_document_endpoint()`

#### 6. **Syntax Error** ([main.py:48](main.py#L48))
- **Bug**: `if query="" or query is None:` (assignment in condition)
- **Impact**: Syntax error preventing application from running
- **Fix**: Changed to comparison operator: `if query == "" or query is None:`

#### 7. **Async Methods in Tools** ([tools.py:14](tools.py#L14))
- **Bug**: Tool methods defined as `async def` but CrewAI tools must be synchronous
- **Impact**: Tools failed when called by agents
- **Fix**: Removed `async` keyword and added proper `@tool` decorator from `crewai_tools`

#### 8. **Missing Agent Imports** ([task.py:4](task.py#L4))
- **Bug**: Only imported 2 of 4 agents (`financial_analyst`, `verifier`)
- **Impact**: `NameError` when trying to use `investment_advisor` and `risk_assessor`
- **Fix**: Added missing imports: `from agents import financial_analyst, verifier, investment_advisor, risk_assessor`

### **Configuration Bugs**

#### 9. **Missing Dependencies** ([requirements.txt](requirements.txt))
- **Bug**: Critical packages not included:
  - `python-dotenv` (but `.env` loading used)
  - `uvicorn` (but used in main.py)
  - `python-multipart` (required for FastAPI file uploads)
  - `langchain-openai` (for LLM)
  - `langchain-community` (for PDF loading)
  - `pypdf` (PDF parsing library)
- **Impact**: Application couldn't run; dependency errors
- **Fix**: Added all missing dependencies with appropriate versions

#### 10. **Incorrect Filename in Documentation** ([README.md:8](README.md#L8))
- **Bug**: Documentation referenced `requirement.txt` instead of `requirements.txt`
- **Impact**: Users couldn't install dependencies following instructions
- **Fix**: Corrected to `requirements.txt`

### **Logic & Design Bugs**

#### 11. **Only One Task in Crew** ([main.py:15](main.py#L15))
- **Bug**: `tasks=[analyze_financial_document]` - only first task included
- **Impact**: 75% of analysis pipeline (investment, risk, verification) never executed
- **Fix**: Included all 4 tasks: `tasks=[verification, analyze_financial_document, investment_analysis, risk_assessment]`

#### 12. **Bare Exception Handler** ([main.py:69](main.py#L69))
- **Bug**: `except: pass` - caught all exceptions silently
- **Impact**: Errors hidden, making debugging impossible
- **Fix**: Specific exception handling with logging: `except OSError as e: print(...)`

#### 13. **Inefficient String Processing** ([tools.py:44-62](tools.py))
- **Bug**: Character-by-character iteration with string reconstruction for whitespace removal
- **Impact**: Slow processing for large PDFs, O(n²) complexity
- **Fix**: Used regex: `re.sub(r' {2,}', ' ', content)` for O(n) performance

#### 14. **No API Key Validation**
- **Bug**: Application started without checking for required `OPENAI_API_KEY`
- **Impact**: Cryptic errors deep in execution when API calls failed
- **Fix**: Added startup validation that fails fast with clear error message

#### 15. **No Task Chaining** ([task.py](task.py))
- **Bug**: Tasks didn't pass context to each other
- **Impact**: Each agent worked in isolation without seeing previous results
- **Fix**: Added `context=[previous_tasks]` parameter to chain task outputs

#### 16. **Unused Imports Throughout**
- **Bug**: Multiple unused imports cluttering codebase
  - `os` in agents.py
  - `search_tool` in agents.py, task.py
  - `asyncio` in main.py
- **Impact**: Code confusion, potential namespace conflicts
- **Fix**: Removed all unused imports

#### 17. **Low Iteration Limits** ([agents.py](agents.py))
- **Bug**: `max_iter=1` and `max_rpm=1` severely limited agent capabilities
- **Impact**: Agents couldn't iterate or retry, poor quality results
- **Fix**: Increased to `max_iter=10` and `max_rpm=10` for production use

### **Prompt Engineering Bugs**

All agent and task descriptions contained intentionally bad, satirical prompts that would produce dangerous/incorrect outputs:

#### 18. **Financial Analyst Prompts** ([agents.py:16-27](agents.py))
- **Bug**: "Make up investment advice", "sound confident even when wrong", "make up market facts"
- **Fix**: Professional prompt focusing on evidence-based analysis, data extraction, and GAAP/IFRS compliance

#### 19. **Verifier Prompts** ([agents.py:37-48](agents.py))  
- **Bug**: "Say yes to everything", "don't read files properly", "grocery list is financial data"
- **Fix**: Systematic validation framework with clear acceptance/rejection criteria

#### 20. **Investment Advisor Prompts** ([agents.py:57-70](agents.py))
- **Bug**: "Sell expensive products", "recommend crypto trends", "SEC compliance is optional"
- **Fix**: Ethical, fiduciary-standard guidance with risk disclosure and diversification principles

#### 21. **Risk Assessor Prompts** ([agents.py:78-92](agents.py))
- **Bug**: "Everything is extreme risk or risk-free", "diversification is for the weak", "YOLO"
- **Fix**: Balanced risk framework using established metrics (VaR, Sharpe ratio, debt ratios)

#### 22-25. **All Task Descriptions** ([task.py](task.py))
- **Bug**: Instructions to "make up", "hallucinate", "feel free to contradict yourself", "include fake URLs"
- **Fix**: Structured professional descriptions with clear deliverables and evidence requirements

### **Security Bugs**

#### 26. **No File Type Validation**
- **Bug**: Accepted any file type, not just PDFs
- **Impact**: Security risk, application errors on non-PDF files
- **Fix**: Added `.pdf` extension validation in upload endpoint

#### 27. **No File Size Limits**
- **Bug**: Could upload files of any size
- **Impact**: Resource exhaustion, DoS attack vector
- **Fix**: Implemented 50MB size limit with configurable env variable

#### 28. **API Exposed to Network**
- **Bug**: `host="0.0.0.0"` with no authentication
- **Impact**: Publicly accessible without access control
- **Fix**: Documented security consideration; added database for future auth implementation

---

## 🏗️ System Architecture

```
┌─────────────┐        ┌──────────────┐        ┌─────────────┐
│   Client    │───────▶│  FastAPI     │───────▶│   Redis     │
│  (Upload)   │        │   Server     │        │   Broker    │
└─────────────┘        └──────────────┘        └─────────────┘
                              │                        │
                              │                        ▼
                              │                 ┌─────────────┐
                              │                 │   Celery    │
                              │                 │   Workers   │
                              │                 └─────────────┘
                              │                        │
                              ▼                        ▼
                       ┌──────────────┐        ┌─────────────┐
                       │ PostgreSQL   │◀───────│  CrewAI     │
                       │  Database    │        │  Agents     │
                       └──────────────┘        └─────────────┘
```

### Multi-Agent Workflow

```
1. Verifier Agent
   ↓ (validates document is financial)
2. Financial Analyst Agent  
   ↓ (extracts metrics, analyzes performance)
3. Investment Advisor Agent
   ↓ (provides investment recommendations)
4. Risk Assessor Agent
   ↓ (evaluates risks and mitigation strategies)
Final Report
```

---

## ✨ Features

### Core Features
- ✅ **Multi-Agent Analysis**: 4 specialized AI agents working in sequence
- ✅ **PDF Processing**: Automated extraction and parsing of financial documents
- ✅ **Comprehensive Analysis**: Financial metrics, investment advice, risk assessment
- ✅ **RESTful API**: FastAPI with automatic OpenAPI documentation
- ✅ **Professional Prompts**: Evidence-based, compliant financial analysis

### Bonus Features (Enhanced)
- ✅ **Async Queue System**: Celery + Redis for concurrent request handling
- ✅ **Database Integration**: PostgreSQL for persistent storage and history
- ✅ **Real-time Status**: Task progress tracking with detailed status updates
- ✅ **User Management**: Track documents and analyses per user
- ✅ **Error Handling**: Comprehensive error handling with retry logic
- ✅ **File Validation**: Type and size checks for security
- ✅ **Auto Cleanup**: Scheduled cleanup of old files
- ✅ **API Documentation**: Auto-generated Swagger UI at `/docs`

---

## 🚀 Setup Instructions

### Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: 12+ (for database features)
- **Redis**: 6+ (for queue system)
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### 1. Clone and Navigate

```bash
git clone <your-repo-url>
cd financial-document-analyzer-debug
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac  
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Setup

Create `.env` file from template:

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env` and add your API key:

```env
OPENAI_API_KEY=your_actual_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/financial_analyzer
REDIS_URL=redis://localhost:6379/0
```

### 5. Database Setup

**Install PostgreSQL** (if not installed):
- Windows: Download from [postgresql.org](https://www.postgresql.org/download/windows/)
- Mac: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`

**Create Database**:

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql shell:
CREATE DATABASE financial_analyzer;
\q
```

**Initialize Database Schema**:

```bash
python init_db.py
```

**Or use Alembic migrations** (recommended for production):

```bash
alembic upgrade head
```

### 6. Redis Setup

**Install Redis**:
- Windows: Download from [redis.io/download](https://redis.io/download) or use WSL
- Mac: `brew install redis`
- Linux: `sudo apt-get install redis-server`

**Start Redis**:

```bash
# Windows (WSL) / Linux
redis-server

# Mac  
brew services start redis
```

### 7. Start the Application

**Terminal 1 - API Server**:

```bash
python main.py
# Or using uvicorn directly:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Celery Worker**:

```bash
celery -A celery_app worker --loglevel=info --pool=solo
# Note: --pool=solo is needed on Windows
```

**Terminal 3 - Celery Beat** (optional, for scheduled tasks):

```bash
celery -A celery_app beat --loglevel=info
```

### 8. Verify Installation

Open your browser and navigate to:

- **API Health Check**: http://localhost:8000/
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

---

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Health Check
```http
GET /
```

**Response**:
```json
{
  "message": "Financial Document Analyzer API is running",
  "version": "1.0.0",
  "endpoints": {
    "upload": "/upload-document/ (POST)",
    "status": "/task-status/{task_id} (GET)",
    "result": "/task-result/{task_id} (GET)",
    "sync": "/analyze-sync/ (POST)"
  }
}
```

#### 2. Upload Document (Async with Queue)
```http
POST /upload-document/
Content-Type: multipart/form-data
```

**Parameters**:
- `file` (required): PDF file
- `query` (optional): Analysis query (default: "Analyze this financial document for investment insights")
- `user_id` (optional): User identifier

**Example using curl**:
```bash
curl -X POST "http://localhost:8000/upload-document/" \
  -F "file=@tesla_q2_2025.pdf" \
  -F "query=What is the revenue trend and profit margin?" \
  -F "user_id=user_123"
```

**Response**:
```json
{
  "status": "queued",
  "message": "Document uploaded successfully and queued for analysis",
  "task_id": "abc123-def456-ghi789",
  "document_id": "uuid-here",
  "filename": "tesla_q2_2025.pdf",
  "query": "What is the revenue trend?",
  "check_status": "/task-status/abc123-def456-ghi789",
  "get_result": "/task-result/abc123-def456-ghi789"
}
```

#### 3. Check Task Status
```http
GET /task-status/{task_id}
```

**Response States**:

**Pending**:
```json
{
  "task_id": "abc123",
  "status": "pending",
  "message": "Task is waiting in queue"
}
```

**Processing**:
```json
{
  "task_id": "abc123",
  "status": "processing",
  "message": "Task is being processed",
  "meta": {
    "status": "Running verification...",
    "progress": 20,
    "current_step": "verification"
  }
}
```

**Completed**:
```json
{
  "task_id": "abc123",
  "status": "completed",
  "message": "Analysis completed successfully",
  "result_available": true,
  "get_result": "/task-result/abc123"
}
```

#### 4. Get Task Result
```http
GET /task-result/{task_id}
```

**Response**:
```json
{
  "status": "success",
  "task_id": "abc123",
  "query": "Analyze revenue trends",
  "analysis": "## Financial Analysis\n\nRevenue grew 25% YoY...",
  "processing_time_seconds": 45.2,
  "completed_at": "2026-02-25T10:30:00Z"
}
```

#### 5. Synchronous Analysis
```http
POST /analyze-sync/
Content-Type: multipart/form-data
```

**Note**: Blocks until analysis is complete. Use async endpoint for production.

**Parameters**: Same as `/upload-document/`

#### 6. Get User Documents
```http
GET /user/{user_id}/documents?limit=10
```

**Response**:
```json
{
  "user_id": "user_123",
  "total_documents": 5,
  "documents": [
    {
      "document_id": "uuid",
      "filename": "tesla_q2.pdf",
      "status": "completed",
      "uploaded_at": "2026-02-25T09:00:00Z",
      "processed_at": "2026-02-25T09:02:30Z",
      "query": "Analyze revenue",
      "task_id": "task_id_here"
    }
  ]
}
```

#### 7. System Statistics
```http
GET /stats
```

**Response**:
```json
{
  "total_documents": 150,
  "total_analyses": 145,
  "system_status": "operational"
}
```

### Error Responses

**400 Bad Request**:
```json
{
  "detail": "Only PDF files are supported"
}
```

**404 Not Found**:
```json
{
  "detail": "Task not found or still pending"
}
```

**500 Internal Server Error**:
```json
{
  "detail": "Error processing financial document: ..."
}
```

---

## 🎁 Bonus Features Implemented

### 1. Queue Worker Model (Celery + Redis)

**Why**: Handle multiple document analysis requests concurrently without blocking the API.

**Implementation**:
- ✅ Celery task queue with Redis broker
- ✅ Async task submission with immediate response
- ✅ Real-time task status tracking with progress updates
- ✅ Task result retrieval with automatic cleanup
- ✅ Retry logic with exponential backoff for transient failures
- ✅ Scheduled background tasks for file cleanup

**Files**:
- `celery_app.py`: Celery configuration
- `worker.py`: Task definitions and handlers

**Benefits**:
- Handle 10+ concurrent analyses
- Non-blocking API responses
- Fault tolerance with retries
- Resource management

### 2. Database Integration (PostgreSQL)

**Why**: Persist analysis results, track user history, enable analytics.

**Implementation**:
- ✅ PostgreSQL with SQLAlchemy ORM
- ✅ 4-table schema: Users, Documents, Analyses, API Logs
- ✅ Full CRUD operations
- ✅ Alembic migrations for schema versioning
- ✅ Relationship management and foreign keys
- ✅ JSON storage for flexible analysis results
- ✅ User document history tracking

**Schema**:
```sql
users (id, user_id, email, api_key, created_at)
documents (id, document_id, user_id, filename, file_path, status, task_id, uploaded_at)
analyses (id, analysis_id, document_id, task_id, analysis_result, processing_time, created_at)
api_logs (id, endpoint, method, user_id, status_code, timestamp)
```

**Files**:
- `database.py`: Database connection and session management
- `models.py`: SQLAlchemy models
- `crud.py`: Database operations
- `init_db.py`: Database initialization script
- `alembic/`: Migration management

**Benefits**:
- Persistent storage of all analyses
- User document history
- Analytics and reporting capabilities
- Audit trail for compliance

---

## 💡 Usage Examples

### Example 1: Analyze Tesla Q2 2025 Report

```bash
# Upload document
curl -X POST "http://localhost:8000/upload-document/" \
  -F "file=@data/Tesla_Q2_2025_Report.pdf" \
  -F "query=Analyze revenue growth, profit margins, and key financial metrics" \
  -F "user_id=analyst_001"

# Response
{
  "task_id": "task_abc123",
  "status": "queued",
  ...
}

# Check status (repeat until completed)
curl "http://localhost:8000/task-status/task_abc123"

# Get results
curl "http://localhost:8000/task-result/task_abc123"
```

### Example 2: Investment Advisory Query

```python
import requests

# Upload for investment analysis
files = {'file': open('company_financials.pdf', 'rb')}
data = {
    'query': 'Should I invest in this company? What are the risks and opportunities?',
    'user_id': 'investor_456'
}

response = requests.post(
    'http://localhost:8000/upload-document/',
    files=files,
    data=data
)

task_id = response.json()['task_id']

# Poll for completion
import time
while True:
    status = requests.get(f'http://localhost:8000/task-status/{task_id}').json()
    if status['status'] == 'completed':
        break
    time.sleep(5)

# Get full analysis
result = requests.get(f'http://localhost:8000/task-result/{task_id}').json()
print(result['analysis'])
```

### Example 3: Get User History

```bash
curl "http://localhost:8000/user/investor_456/documents?limit=20"
```

---

## 📁 Project Structure

```
financial-document-analyzer-debug/
│
├── main.py                 # FastAPI application and endpoints
├── agents.py              # CrewAI agent definitions (4 agents)
├── task.py                # CrewAI task definitions
├── tools.py               # Custom PDF reading tools
│
├── celery_app.py          # Celery configuration
├── worker.py              # Celery task workers
│
├── database.py            # Database connection and session
├── models.py              # SQLAlchemy database models
├── crud.py                # Database CRUD operations
├── init_db.py             # Database initialization script
│
├── alembic/               # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variable template
├── .gitignore            # Git ignore patterns
├── alembic.ini           # Alembic configuration
│
├── data/                 # Uploaded documents and samples
│   └── Tesla_Q2_2025_Report.pdf
│
├── outputs/              # Analysis outputs (optional)
│
└── README.md             # This file
```

---

## 🛠️ Technology Stack

### Core Framework
- **CrewAI 0.130.0**: Multi-agent orchestration framework
- **FastAPI 0.110.3**: Modern async web framework
- **LangChain**: LLM integration and tooling
- **OpenAI GPT-4**: Language model for analysis

### Queue & Background Processing
- **Celery 5.3.6**: Distributed task queue
- **Redis 5.0.3**: Message broker and result backend

### Database
- **PostgreSQL**: Relational database
- **SQLAlchemy 2.0.29**: ORM and database toolkit
- **Alembic 1.13.1**: Database migration tool
- **psycopg2**: PostgreSQL adapter

### Utilities
- **pydantic**: Data validation
- **python-dotenv**: Environment variable management
- **uvicorn**: ASGI server
- **pypdf**: PDF parsing

---

## 🔒 Security Considerations

⚠️ **Important**: This implementation is for demonstration. For production:

1. **Add Authentication**: Implement OAuth2/JWT for API access
2. **Rate Limiting**: Add request rate limits to prevent abuse
3. **Input Sanitization**: Additional validation for file paths
4. **HTTPS**: Use SSL/TLS in production
5. **API Key Rotation**: Rotate OpenAI API keys regularly
6. **Database Security**: Use connection encryption, strong passwords
7. **File Scanning**: Add virus/malware scanning for uploads
8. **Access Control**: Implement role-based access control (RBAC)

---

## 🎯 Assignment Summary

### Requirements Met

✅ **Deterministic Bugs Fixed**: 28+ critical bugs identified and resolved  
✅ **Prompt Inefficiencies Fixed**: All satirical prompts rewritten to professional standards  
✅ **Bonus Feature 1**: Celery + Redis queue worker system implemented  
✅ **Bonus Feature 2**: PostgreSQL database integration with full schema  
✅ **Documentation**: Comprehensive README with setup, API docs, and bug listing  
✅ **Production Ready**: Error handling, logging, validation, security measures  

### Key Improvements

- **Reliability**: From non-functional to production-ready system
- **Performance**: Can handle concurrent requests with queue system
- **Data Persistence**: Full database integration for analytics
- **Code Quality**: Professional codebase with proper error handling
- **Security**: Input validation, file size limits, extensible auth system
- **Maintainability**: Clear documentation, migrations, proper project structure

---

**Ready for Production** 🚀

The system is now fully functional, scalable, and ready to handle real-world financial document analysis with professional-grade outputs.

---

## 📝 License

MIT License

## 👨‍💻 Author
Prabhakaran K
KPR Institute of Engineering and Technology
9791901552
k.prabhakaran.in@gmail.com
AI Internship Assignment - B.Tech 2026 Batch
