# Trust & Safety Newsletter Automation

**AI-powered multi-agent system for automating threat intelligence gathering and newsletter generation**

Built with GPT-5 Responses API, fully self-hosted except for LLM calls.

---

## Overview

This system uses 6 specialized AI agents to autonomously research, analyze, and generate weekly newsletters about advertising fraud and security threats affecting platforms like Microsoft Ads.

### Key Features

- ✅ **Fully Autonomous**: No human review needed (optional)
- ✅ **Self-Hosted**: Run entirely on your infrastructure
- ✅ **GPT-5 Powered**: Uses OpenAI's latest Responses API
- ✅ **Configurable Search**: DuckDuckGo (free) or Bing Search API (paid)
- ✅ **Multi-Agent System**: 6 specialized agents with ReAct pattern
- ✅ **Explainable**: Full reasoning traces for all decisions
- ✅ **Scalable**: Parallel research with multiple agents

---

## Architecture

### Multi-Agent System

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│              (Coordinates workflow strategy)                 │
└───────────┬──────────┬──────────┬──────────┬─────────────────┘
            │          │          │          │
        ┌───▼───┐  ┌──▼───┐  ┌──▼───┐  ┌──▼───┐  ┌────▼────┐
        │Research│  │Rele- │  │Analy-│  │Summa-│  │Quality  │
        │ Agent  │  │vance │  │sis   │  │ry    │  │ Agent   │
        │(3-5x)  │  │Agent │  │Agent │  │Agent │  │         │
        └────────┘  └──────┘  └──────┘  └──────┘  └─────────┘
             │          │          │         │          │
             └──────────┴──────────┴─────────┴──────────┘
                               │
                     ┌─────────▼──────────┐
                     │   Self-Hosted      │
                     │  PostgreSQL +      │
                     │   Weaviate         │
                     └────────────────────┘
```

### Agent Descriptions

1. **Orchestrator Agent** 🎯
   - Strategic coordinator
   - Spawns and manages other agents
   - Makes decisions about research topics
   - Ensures workflow completion

2. **Research Agent** 🔍 (runs in parallel, 3-5 instances)
   - Web search (DuckDuckGo/Bing)
   - RSS feed monitoring
   - Article content fetching
   - Citation chaining

3. **Relevance Agent** 📊
   - Multi-dimensional scoring (relevance, novelty, impact, actionability)
   - LLM-powered evaluation (not rule-based)
   - Priority classification (HIGH/MEDIUM/LOW)

4. **Analysis Agent** 🧠
   - Deep threat intelligence analysis
   - Technical detail extraction (IOCs, TTPs)
   - Pattern recognition
   - Detection gap analysis

5. **Summary Agent** ✍️
   - Executive-friendly content generation
   - Consistent style and formatting
   - Headline creation
   - Source attribution

6. **Quality Agent** ✅
   - Fact-checking against sources
   - Hallucination detection
   - Style guide compliance
   - Approval/revision workflow

---

## Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose (for databases)
- Azure OpenAI endpoint and API key (or standard OpenAI API key)
- Optional: Bing Search API key (if not using DuckDuckGo)

### Installation

1. **Clone and install dependencies:**
```bash
cd bert-for-inference
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Required `.env` variables:

**Option A: Azure OpenAI (Recommended for enterprise):**
```bash
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/openai/v1/
AZURE_OPENAI_API_KEY=your_azure_api_key
POSTGRES_PASSWORD=your_secure_password
```

**Option B: Standard OpenAI:**
```bash
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
POSTGRES_PASSWORD=your_secure_password
```

Optional:
```bash
BING_SEARCH_API_KEY=your_bing_key  # If using Bing instead of DuckDuckGo
```

3. **Start databases:**
```bash
# Start PostgreSQL and Weaviate
docker compose up -d

# Wait for databases to be healthy
docker compose ps

# Initialize Weaviate schema
python ts_newsletter/database/weaviate_schema.py
```

4. **Configure LLM provider:**

Edit `ts_newsletter/config.yaml`:

**For Azure OpenAI (default):**
```yaml
llm:
  provider: "azure_openai"
  azure_endpoint_env: "AZURE_OPENAI_ENDPOINT"
  azure_api_key_env: "AZURE_OPENAI_API_KEY"
  azure_api_version: "2024-02-15-preview"
  deployment_name: "gpt-5"  # Your Azure deployment name
```

**For Standard OpenAI:**
```yaml
llm:
  provider: "openai"
  api_key_env: "OPENAI_API_KEY"
  model: "gpt-5"
```

