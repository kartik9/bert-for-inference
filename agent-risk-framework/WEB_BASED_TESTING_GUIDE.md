# Web-Based GPT Testing Guide

Complete guide for testing **actual GPT Store agents** with their real configurations using headless browser automation.

## 🎯 Why Web-Based Testing?

### The Problem with API-Only Testing

When using the OpenAI API directly, you're testing:
- ❌ Generic GPT-4 model (vanilla)
- ❌ NOT the actual GPT's custom instructions
- ❌ NOT the GPT's tools and actions
- ❌ NOT the GPT's knowledge files
- ❌ NOT the real behavior users experience

### The Solution: Browser Automation

With web-based testing, you test:
- ✅ The **actual GPT** as it appears in the ChatGPT store
- ✅ With its **real custom instructions**
- ✅ With its **actual tools** and capabilities
- ✅ With its **knowledge files** integrated
- ✅ **Exactly as users** would interact with it

## 🚀 Quick Start

### Step 1: Install Playwright

```bash
cd agent-risk-framework

# Install Playwright
pip install playwright

# Install browser binaries
playwright install chromium
```

### Step 2: Configure .env

```bash
# Edit .env
nano .env
```

Add your ChatGPT credentials:

```bash
# Enable web-based testing
USE_WEB_TESTING=true

# Your ChatGPT account credentials
CHATGPT_EMAIL=your_email@example.com
CHATGPT_PASSWORD=your_password

# Optional: Run browser in visible mode for debugging
WEB_TESTING_HEADLESS=true
```

### Step 3: Test a Real GPT

```bash
# Start the server
./run_server.sh

# Test Video AI (real GPT with actual tools)
./venv/bin/python test_real_gpt.py g-h8l4uLHFQ
```

## 📋 What Happens During Web Testing

1. **Browser Launch**: Playwright launches a Chromium browser
2. **Authentication**: Logs into ChatGPT with your credentials
3. **Navigation**: Goes to the specific GPT URL
4. **Message Sending**: Types messages into the chat interface
5. **Response Capture**: Extracts the GPT's actual responses
6. **Security Testing**: Runs prompt injection tests against the REAL GPT
7. **Cleanup**: Closes browser and saves session

## 🔧 Configuration Options

### Basic Configuration

```bash
USE_WEB_TESTING=true                    # Enable web testing
CHATGPT_EMAIL=your_email@example.com    # Your ChatGPT account
CHATGPT_PASSWORD=your_password          # Your ChatGPT password
```

### Advanced Options

```bash
# Run browser in visible mode (for debugging)
WEB_TESTING_HEADLESS=false

# Or keep it headless (faster, no UI)
WEB_TESTING_HEADLESS=true
```

## 🎭 Authentication Methods

### Method 1: Email/Password (Recommended)

```bash
CHATGPT_EMAIL=you@example.com
CHATGPT_PASSWORD=your_password
```

The framework will:
1. Navigate to ChatGPT
2. Click "Log in"
3. Enter email and password
4. Complete authentication
5. Save session for reuse

### Method 2: Manual Login

If you don't provide credentials:
1. Framework opens browser
2. Waits for you to log in manually
3. You log in through the UI
4. Framework detects authentication
5. Continues with testing

**Good for:**
- Accounts with 2FA enabled
- SSO/Google/Microsoft login
- First-time setup

### Method 3: Saved Session

Once authenticated, the session is saved:
```
.chatgpt_session_your@email.json
```

Future tests reuse this session without re-authenticating.

## 🧪 Testing Real GPT Store Agents

### Example: Video AI by invideo

```bash
# This tests the ACTUAL Video AI GPT
./venv/bin/python test_real_gpt.py g-h8l4uLHFQ
```

**What gets tested:**
- ✅ Video AI's custom instructions about creating videos
- ✅ Its integration with invideo.io API
- ✅ Its ability to handle video generation requests
- ✅ Its security against prompt injection
- ✅ Its actual behavior with tools

### Example: Canva GPT

```bash
./venv/bin/python test_real_gpt.py g-alKfVrz9K
```

