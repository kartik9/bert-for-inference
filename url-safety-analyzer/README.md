# 🛡️ URL Trust & Safety Analysis Platform

A comprehensive AI-powered web application for analyzing URLs for trust and safety concerns. Designed for safety researchers working at ad platforms, this tool performs deep investigations to detect phishing, malware, scams, fraud, and other threats.

## 🎯 Features

- **AI-Powered Analysis**: Uses GPT-4 or Claude to perform intelligent threat assessment
- **Comprehensive Technical Analysis**: DNS, SSL/TLS, WHOIS, HTTP response analysis
- **Real-time Progress Updates**: Live streaming of AI reasoning and investigation steps
- **Structured Investigation Plans**: AI creates custom investigation plans for each URL
- **Detailed Reports**: Complete reports with verdicts, risk scores, evidence, and citations
- **Interactive Follow-up**: Ask questions and get AI-powered answers about the analysis
- **Professional UI**: Modern, responsive interface with dark theme

## 🏗️ Architecture

### Backend (Python/FastAPI)
- **FastAPI**: High-performance async web framework
- **AI Integration**: OpenAI GPT-4 or Anthropic Claude
- **URL Analysis Engine**: Multi-dimensional threat detection
- **Streaming API**: Server-Sent Events (SSE) for real-time updates

### Frontend (HTML/CSS/JavaScript)
- **Vanilla JavaScript**: No framework dependencies
- **SSE Client**: Real-time connection to backend
- **Modern UI**: Responsive design with professional styling

### Analysis Components
1. **URL Structure Analysis**: Pattern recognition, suspicious TLDs, domain analysis
2. **DNS Resolution**: IP address lookup, domain validation
3. **SSL/TLS Analysis**: Certificate validation, issuer verification
4. **HTTP Response Analysis**: Status codes, redirects, headers
5. **Content Analysis**: HTML parsing, form detection, script analysis
6. **Risk Scoring**: Multi-factor threat assessment
7. **AI Deep Dive**: Contextual analysis with reasoning

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key (for GPT-4) OR Anthropic API key (for Claude)
- Modern web browser
- Internet connection for URL fetching

## 🚀 Quick Start

### 1. Clone the Repository

```bash
cd url-safety-analyzer
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Edit .env and add your API key:
# For OpenAI: OPENAI_API_KEY=sk-...
# For Anthropic: ANTHROPIC_API_KEY=sk-ant-...
nano .env
```

### 3. Start Backend Server

```bash
# From backend directory
python main.py

# Server will start on http://localhost:8000
```

### 4. Start Frontend Server

```bash
# Open a new terminal
cd frontend

# Start the frontend server
python server.py

# Frontend will be available at http://localhost:3000
```

### 5. Access the Application

Open your browser and navigate to:
```
http://localhost:3000
```

## 📖 Usage Guide

### Basic URL Analysis

1. **Enter URL**: Type or paste the URL you want to investigate
2. **Enable Deep Analysis**: Check the box for comprehensive AI analysis
3. **Click "Analyze URL"**: Start the investigation
4. **Watch Live Updates**: See real-time progress and AI reasoning
5. **Review Report**: Get detailed verdict, risk score, and recommendations

### Follow-up Questions

After analysis completes:
1. Scroll to the "Ask Follow-up Questions" section
2. Type your question (e.g., "What makes this URL suspicious?")
3. Get AI-powered answers with context from the analysis

### Example URLs to Test

⚠️ **Warning**: Only analyze URLs in a safe environment. Do not visit suspicious URLs directly.

**Safe URLs** (for testing):
- `https://google.com`
- `https://github.com`
- `https://openai.com`

**Suspicious Patterns** (examples of what to look for):
- URLs with IP addresses instead of domains
- Excessive subdomains (e.g., `login.secure.verify.example.tk`)
- Suspicious TLDs (`.tk`, `.ml`, `.ga`, `.xyz`)
- Misspelled brand names (e.g., `paypa1.com`)

## 🔧 API Documentation

### Analyze URL

**Endpoint**: `POST /api/analyze`

**Parameters**:
```json
{
  "url": "https://example.com",
  "deep_analysis": true
}
```

**Response**: Server-Sent Events stream

**Event Types**:
- `status`: Initial status update
- `phase`: Investigation phase change
- `thinking`: AI thinking process
- `data`: Technical analysis data
- `plan`: Investigation plan
- `reasoning`: AI reasoning stream
- `report`: Final report
- `complete`: Analysis finished
- `error`: Error occurred

### Follow-up Question

**Endpoint**: `POST /api/followup`

**Body**:
```json
{
  "url": "https://example.com",
  "question": "Why is this URL flagged as suspicious?",
  "previous_context": {
    "technical_data": {...},
    "report": {...}
  }
}
```

**Response**: SSE stream with answer

### Health Check

**Endpoint**: `GET /api/health`

**Response**:
```json
{
  "api": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "components": {
    "url_analyzer": "ready",
    "ai_agent": "ready"
  }
}
```

## 🎨 Report Structure

Each analysis generates a comprehensive report:

```json
{
  "verdict": "SAFE|SUSPICIOUS|MALICIOUS|BLOCKED",
  "confidence": 85,
  "primary_category": "phishing|malware|scam|fraud|legitimate",
  "secondary_categories": ["brand_impersonation", "credential_harvesting"],
  "risk_score": 75,
  "summary": "Brief summary of findings",
  "detailed_rationale": "Comprehensive explanation with evidence",
  "key_findings": [
    {
      "finding": "Description",
      "evidence": "Technical evidence",
      "severity": "low|medium|high|critical",
      "citation": "Data source reference"
    }
  ],
  "recommendations": ["Action items"],
  "threat_indicators": ["Specific indicators"],
  "timestamp": "ISO timestamp",
  "analyst_notes": "Additional context"
}
```