5. **Configure search provider:**

Edit `ts_newsletter/config.yaml`:

**For DuckDuckGo (free, default):**
```yaml
search:
  provider: "duckduckgo"
```

**For Bing Search (paid):**
```yaml
search:
  provider: "bing"
```

Then set `BING_SEARCH_API_KEY` in `.env`

---

## Usage

### Basic Usage

Generate newsletter with default settings:
```bash
python run_newsletter.py
```

Output will be saved to `./output/newsletters/newsletter_YYYY-MM-DD.md`

### Advanced Usage

```bash
# Custom output directory
python run_newsletter.py --output ./my_newsletters

# Verbose mode (includes agent reasoning traces)
python run_newsletter.py --verbose

# Custom config file
TS_NEWSLETTER_CONFIG=./custom_config.yaml python run_newsletter.py

# All options
python run_newsletter.py --output ./output --verbose --config ./custom.yaml
```

### Configuration

Edit `ts_newsletter/config.yaml` to customize:

**LLM Settings:**
```yaml
llm:
  provider: "azure_openai"  # or "openai" for standard OpenAI
  deployment_name: "gpt-5"  # For Azure: your deployment name
                            # For OpenAI: model name (gpt-5, gpt-5.2-instant, etc.)

  # Use different models/deployments per agent
  agent_models:
    orchestrator: "gpt-5-thinking"   # Best reasoning
    research: "gpt-5"                # Standard
    relevance: "gpt-5"               # Fast scoring
    analysis: "gpt-5-thinking"       # Deep analysis
    summary: "gpt-5"                 # Content gen
    quality: "gpt-5-thinking"        # Critical review
```

**Search Configuration:**
```yaml
search:
  provider: "duckduckgo"  # or "bing"

  duckduckgo:
    max_results: 20
    time_range: "w"  # w=week, m=month

  bing:
    max_results: 20
    freshness: "Week"
```

**Newsletter Parameters:**
```yaml
newsletter:
  target_articles: 8
  min_articles: 5
  max_articles: 12
  date_range_days: 7

  scoring:
    min_relevance: 7.0
    min_novelty: 5.0
    min_impact: 6.0
    min_actionability: 5.0
```

**Research Topics:**
```yaml
search_queries:
  core_topics:
    - "advertising fraud"
    - "malvertising"
    - "ad cloaking"
    - "deepfake advertising scams"

  platforms:
    - "Google Ads fraud"
    - "Meta advertising scams"
```

---

## Output

### Newsletter Format

Generated newsletters follow this structure:

```markdown
# What's Happening in Trust & Safety
### Week Ending December 17, 2025

---

### 🚨 **Parked Domains Now Primary Malvertising Vector**
**Published:** December 16, 2025 (Infoblox Threat Intelligence)

**What Happened:**
Over 90% of parked domain visitors are now redirected to scams and malware...

**Key Details:**
- Attackers use device fingerprinting to evade detection
- Example domains: scotaibank[.]com targets mobile users
- Traffic sold through multiple affiliate networks

**Why It Matters:**
This represents a sophisticated evasion technique that Aurora cannot currently detect.
Recommend implementing residential IP testing infrastructure.

**Source:** [Infoblox Threat Intelligence](https://blogs.infoblox.com/...)

---

[Additional articles...]

---

## Emerging Patterns to Watch

1. Geographic cloaking sophistication increasing
2. AI-as-a-service lowering fraud barriers
3. Cross-platform campaign coordination

---

*Generated by: Ads Trust & Safety Intelligence Team*
```

### Output Files

- `newsletter_YYYY-MM-DD.md` - Final newsletter markdown
- `summary_YYYY-MM-DD.json` - Workflow metrics and metadata
- `traces_YYYY-MM-DD.json` - Agent reasoning traces (if `--verbose`)

---

## Database Management

### PostgreSQL

**Connect to database:**
```bash
docker compose exec postgres psql -U ts_user -d ts_newsletter
```

**View high-priority articles:**
```sql
SELECT * FROM v_high_priority_articles LIMIT 10;
```

**Check recent newsletters:**
```sql
SELECT * FROM v_newsletter_summary ORDER BY week_ending DESC LIMIT 5;
```

**Agent performance metrics:**
```sql
SELECT * FROM v_agent_performance;
```

### Weaviate

**Access Weaviate console:**
```
http://localhost:8080/v1/schema
```

