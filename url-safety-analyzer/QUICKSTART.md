# 🚀 Quick Start Guide

Get the URL Safety Analyzer running in under 5 minutes!

## Prerequisites

- Python 3.8 or higher
- OpenAI API key OR Anthropic API key
- Internet connection

## Step-by-Step Setup

### 1. Install Dependencies

```bash
cd url-safety-analyzer/backend
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API key
# Choose ONE of the following:
```

For **OpenAI (GPT-4)**:
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
```

For **Anthropic (Claude)**:
```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

### 3. Start the Application

**Option A: Automated Start (Linux/Mac)**
```bash
cd ..  # Back to url-safety-analyzer directory
./start.sh
```

**Option B: Manual Start**

Terminal 1 (Backend):
```bash
cd backend
python main.py
```

Terminal 2 (Frontend):
```bash
cd frontend
python server.py
```

### 4. Access the Application

Open your browser and go to:
```
http://localhost:3000
```

## 🎯 Try Your First Analysis

1. Enter a URL in the input field (e.g., `https://google.com`)
2. Make sure "Enable Deep Analysis" is checked
3. Click "Analyze URL"
4. Watch the real-time analysis unfold!

## 📊 What to Expect

The analysis will go through these phases:

1. **Technical Analysis** (0-30%)
   - DNS lookup
   - SSL certificate check
   - HTTP response analysis

2. **AI Planning** (30-40%)
   - Creates custom investigation plan

3. **Deep Investigation** (40-90%)
   - AI analyzes each aspect with reasoning
   - Real-time thinking stream

4. **Report Generation** (90-100%)
   - Final verdict
   - Risk score
   - Detailed findings with citations

## 💬 Follow-up Questions

After analysis completes, try asking:
- "What specific indicators make this URL suspicious?"
- "Can you explain the SSL certificate findings?"
- "What should I investigate further?"

## 🔧 Troubleshooting

**Backend won't start?**
```bash
# Check if port 8000 is available
lsof -i :8000

# Try a different port by editing backend/main.py
# Change the port number in the last line
```

**Frontend shows "Connection refused"?**
- Make sure the backend is running first
- Check that backend is on http://localhost:8000
- Look for errors in the backend terminal

**"AI agent not configured" error?**
- Make sure you added an API key to backend/.env
- Check that the .env file is in the backend directory
- Restart the backend server

**Analysis fails or times out?**
- Check your internet connection
- Some URLs may block automated requests
- SSL errors are normal for sites without certificates

## 🎓 Example Test Cases

### Safe URL
```
https://github.com
```
Expected: LOW risk, legitimate category

### URL with Suspicious Patterns
```
https://secure-login-verify-account.tk/signin
```
Expected: HIGH risk due to:
- Suspicious TLD (.tk)
- Multiple hyphens
- Security-related keywords

### IP Address URL
```
http://192.168.1.1
```
Expected: MEDIUM risk - IP addresses instead of domains

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Customize AI prompts in `backend/ai_agent.py`
- Add custom analysis logic in `backend/url_analyzer.py`

## ⚡ Pro Tips

1. **API Costs**: Each analysis makes multiple AI API calls. Monitor your usage!

2. **Performance**: Deep analysis takes 30-90 seconds depending on the AI model

3. **Best Results**: Use GPT-4 for most thorough analysis (Claude 3 Opus is also excellent)

4. **Safety**: Never visit suspicious URLs directly - let the tool analyze them

5. **Batch Analysis**: For multiple URLs, analyze them one at a time

## 🆘 Need Help?

- Check the [README.md](README.md) for full documentation
- Review backend logs for error details
- Check browser console for frontend issues
- Ensure your API key is valid and has credits

---

**Ready to analyze? Let's go! 🚀**
