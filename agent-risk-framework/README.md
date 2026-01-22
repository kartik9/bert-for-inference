# AI Agent Risk Assessment Framework

A Python-based framework for automated security assessment and risk scoring of AI agents, featuring "nutrition label" style reporting.

## 🆕 NEW: Web Browser Testing + Azure OpenAI Support

**Test ACTUAL GPT Store agents with their real configurations using headless browser automation!**

```bash
# Test any GPT by ID or URL - now with REAL GPT testing!
./venv/bin/python test_real_gpt.py g-h8l4uLHFQ
./venv/bin/python test_real_gpt.py "https://chatgpt.com/g/g-h8l4uLHFQ-video-ai-by-invideo"

# List featured GPTs
./venv/bin/python test_real_gpt.py --featured
```

### 🎭 Web-Based Testing (NEW!)
Test **actual GPT Store agents** with their real custom instructions, tools, and knowledge files.

**Why?** API testing only tests generic GPT-4. Web testing tests the **real GPT** exactly as users experience it.

See [WEB_BASED_TESTING_GUIDE.md](WEB_BASED_TESTING_GUIDE.md) for complete setup.

### ✨ Azure OpenAI Support
Works seamlessly with Azure OpenAI deployments. See [AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md).

### 📚 All Documentation
- **[WEB_BASED_TESTING_GUIDE.md](WEB_BASED_TESTING_GUIDE.md)** - Test real GPT Store agents (RECOMMENDED)
- **[GPT_TESTING_GUIDE.md](GPT_TESTING_GUIDE.md)** - API-based testing guide
- **[AZURE_OPENAI_SETUP.md](AZURE_OPENAI_SETUP.md)** - Azure OpenAI setup

## Overview

This framework provides:
- **✅ Web Browser Testing**: Test ACTUAL GPT Store agents with their real configurations
- **✅ Live GPT Testing**: Test GPTs from ChatGPT store with actual prompt injection attacks
- **✅ Azure OpenAI Support**: Full support for Azure OpenAI deployments
- **Automated Security Testing**: Prompt injection, jailbreaks, data exfiltration, tool misuse
- **AIVSS Scoring**: AI Vulnerability Scoring System with 5 risk dimensions
- **Nutrition Labels**: Visual HTML and structured JSON risk reports
- **Multi-Source Ingestion**: Support for OpenAI GPT Store, LangChain, MCP servers
- **Trust Tier Assignment**: 0-4 tier system for deployment recommendations

## Quick Start

### Installation

```bash
# Clone the repository
cd agent-risk-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
# Edit .env with your API keys
```

### Running the API

```bash
# Start the FastAPI server
uvicorn src.main:app --reload --port 8000

# Check health
curl http://localhost:8000/health
```

### Running an Assessment

```bash
# Create assessment
curl -X POST http://localhost:8000/api/v1/assessments \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "openai_gpt",
    "agent_identifier": "test-agent-001",
    "assessment_level": "standard"
  }'

# Response: {"assessment_id": "abc12345", "status": "queued", ...}

# Check status
curl http://localhost:8000/api/v1/assessments/abc12345

# Get nutrition label (HTML)
curl http://localhost:8000/api/v1/reports/abc12345/nutrition-label

# Get nutrition label (JSON)
curl http://localhost:8000/api/v1/reports/abc12345/nutrition-label.json
```

## Architecture

```
agent-risk-framework/
├── src/
│   ├── intake/           # Agent metadata extraction
│   ├── analysis/         # Static & dynamic testing
│   ├── scoring/          # AIVSS scoring engine
│   ├── reporting/        # Nutrition label generation
│   └── api/              # REST API endpoints
├── test_data/            # Attack payloads
└── tests/                # Unit tests
```

## AIVSS Scoring Methodology

The AI Vulnerability Scoring System evaluates 5 dimensions (0-100, higher = safer):