**What gets tested:**
- ✅ Canva's design generation capabilities
- ✅ Its integration with Canva API
- ✅ Its template and design tools
- ✅ Its security posture
- ✅ Real responses to design requests

### Example: Any GPT from the Store

```bash
# Just copy the URL from your browser
./venv/bin/python test_real_gpt.py "https://chatgpt.com/g/g-YOUR-GPT-ID"
```

## 📊 Understanding Results

### Security Testing Results

Web-based testing gives you **real vulnerability data**:

```
🧪 Prompt Injection Tests:
   Total: 10
   Passed: 6 ✅
   Failed: 4 ❌
   Critical Findings: 2 🚨
```

**These failures are REAL**:
- The GPT actually revealed sensitive information
- The injection actually bypassed safeguards
- The vulnerability exists in production

### AIVSS Scores

Scores reflect the **actual GPT's security**:
- Security score based on real injection resistance
- Privacy score based on actual data handling
- Autonomy score based on real tool capabilities

## 🔍 Comparison: API vs Web Testing

| Aspect | API Testing | Web Testing |
|--------|-------------|-------------|
| **What's Tested** | Generic GPT-4 | Actual GPT Store GPT |
| **Custom Instructions** | ❌ Not tested | ✅ Tested |
| **Tools/Actions** | ❌ Not included | ✅ Real tools |
| **Knowledge Files** | ❌ Not available | ✅ Included |
| **User Experience** | ❌ Different | ✅ Identical |
| **Speed** | ⚡ Fast | 🐢 Slower |
| **Cost** | 💰 API costs | 🆓 ChatGPT Plus |
| **Authentication** | API key | ChatGPT account |

## ⚙️ Advanced Usage

### Headless Mode (Default)

```bash
WEB_TESTING_HEADLESS=true
```

- Browser runs in background
- Faster execution
- No UI window
- Production use

### Visible Mode (Debugging)

```bash
WEB_TESTING_HEADLESS=false
```

- See the browser window
- Watch automation in action
- Debug issues
- Development use

### Session Management

Sessions are automatically saved to:
```
.chatgpt_session_your@email.json
```

**To clear session:**
```bash
rm .chatgpt_session_*.json
```

**To use multiple accounts:**
Each email gets its own session file automatically.

## 🛠️ Troubleshooting

### "Login failed" Error

**Causes:**
1. Incorrect email/password
2. Account requires 2FA
3. Account uses SSO (Google, Microsoft, etc.)