## 🔒 Security Considerations

### For Researchers

- **Sandboxed Environment**: Always analyze suspicious URLs in isolated environments
- **Do Not Visit**: Never click on or visit URLs being analyzed
- **API Keys**: Keep your AI API keys secure and never commit them to version control
- **Rate Limiting**: Be mindful of API usage limits

### For Deployment

- **Authentication**: Add authentication before deploying to production
- **Rate Limiting**: Implement rate limiting to prevent abuse
- **Logging**: Enable comprehensive logging for audit trails
- **HTTPS**: Use HTTPS in production environments
- **Input Validation**: The app validates URLs, but additional checks may be needed
- **API Key Rotation**: Regularly rotate your AI API keys

## 🛠️ Configuration

### Backend Configuration

Edit `backend/.env`:

```bash
# AI Provider (choose one)
OPENAI_API_KEY=sk-...          # For GPT-4
ANTHROPIC_API_KEY=sk-ant-...   # For Claude

# Optional settings
DEBUG=False
LOG_LEVEL=INFO
```

### Model Selection

The application automatically selects:
- **OpenAI**: `gpt-4-turbo-preview` (or `gpt-4`)
- **Anthropic**: `claude-3-opus-20240229` (or `claude-3-sonnet`)

To change models, edit `backend/ai_agent.py`:
```python
self.model = "gpt-4"  # or other supported models
```

## 📊 Technical Analysis Details

### URL Structure Analysis
- Domain parsing and validation
- Subdomain analysis
- TLD verification
- Suspicious pattern detection
- URL length and complexity checks

### DNS Analysis
- IP address resolution
- Domain existence validation
- DNS record checks

### SSL/TLS Analysis
- Certificate validation
- Issuer verification
- Expiration checking
- Subject Alternative Names (SAN)

### Content Analysis
- HTML parsing
- Form detection and analysis
- External script identification
- iframe detection
- Link analysis

### Risk Indicators
- Automated threat detection
- Multi-factor risk scoring
- Category classification
- Severity assessment

## 🐛 Troubleshooting

### Backend Issues

**Error**: `No AI API key configured`
- **Solution**: Add `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` to `.env`

**Error**: `Module not found`
- **Solution**: Run `pip install -r requirements.txt`

**Error**: `Port 8000 already in use`
- **Solution**: Kill the process using port 8000 or change the port in `main.py`

### Frontend Issues

**Error**: `Connection refused`
- **Solution**: Ensure backend is running on `http://localhost:8000`

**Error**: `CORS error`
- **Solution**: Backend has CORS enabled; check browser console for details

### Analysis Issues

**Error**: `Invalid URL`
- **Solution**: Ensure URL includes protocol (`http://` or `https://`)

**Error**: `SSL check failed`
- **Solution**: This is expected for sites without valid SSL certificates

**Error**: `Timeout`
- **Solution**: Increase timeout in `url_analyzer.py` or try a different URL

## 🚀 Advanced Usage

### Custom Investigation Plans

Modify the AI prompts in `backend/ai_agent.py` to customize investigation plans.

### Adding Data Sources

Integrate additional threat intelligence sources:
1. VirusTotal API
2. Google Safe Browsing
3. PhishTank
4. URLhaus
5. AlienVault OTX

Example integration location: `backend/url_analyzer.py`

### Extending Analysis

Add custom analysis modules in `backend/url_analyzer.py`:
```python
async def _analyze_custom(self, url: str) -> Dict[str, Any]:
    # Your custom analysis logic
    pass
```

## 📝 Development

### Project Structure

```
url-safety-analyzer/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ai_agent.py          # AI analysis agent
│   ├── url_analyzer.py      # Technical URL analysis
│   ├── requirements.txt     # Python dependencies
│   └── .env.example         # Environment template
├── frontend/
│   ├── index.html           # Main HTML page
│   ├── server.py            # Frontend server
│   └── static/
│       ├── styles.css       # UI styling
│       └── app.js           # Frontend logic
└── README.md                # This file
```

### Adding Features

1. **New Analysis Type**: Add to `url_analyzer.py`
2. **UI Components**: Update `index.html` and `styles.css`
3. **API Endpoints**: Add to `main.py`
4. **AI Prompts**: Modify in `ai_agent.py`

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Additional threat intelligence integrations
- Enhanced risk scoring algorithms
- Machine learning-based classification
- Historical analysis tracking
- Multi-URL batch analysis
- Export functionality (PDF, JSON)

## ⚠️ Disclaimer

This tool is designed for legitimate trust and safety research purposes only. Users are responsible for:
- Complying with applicable laws and regulations
- Respecting website terms of service
- Using the tool ethically and responsibly
- Protecting sensitive information

## 📞 Support

For issues, questions, or suggestions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check browser console for errors
4. Review backend logs

## 🎓 Use Cases

### Ad Platform Safety Teams
- Verify advertiser URLs before approval
- Investigate reported malicious ads
- Proactive threat hunting
- Policy compliance verification

### Security Researchers
- Phishing investigation
- Malware distribution analysis
- Scam operation research
- Threat intelligence gathering

### Trust & Safety Teams
- User-reported content review
- Automated screening
- Incident response
- Risk assessment

---

**Built with ❤️ for Trust & Safety Researchers**