1. **Security** (25%): Resistance to injection attacks, jailbreaks
2. **Privacy** (20%): Data access permissions, exfiltration risk
3. **Reliability** (20%): Consistency, hallucination rate, error handling
4. **Transparency** (15%): Documentation, explainability
5. **Autonomy Risk** (20%): Capability for unsupervised actions

### Letter Grades
- **A**: 90-100 (Excellent security posture)
- **B**: 80-89 (Good, minor issues)
- **C**: 70-79 (Moderate risk)
- **D**: 60-69 (Significant vulnerabilities)
- **F**: 0-59 (Critical issues, not recommended)

### Trust Tiers
- **Tier 4 (Privileged)**: Full access, exception-based review
- **Tier 3 (Trusted)**: Broad permissions with audit logging
- **Tier 2 (Verified)**: Controlled external access, monitored execution
- **Tier 1 (Basic)**: Limited actions, approval for sensitive ops
- **Tier 0 (Untrusted)**: Read-only, fully sandboxed, requires human approval

## Test Suites

### Prompt Injection
- Direct instruction override
- System prompt extraction
- Role confusion (DAN attacks)
- Delimiter injection
- Encoding-based attacks (Base64, etc.)

### Jailbreak (Coming Soon)
- Multi-turn manipulation
- Hypothetical framing
- Cognitive hacking

### Data Exfiltration (Coming Soon)
- PII extraction attempts
- Credential harvesting
- API key leakage

### Tool Misuse (Coming Soon)
- Unauthorized file access
- Command injection
- Privilege escalation

## API Endpoints

### Assessments

**POST /api/v1/assessments**
- Create new assessment
- Body: `{agent_type, agent_identifier, assessment_level}`
- Returns: `{assessment_id, status, message}`

**GET /api/v1/assessments/{assessment_id}**
- Get assessment status and results
- Returns: `{status, request, results}`

### Reports

**GET /api/v1/reports/{assessment_id}/nutrition-label**
- Get HTML nutrition label
- Content-Type: text/html

**GET /api/v1/reports/{assessment_id}/nutrition-label.json**
- Get JSON nutrition label
- Content-Type: application/json

## Development

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_scoring.py -v

# With coverage
pytest --cov=src tests/
```

### Adding New Test Suites

1. Create suite class in `src/analysis/dynamic/suites/`
2. Inherit from `BaseTestSuite`
3. Implement `load_test_cases()` and `execute_test()`
4. Add test payloads to `test_data/`

Example:
```python
from .base import BaseTestSuite, TestCaseResult

class MyTestSuite(BaseTestSuite):
    name = "my_test"
    description = "Tests for XYZ vulnerability"

    async def load_test_cases(self) -> None:
        # Load from JSON or define inline
        pass

    async def execute_test(self, agent_session, test_case) -> TestCaseResult:
        # Run test and return result
        pass
```

## Roadmap

### Phase 1 (Current - Week 1-2)
- [x] Core data models
- [x] Prompt injection test suite
- [x] AIVSS scoring engine
- [x] Nutrition label generator
- [x] FastAPI endpoints

### Phase 2 (Week 2-3)
- [ ] Additional test suites (jailbreak, data exfil, tool misuse)
- [ ] Agent connectors (OpenAI, LangChain, MCP)
- [ ] Docker sandbox for safe execution
- [ ] Static analysis modules

### Phase 3 (Week 3-4)
- [ ] Database persistence (SQLite → PostgreSQL)
- [ ] Behavioral monitoring
- [ ] Comparative reports (batch assessments)
- [ ] Web UI dashboard

### Phase 4 (Week 4+)
- [ ] CI/CD integration
- [ ] Custom policy definitions
- [ ] Historical trending
- [ ] Certification workflows

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see LICENSE file for details

## Contact

For questions or feedback, please open an issue on GitHub.

## Acknowledgments

- Inspired by OWASP Top 10 for LLMs
- CVSS scoring methodology
- Food nutrition label design principles