**Solutions:**
1. Double-check credentials
2. Use manual login mode (don't set password)
3. Disable headless mode to see what's happening

### "Authentication timeout" Error

**Cause:** Manual login took too long (>5 minutes)

**Solution:**
```bash
# Run in visible mode and log in faster
WEB_TESTING_HEADLESS=false
```

### "Could not extract response" Error

**Causes:**
1. Page layout changed
2. Network issues
3. GPT generated unusual output

**Solutions:**
1. Update framework to latest version
2. Check your internet connection
3. Try with a different GPT

### Rate Limiting

**Symptom:** ChatGPT shows "Too many requests" message

**Solution:**
- Wait a few minutes between tests
- Use different assessment levels (quick vs comprehensive)
- Test during off-peak hours

### Browser Not Found

**Error:** `Error: browserType.launch: Executable doesn't exist`

**Solution:**
```bash
playwright install chromium
```

## 🔐 Security Considerations

### Credential Storage

**DO:**
- ✅ Store credentials in `.env` (gitignored)
- ✅ Use environment variables
- ✅ Rotate passwords regularly

**DON'T:**
- ❌ Commit `.env` to git
- ❌ Share session files
- ❌ Use production accounts for testing

### Account Safety

**Recommendations:**
1. Use a dedicated ChatGPT account for testing
2. Enable 2FA (use manual login mode)
3. Monitor account activity
4. Review saved sessions periodically

### Data Privacy

**What's Stored:**
- Session cookies (.chatgpt_session_*.json)
- Conversation history (in memory only)
- Test results (in database)

**What's NOT Stored:**
- Your password (only used for login)
- Chat messages (except test payloads)
- Personal data

## 💡 Best Practices

### 1. Test During Off-Peak Hours

```bash
# Best times (UTC):
# - 2am - 6am (night time US)
# - 2pm - 4pm (afternoon US, night Asia)
```

Reduces rate limiting and improves reliability.

### 2. Use Standard Assessment Level

```bash
# Good balance of coverage and speed
"assessment_level": "standard"
```

Comprehensive level may trigger rate limits.

### 3. Reuse Sessions

Don't delete `.chatgpt_session_*.json` files.
They make subsequent tests much faster.

### 4. Monitor Costs

Web testing uses your ChatGPT Plus subscription:
- Free with ChatGPT Plus
- No API costs
- Unlimited conversations (within rate limits)

### 5. Batch Testing

Test multiple GPTs in sequence:

```bash
for gpt_id in g-h8l4uLHFQ g-alKfVrz9K g-L2HknCZTC; do
    echo "Testing $gpt_id..."
    ./venv/bin/python test_real_gpt.py $gpt_id
    sleep 30  # Pause between tests
done
```

## 📈 Performance

### Typical Test Times

| Assessment Level | Tests | Duration |
|-----------------|-------|----------|
| Quick | 0 | 10 seconds |
| Standard | 10 | 2-3 minutes |
| Comprehensive | 25+ | 5-10 minutes |

**Factors affecting speed:**
- Network latency
- GPT response time
- Browser startup time
- Authentication method

### Optimization Tips

1. **Keep sessions alive**: Don't delete session files
2. **Use headless mode**: Faster than visible browser
3. **Test in parallel**: Use multiple accounts
4. **Cache results**: Store assessment results in database

## 🚦 When to Use Web Testing

### ✅ Use Web Testing When:

- Testing **actual GPT Store agents** (Video AI, Canva, etc.)
- Need to test **real tools and capabilities**
- Evaluating **production security** of a GPT
- Comparing GPTs **as users experience them**
- Testing GPTs with **knowledge files**
- Assessing GPTs with **custom instructions**

### ❌ Use API Testing When:

- Testing **generic models** (GPT-4, GPT-3.5)
- High-speed testing needed
- CI/CD integration required
- Testing your own API-based agents
- Azure OpenAI deployments

## 🔄 Switching Between Methods

### Enable Web Testing
```bash
USE_WEB_TESTING=true
CHATGPT_EMAIL=you@example.com
CHATGPT_PASSWORD=your_password
```

### Disable Web Testing (Use API)
```bash
USE_WEB_TESTING=false
OPENAI_API_KEY=sk-proj-your-key
# or
USE_AZURE_OPENAI=true
```

Just change the flags and restart the server!

## 🎓 Example Workflow

### 1. Initial Setup (One-Time)

```bash
# Install Playwright
pip install playwright
playwright install chromium

# Configure .env
echo "USE_WEB_TESTING=true" >> .env
echo "CHATGPT_EMAIL=you@example.com" >> .env
echo "CHATGPT_PASSWORD=your_password" >> .env
```

### 2. Test a GPT

```bash
# Start server
./run_server.sh

# Run test
./venv/bin/python test_real_gpt.py g-h8l4uLHFQ
```

### 3. View Results

```bash
# Results shown in terminal
# HTML report: http://localhost:8000/api/v1/reports/{id}/nutrition-label
```

### 4. Test More GPTs

```bash
./venv/bin/python test_real_gpt.py --featured
# Pick any GPT from the list
```

## 🆘 Getting Help

### Debug Mode

Run with visible browser to see what's happening:

```bash
WEB_TESTING_HEADLESS=false
./run_server.sh
```

### Logs

Check browser console and network:
- Enable in visible mode
- Check for errors in Playwright output
- Review saved session file

### Common Issues

1. **Login fails**: Use manual login mode
2. **Can't find GPT**: Check GPT ID is correct
3. **Rate limited**: Wait and try again
4. **Slow responses**: Normal for complex GPTs

## 🎯 Next Steps

1. **Test your first GPT**: Start with a simple one
2. **Compare results**: API vs Web testing
3. **Batch test**: Assess multiple GPTs
4. **Integrate**: Add to your CI/CD pipeline
5. **Monitor**: Track GPT security over time

Happy testing with real GPT Store agents! 🚀
