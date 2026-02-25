# Quick Start Guide 🚀

## Minimum Setup (Testing Without Queue/DB)

If you just want to test the core functionality without setting up PostgreSQL and Redis:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set OpenAI API Key
Create `.env` file:
```env
OPENAI_API_KEY=your_key_here
```

### 3. RunSync Endpoint
```bash
python main.py
```

### 4. Test
```bash
curl -X POST "http://localhost:8000/analyze-sync/" \
  -F "file=@data/sample.pdf" \
  -F "query=Analyze this financial document"
```

**Note**: This uses synchronous processing. The app will work but without queue or database features.

---

## Full Setup (Production with Queue & Database)

### Prerequisites Installation

#### PostgreSQL (Windows)
1. Download from https://www.postgresql.org/download/windows/
2. Run installer, remember the password
3. Open pgAdmin or Command Prompt:
```bash
psql -U postgres
CREATE DATABASE financial_analyzer;
\q
```

#### Redis (Windows)
Option 1 - WSL:
```bash
wsl
sudo apt-get update
sudo apt-get install redis-server
redis-server
```

Option 2 - Windows Native:
1. Download from https://github.com/microsoftarchive/redis/releases
2. Extract and run redis-server.exe

### Setup Steps

1. **Install Python packages**
```bash
pip install -r requirements.txt
```

2. **Configure environment**
```bash
copy .env.example .env
# Edit .env with your OpenAI key
```

3. **Initialize database**
```bash
python init_db.py
```

4. **Start Redis** (in separate terminal)
```bash
redis-server
```

5. **Start Celery Worker** (in separate terminal)
```bash
celery -A celery_app worker --loglevel=info --pool=solo
```

6. **Start API Server**
```bash
python main.py
```

7. **Test**
Visit http://localhost:8000/docs

---

## Testing the Full System

### Upload Document (Async)
```bash
curl -X POST "http://localhost:8000/upload-document/" \
  -F "file=@data/sample.pdf" \
  -F "query=Analyze revenue and profitability" \
  -F "user_id=test_user"
```

Returns:
```json
{
  "task_id": "abc123...",
  "status": "queued",
  ...
}
```

### Check Status
```bash
curl "http://localhost:8000/task-status/abc123..."
```

### Get Result
```bash
curl "http://localhost:8000/task-result/abc123..."
```

---

## Troubleshooting

### "Database connection failed"
- Check PostgreSQL is running: `pg_isready`
- Verify DATABASE_URL in .env
- Try: `psql -U postgres -d financial_analyzer`

### "Cannot connect to Redis"
- Check Redis is running: `redis-cli ping` (should return PONG)
- Verify REDIS_URL in .env

### "NameError: name 'llm' is not defined"
- This means you're running the old buggy code
- Make sure all files are updated with fixes

### "OPENAI_API_KEY not set"
- Create .env file with your OpenAI API key
- Restart the application

### Celery worker not starting
- On Windows, use: `celery -A celery_app worker --pool=solo --loglevel=info`
- Check Redis is running first

---

## What Was Fixed

✅ **28+ Critical Bugs Fixed**
- LLM initialization
- PDF loading
- Agent/task assignments
- Syntax errors
- Missing dependencies

✅ **All Prompts Rewritten**
- From satirical to professional
- Evidence-based analysis
- No hallucinations

✅ **Bonus Features Added**
- Celery + Redis queue system
- PostgreSQL database
- User tracking
- Progress monitoring

See full list in [README.md](README.md#-bugs-found-and-fixed)

---

## Next Steps

1. ✅ Get it running locally
2. ✅ Test with sample PDF
3. ✅ Verify all agents execute
4. ✅ Check database records
5. 🚀 Deploy to production (add auth, HTTPS, monitoring)

---

## Support

- Interactive Docs: http://localhost:8000/docs
- Full README: [README.md](README.md)
- Check logs in terminal for detailed errors
