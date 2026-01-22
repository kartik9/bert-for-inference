# Quick Start Guide

## 1. Setup (5 minutes)

```bash
# Navigate to the project
cd agent-risk-framework

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Copy and edit environment file
cp .env.example .env
```

## 2. Start the Server

### Option A: Using the start script
```bash
./run_server.sh
```

### Option B: Manual start
```bash
source venv/bin/activate
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

## 3. Test the API

### Check Health
```bash
curl http://localhost:8000/health
```

### Create an Assessment
```bash
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "openai_gpt",
    "agent_identifier": "my-test-agent",
    "assessment_level": "standard"
  }'
```

You'll receive:
```json
{
  "assessment_id": "abc12345",
  "status": "queued",
  "message": "Assessment queued. Check status at /api/v1/assessments/abc12345"
}
```

### Check Assessment Status
```bash
curl http://localhost:8000/api/v1/assessments/abc12345
```

### Get Nutrition Label (HTML)
```bash
# Open in browser
open http://localhost:8000/api/v1/reports/abc12345/nutrition-label

# Or download
curl http://localhost:8000/api/v1/reports/abc12345/nutrition-label > label.html
```

### Get Nutrition Label (JSON)
```bash
curl http://localhost:8000/api/v1/reports/abc12345/nutrition-label.json
```

## 4. Run Automated API Tests

```bash
./venv/bin/python test_api.py
```

## 5. Run Unit Tests

```bash
./venv/bin/pytest tests/ -v
```

## API Documentation

Once the server is running, visit:
- **Interactive API docs**: http://localhost:8000/docs
- **Alternative docs**: http://localhost:8000/redoc

## What's Next?

See [README.md](README.md) for:
- Detailed architecture
- AIVSS scoring methodology
- Adding new test suites
- Development guidelines
- Roadmap

## Troubleshooting

**Port already in use?**
```bash
# Use a different port
uvicorn src.main:app --port 8001 --reload
```

**Module import errors?**
```bash
# Make sure you're in the venv
source venv/bin/activate
# Reinstall dependencies
pip install -r requirements.txt
```

**API not responding?**
```bash
# Check server logs for errors
# Make sure you're in the project root directory
```