**Query similar articles (Python):**
```python
import weaviate

client = weaviate.connect_to_local()
articles = client.collections.get("Article")

result = articles.query.near_text(
    query="deepfake advertising fraud",
    limit=10
)
```

### Optional: pgAdmin

Start with tools profile:
```bash
docker compose --profile tools up -d
```

Access pgAdmin at http://localhost:5050
- Email: admin@localhost
- Password: (from .env or "admin")

---

## Scheduling

### Cron (Linux/Mac)

Run every Monday at 9 AM:
```bash
crontab -e
```

Add:
```
0 9 * * 1 cd /path/to/bert-for-inference && /path/to/python run_newsletter.py
```

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Weekly, Monday, 9:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\path\to\bert-for-inference\run_newsletter.py`
7. Start in: `C:\path\to\bert-for-inference`

### Systemd Service (Linux)

Create `/etc/systemd/system/ts-newsletter.service`:
```ini
[Unit]
Description=Trust & Safety Newsletter Generation
After=network.target docker.service

[Service]
Type=oneshot
User=your-user
WorkingDirectory=/path/to/bert-for-inference
Environment="PATH=/path/to/venv/bin:/usr/bin"
ExecStart=/path/to/venv/bin/python run_newsletter.py

[Install]
WantedBy=multi-user.target
```

Create timer `/etc/systemd/system/ts-newsletter.timer`:
```ini
[Unit]
Description=Weekly Newsletter Generation

[Timer]
OnCalendar=Mon *-*-* 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable ts-newsletter.timer
sudo systemctl start ts-newsletter.timer
```

---

## Cost Estimates

### Infrastructure (Self-Hosted)

**Option 1: Docker on existing server**
- Cost: $0 (uses existing resources)

**Option 2: Azure VM (8 vCPU, 32GB RAM)**
- Cost: ~$200-300/month
- Storage: ~$10/month for 100GB

### API Costs (Monthly)

**OpenAI GPT-5:**
- Est. 500K tokens/week for all agents
- GPT-5: $2.50 per 1M input tokens, $10 per 1M output tokens
- Cost: ~$50-150/month

**Search API:**
- DuckDuckGo: $0 (free)
- Bing Search API: ~$20-40/month (optional)

**Total: $50-500/month** depending on infrastructure choice

---

## Troubleshooting

### Database Connection Issues

```bash
# Check if databases are running
docker compose ps

# View logs
docker compose logs postgres
docker compose logs weaviate

# Restart databases
docker compose restart postgres weaviate
```

### OpenAI API Errors

**Rate Limits:**
- Reduce `parallel_research_agents` in config.yaml
- Add delays between agent spawns

**Invalid API Key:**
- Check `.env` file has correct `OPENAI_API_KEY`
- Ensure key starts with `sk-proj-`

### Search API Issues

**DuckDuckGo Rate Limiting:**
- Increase `rate_limit_delay` in config.yaml
- Switch to Bing Search API

**Bing API Quota Exceeded:**
- Check your Bing API subscription limits
- Fallback to DuckDuckGo temporarily

---

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

```bash
# Format code
black ts_newsletter/

# Lint
flake8 ts_newsletter/

# Type checking
mypy ts_newsletter/
```

### Adding New Search Queries

Edit `ts_newsletter/config.yaml`:
```yaml
search_queries:
  core_topics:
    - "your new query here"
```

### Adding New RSS Feeds

```yaml
rss_feeds:
  security_blogs:
    - name: "Your Blog"
      url: "https://example.com/feed/"
      priority: "high"
```

---

## Architecture Details

### Agent Communication

Agents communicate via tool calls:

```python
# Orchestrator spawns Research Agent
orchestrator.execute_tool(
    "spawn_research_agent",
    {
        "agent_id": "research-1",
        "task": "Find deepfake advertising scams"
    }
)

# Research Agent returns collected articles
# Orchestrator passes to Relevance Agent
orchestrator.execute_tool(
    "score_articles",
    {"articles": json.dumps(collected)}
)
```

### ReAct Pattern

All agents use Reasoning + Acting:

```
Thought: I need to search for malvertising articles
Action: web_search("malvertising 2025")
Observation: Found 15 results from security blogs
Thought: Results look relevant, let me fetch full content
Action: fetch_article("https://...")
Observation: Article contains technical details
Thought: This is high-quality, store it
Action: store_article(...)
Decision: Collected 1 article, continue searching
```

---

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

## Support

For issues or questions:
- GitHub Issues: [Repository URL]
- Internal: [Contact Information]

---

**Built by:** Aurora Project Team
**Last Updated:** December 2025
