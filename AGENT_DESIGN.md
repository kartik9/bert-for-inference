# Trust & Safety Newsletter Automation - AI Agent Design
**Version:** 1.0
**Date:** December 17, 2025
**Architecture:** Multi-Agent System with LLM-powered reasoning

---

## System Overview

A **multi-agent orchestration system** where specialized AI agents collaborate to automate threat intelligence gathering, analysis, and newsletter generation. Each agent uses LLMs (Claude/GPT-4) as reasoning engines with tool-use capabilities.

### Core Principles
- **Agent autonomy**: Each agent makes decisions using LLM reasoning, not rule-based logic
- **Tool augmentation**: Agents use tools (web search, scraping, databases) via function calling
- **Iterative refinement**: Agents can critique and improve their own outputs
- **Collaborative intelligence**: Agents share context and build on each other's work
- **Explainability**: All decisions logged with reasoning traces

---

## Multi-Agent Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR AGENT                        │
│  (Coordinates workflow, manages state, makes strategic      │
│   decisions about what to research and when)                │
└──────────────────┬──────────────────────────────────────────┘
                   │
        ┌──────────┼──────────┬──────────┬──────────┐
        │          │          │          │          │
        ▼          ▼          ▼          ▼          ▼
   ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
   │Research│ │Relevance│ │Analysis│ │Summary │ │Quality │
   │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │ │ Agent  │
   └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
        │          │          │          │          │
        └──────────┴──────────┴──────────┴──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   SHARED MEMORY    │
                    │  (Vector DB + SQL) │
                    └────────────────────┘
```

---

## Agent Specifications

### 1. **Orchestrator Agent** 🎯
**Role:** Strategic coordinator and workflow manager

**Responsibilities:**
- Decide what topics/threats to research this week based on trends
- Allocate research tasks to Research Agents
- Determine when enough articles have been collected
- Coordinate handoffs between agents
- Make strategic decisions (e.g., "focus more on deepfake threats this week")
- Manage overall quality and coherence of final output

**Tools:**
- `query_vector_db()` - Check historical coverage and gaps
- `get_previous_newsletters()` - Understand past patterns
- `check_internal_incidents()` - See if Aurora detected new threats
- `create_research_tasks()` - Spawn Research Agent instances
- `evaluate_coverage()` - Assess if current collection is comprehensive

**LLM Prompt Pattern:**
```
You are a strategic intelligence coordinator for Microsoft Ads Trust & Safety.

Your role is to:
1. Analyze what threats/topics need coverage this week
2. Review recent internal incidents and industry trends
3. Decide what research to prioritize
4. Coordinate specialist agents to gather and analyze intelligence
5. Ensure balanced coverage across fraud types

Current date: {date}
Last newsletter covered: {previous_topics}
Recent Aurora detections: {internal_threats}

Decision: What should we research this week? Use your tools to gather
context, then create specific research tasks.
```

**Reasoning Loop:**
- Uses **ReAct pattern**: Thought → Action → Observation → Thought...
- Can spawn multiple research threads in parallel
- Adjusts strategy based on preliminary findings

---

### 2. **Research Agent** 🔍
**Role:** Autonomous information gatherer (multiple instances run in parallel)

**Responsibilities:**
- Execute specific research tasks (e.g., "find articles about parked domain fraud")
- Search multiple sources intelligently
- Follow citation chains (if article cites research, fetch that too)
- Deduplicate across sources
- Extract metadata (publication date, source authority, author credentials)
- Store findings in shared memory

**Tools:**
- `web_search(query, sources, date_range)` - Multi-source search
- `fetch_url(url)` - Retrieve full article content
- `check_rss_feeds(feed_list)` - Monitor RSS sources
- `extract_citations(article)` - Find referenced research
- `store_article(metadata, content)` - Save to database
- `semantic_search(embedding)` - Check if similar article already collected

**LLM Prompt Pattern:**
```
You are an expert threat intelligence researcher specializing in advertising fraud.

Task: {specific_research_task}
Examples: "Find recent articles about cloaking techniques" or
          "Search for deepfake advertising scams"

Available sources: {source_list}
Date range: Last 7 days

Your approach:
1. Break down the task into search queries
2. Search multiple sources systematically
3. Evaluate each result for relevance before fetching full content
4. Follow citation chains for high-quality sources
5. Store all relevant findings with metadata

Be thorough but efficient. Explain your search strategy before executing.
```

**Advanced Capabilities:**
- **Query reformulation**: If initial search fails, rephrase using synonyms
- **Source routing**: Knows which sources are best for which topics
- **Citation chaining**: Automatically fetches referenced research papers
- **Deduplication**: Uses embeddings to detect duplicate coverage

---

### 3. **Relevance Agent** 🎯
**Role:** Intelligent filter and prioritizer

**Responsibilities:**
- Evaluate each article for relevance to Microsoft Ads Trust & Safety
- Score articles on multiple dimensions (novelty, impact, actionability)
- Identify false positives (generic cybersecurity news, vendor marketing)
- Flag high-priority items requiring immediate attention
- Cluster related articles covering same incident

**Tools:**
- `get_article(article_id)` - Retrieve full content
- `get_historical_context(topic)` - Check past coverage
- `check_microsoft_relevance(article)` - Query internal knowledge base
- `calculate_threat_score(article)` - Use threat taxonomy
- `update_article_score(article_id, scores)` - Store assessment

**LLM Prompt Pattern:**
```
You are an expert in advertising platform security and fraud detection.

Article: {article_content}
Source: {source_name}
Published: {date}

Evaluate this article on:

1. **Relevance to Microsoft Ads** (0-10)
   - Does it discuss threats affecting display/search/video ads?
   - Is it specific to ad fraud or generic cybersecurity?
   - Does it mention platforms like Google Ads, Meta, or programmatic ecosystem?

2. **Novelty** (0-10)
   - Is this a new technique/threat or rehash of known issues?
   - Check historical context: {past_coverage}

3. **Impact** (0-10)
   - Scale of threat (individual scams vs. systemic vulnerabilities)
   - Financial or user safety implications
   - Affects major platforms or niche cases?

4. **Actionability** (0-10)
   - Can Microsoft Ads team take concrete action?
   - Contains technical details for implementation?
   - Or just awareness/monitoring?

Provide scores with detailed reasoning. Flag if this needs immediate escalation.
```

**Multi-dimensional Scoring:**
```json
{
  "article_id": "abc123",
  "scores": {
    "relevance": 9,
    "novelty": 8,
    "impact": 10,
    "actionability": 7,
    "overall_priority": "HIGH"
  },
  "reasoning": "Novel cloaking technique affecting parked domains...",
  "flags": ["immediate_attention", "technical_detail"],
  "related_articles": ["xyz789"],
  "recommended_action": "Review Aurora's parked domain detection"
}
```

---

### 4. **Analysis Agent** 🧠
**Role:** Deep threat intelligence analyst

**Responsibilities:**
- Perform deep analysis on high-priority articles
- Extract technical details (attack vectors, indicators of compromise)
- Identify patterns across multiple articles
- Connect to known threat frameworks (MITRE ATT&CK, fraud taxonomies)
- Generate insights beyond surface-level reporting
- Compare with internal Aurora detection capabilities

**Tools:**
- `extract_technical_details(article)` - Parse IOCs, TTPs
- `query_threat_database(indicators)` - Check known threats
- `find_related_incidents(article)` - Cross-reference
- `compare_detection_capabilities(threat, aurora_data)` - Gap analysis
- `generate_threat_briefing(article)` - Create detailed analysis

**LLM Prompt Pattern:**
```
You are a senior threat intelligence analyst with expertise in ad fraud.

Article: {article_content}
Priority Score: {priority_score}

Perform deep analysis:

1. **Threat Taxonomy**
   - Type: Malvertising / Cloaking / Bot Traffic / Fake Engagement / Other
   - Attack Vector: How does it work technically?
   - Evasion Techniques: How does it avoid detection?

2. **Technical Indicators**
   - Domains, IPs, patterns mentioned
   - Code snippets or behavioral signatures
   - Attribution (threat actor, geography, motivation)

3. **Pattern Analysis**
   - Related incidents: {fetch related articles}
   - Is this part of larger campaign?
   - Evolution from previous techniques?

4. **Microsoft Ads Implications**
   - Aurora detection capability: {aurora_context}
   - Gaps in current defenses?
   - Recommended detection logic?

5. **Actionable Intelligence**
   - What should the team investigate?
   - What detection rules should be added?
   - What policies might need updating?

Generate a threat briefing suitable for technical and leadership audiences.
```

**Output Example:**
```markdown
## Threat Briefing: Parked Domain Malvertising (Dec 2025)

**Threat Type:** Geographic Cloaking + Affiliate Network Obfuscation
**Severity:** CRITICAL
**Affected Platforms:** Google Ads (confirmed), likely cross-platform

### Technical Details
- Attack Vector: Typosquatting domains + device fingerprinting
- Evasion: Shows clean content to VPN/datacenter IPs, malicious to residential
- Attribution: Multiple affiliate networks, Chinese fraud operators suspected

### Detection Gaps
Aurora currently scans from datacenter IPs, would miss this threat.
Recommend: Residential proxy testing infrastructure.

### Recommended Actions
1. [IMMEDIATE] Test Aurora against known parked domains from residential IPs
2. [SHORT-TERM] Implement geographic diversity in ad scanning
3. [MEDIUM-TERM] Partner with TAG for parked domain threat intelligence
```

---

### 5. **Summary Agent** ✍️
**Role:** Newsletter content generator

**Responsibilities:**
- Generate concise, executive-friendly summaries
- Maintain consistent tone and style
- Create attention-grabbing headlines
- Structure multi-article narratives
- Add proper citations and source links
- Format for newsletter template

**Tools:**
- `get_articles_by_priority(threshold)` - Fetch top articles
- `get_threat_briefings(article_ids)` - Retrieve analysis
- `get_style_guide()` - Newsletter formatting rules
- `generate_summary(article, briefing, style)` - Create draft
- `format_newsletter_section(summaries)` - Apply template

**LLM Prompt Pattern:**
```
You are an expert technical writer for Microsoft's Trust & Safety team.

Input:
- Article: {article_content}
- Threat Briefing: {analysis_output}
- Priority: {priority_level}

Generate newsletter summary following this style:

**Format:**
### [Emoji] **[Attention-grabbing headline]**
**Published:** [Date] ([Source])

**What Happened:**
[2-3 sentence overview - lead with impact, then mechanism]

**Key Details:**
- [Bullet point: specific technical detail]
- [Bullet point: scale/scope with numbers]
- [Bullet point: novel element or evolution]
- [Bullet point: attribution if known]

**Why It Matters:**
[2-3 sentences on implications for Microsoft Ads, connection to Aurora
capabilities, or strategic importance. Executive-friendly language.]

**Source:** [Link to original with title]

**Style Requirements:**
- Professional but accessible (executive-friendly)
- Lead with "what" and "why it matters"
- Include specific numbers/metrics when available
- Avoid jargon without context
- Active voice, present tense for ongoing threats
- Flag actionable items clearly

Generate the summary now.
```

**Quality Checks:**
- Ensure all claims are backed by article content
- Verify links are correct
- Check for consistent emoji/priority markers
- Validate word count (target: 150-200 words per item)

---

### 6. **Quality Agent** ✅
**Role:** Critic and quality assurance

**Responsibilities:**
- Review all summaries for accuracy
- Check for hallucinations or unsupported claims
- Verify source citations
- Assess overall newsletter balance and coherence
- Identify gaps in coverage
- Request refinements from other agents

**Tools:**
- `verify_claim(claim, article)` - Cross-check facts
- `check_citation(link)` - Validate URLs
- `assess_balance(newsletter)` - Coverage analysis
- `request_revision(agent, item, feedback)` - Send back for improvement
- `finalize_newsletter(content)` - Approve for output

**LLM Prompt Pattern:**
```
You are a senior editor ensuring quality and accuracy.

Newsletter Draft: {newsletter_content}
Source Articles: {article_references}

Quality Review Checklist:

1. **Factual Accuracy**
   - Are all claims supported by source articles?
   - Any hallucinated details or speculation?
   - Numbers/dates correct?

2. **Source Quality**
   - All links functional and properly attributed?
   - Mix of authoritative sources?
   - Any questionable/low-credibility sources?

3. **Coverage Balance**
   - Mix of threat types (fraud, malvertising, deepfakes, etc.)?
   - Geographic diversity?
   - Both tactical (specific incidents) and strategic (trends)?

4. **Clarity & Coherence**
   - Summaries clear and self-contained?
   - Consistent terminology?
   - Executive-friendly language?

5. **Actionability**
   - At least 30% of items have clear Microsoft implications?
   - Recommended actions specific and feasible?

For each issue found, provide specific feedback and request revision
from the appropriate agent. Approve only when quality bar is met.
```

**Iterative Refinement:**
- Can send items back to Summary Agent for rewriting
- Can request additional research if gaps identified
- Can ask Analysis Agent for deeper technical details
- Final approval gates the output

---

## Workflow Orchestration

### Weekly Execution Flow

```
MONDAY 9 AM:
├─ Orchestrator Agent activates
├─ Reviews previous week's newsletter
├─ Checks Aurora incident reports
├─ Identifies trending topics from vector DB
└─ Creates research plan

MONDAY 9:30 AM - 12 PM:
├─ Spawns 5-10 Research Agent instances in parallel
│  ├─ Agent 1: Search for "malvertising" (last 7 days)
│  ├─ Agent 2: Search for "ad fraud" (last 7 days)
│  ├─ Agent 3: Monitor security blog RSS feeds
│  ├─ Agent 4: Search for "cloaking detection"
│  └─ Agent 5: Check academic papers on arXiv
├─ Each agent stores findings in shared memory
└─ Orchestrator monitors progress

MONDAY 12 PM - 2 PM:
├─ Relevance Agent processes all collected articles
├─ Scores and prioritizes each article
├─ Flags top 15-20 candidates
└─ Clusters related articles

MONDAY 2 PM - 4 PM:
├─ Analysis Agent performs deep analysis on top articles
├─ Generates threat briefings
├─ Identifies patterns and gaps
└─ Creates actionable recommendations

MONDAY 4 PM - 5 PM:
├─ Summary Agent generates newsletter content
├─ Creates 5-8 summary items
├─ Formats according to style guide
└─ Adds sources and context

MONDAY 5 PM - 5:30 PM:
├─ Quality Agent reviews full newsletter
├─ Checks accuracy, balance, clarity
├─ Requests revisions if needed
├─ Iterates until quality bar met
└─ Outputs final draft

MONDAY 5:30 PM:
└─ Final draft saved for human review (Tuesday)
```

---

## Memory & State Management

### Vector Database (Weaviate or Pinecone)
**Purpose:** Semantic search and deduplication

**Schema:**
```python
{
  "article_id": "uuid",
  "title": "string",
  "content": "string",  # Full article text
  "embedding": "vector[1536]",  # OpenAI ada-002 or similar
  "source": "string",
  "url": "string",
  "published_date": "datetime",
  "collected_date": "datetime",
  "tags": ["malvertising", "cloaking"],
  "priority_score": "float",
  "included_in_newsletter": "boolean",
  "newsletter_date": "datetime"
}
```

**Queries:**
- Find similar articles (deduplication)
- Semantic search for related incidents
- Identify coverage gaps
- Track topic trends over time

### SQL Database (PostgreSQL)
**Purpose:** Structured metadata and workflow state

**Tables:**
```sql
-- Articles collected
CREATE TABLE articles (
  id UUID PRIMARY KEY,
  url TEXT UNIQUE,
  title TEXT,
  source TEXT,
  published_date TIMESTAMP,
  collected_date TIMESTAMP,
  content TEXT,
  embedding_id UUID,  -- Reference to vector DB
  relevance_score JSONB,  -- All scoring dimensions
  analysis JSONB,  -- Threat briefing
  newsletter_summary TEXT,
  included_in_newsletter BOOLEAN,
  newsletter_date DATE
);

-- Research tasks
CREATE TABLE research_tasks (
  id UUID PRIMARY KEY,
  created_by TEXT,  -- Orchestrator
  task_description TEXT,
  query_terms JSONB,
  status TEXT,  -- pending, in_progress, completed
  assigned_agent TEXT,
  results JSONB,  -- Article IDs found
  created_at TIMESTAMP,
  completed_at TIMESTAMP
);

-- Agent execution logs
CREATE TABLE agent_logs (
  id UUID PRIMARY KEY,
  agent_type TEXT,
  agent_instance TEXT,
  action TEXT,
  reasoning TEXT,  -- LLM's chain of thought
  tools_used JSONB,
  outcome TEXT,
  timestamp TIMESTAMP
);

-- Newsletter history
CREATE TABLE newsletters (
  id UUID PRIMARY KEY,
  week_ending DATE,
  status TEXT,  -- draft, approved, published
  content TEXT,
  article_ids UUID[],
  quality_score JSONB,
  created_at TIMESTAMP,
  approved_at TIMESTAMP
);
```

---

## Agent Communication Protocol

### Message Format (JSON)
```json
{
  "from": "orchestrator_agent",
  "to": "research_agent_1",
  "message_type": "TASK_ASSIGNMENT",
  "content": {
    "task_id": "task_123",
    "task_description": "Find articles about deepfake advertising fraud",
    "parameters": {
      "date_range": "2025-12-10 to 2025-12-17",
      "sources": ["krebs", "unit42", "infoblox"],
      "max_articles": 20
    },
    "priority": "high"
  },
  "timestamp": "2025-12-17T09:30:00Z"
}
```

### Agent Response Format
```json
{
  "from": "research_agent_1",
  "to": "orchestrator_agent",
  "message_type": "TASK_COMPLETE",
  "content": {
    "task_id": "task_123",
    "status": "completed",
    "results": {
      "articles_found": 8,
      "article_ids": ["art_1", "art_2", "..."],
      "search_queries_used": [
        "deepfake advertising fraud 2025",
        "AI-generated scam ads",
        "synthetic media advertising"
      ],
      "sources_checked": ["krebs", "unit42", "infoblox"],
      "reasoning": "Used progressive query refinement..."
    },
    "execution_time_seconds": 45
  },
  "timestamp": "2025-12-17T09:45:00Z"
}
```

---

## Technical Implementation Stack

### Agent Framework
**Option 1: LangGraph** (Recommended)
- Built for multi-agent workflows with cycles
- State management built-in
- Easy to visualize and debug agent interactions
- Native LangChain integration

**Option 2: AutoGen (Microsoft Research)**
- Sophisticated multi-agent collaboration
- Built-in conversation patterns
- Good for research/exploration phases

**Option 3: Custom with Claude/GPT API**
- Maximum control
- Simpler for MVP
- Use function calling for tool use

### LLM Selection
- **Primary:** Claude Sonnet 4.5 (reasoning, analysis, summarization)
- **Fast tasks:** Claude Haiku (relevance scoring, simple extraction)
- **Fallback:** GPT-4 Turbo (if Claude unavailable)

### Tools & Infrastructure
```python
# Agent tools implementation
tools = {
    # Search & Retrieval
    "web_search": BingSearchAPI(),  # or Google Custom Search
    "rss_reader": FeedParser(),
    "url_fetcher": requests + BeautifulSoup,

    # Storage
    "vector_db": WeaviateClient(),
    "sql_db": PostgreSQLClient(),

    # Analysis
    "embedding_generator": OpenAIEmbeddings(),
    "threat_taxonomy": ThreatFramework(),

    # Internal
    "aurora_api": AuroraIncidentAPI(),
    "newsletter_api": NewsletterTemplateEngine()
}
```

### Deployment
- **Container:** Docker with agent orchestrator
- **Scheduler:** Airflow DAG or Prefect workflow
- **Hosting:** Azure Container Instances or AKS
- **Monitoring:** Prometheus + Grafana for agent metrics

---

## Explainability & Logging

Every agent action is logged with full reasoning:

```json
{
  "agent": "relevance_agent",
  "timestamp": "2025-12-17T12:15:00Z",
  "action": "score_article",
  "article_id": "art_456",
  "reasoning": [
    "THOUGHT: This article discusses parked domain fraud with technical details",
    "OBSERVATION: Source is Infoblox, high-authority security firm",
    "THOUGHT: Published Dec 16, 2025 - within 7-day window",
    "ACTION: Retrieve full article content",
    "OBSERVATION: Contains specific attack vectors, geographic targeting details",
    "THOUGHT: Highly relevant - novel technique, high impact, actionable",
    "ACTION: Assign scores - relevance: 9, novelty: 8, impact: 10, actionability: 7",
    "DECISION: Flag as HIGH PRIORITY"
  ],
  "tool_calls": [
    {"tool": "get_article", "params": {"id": "art_456"}},
    {"tool": "update_article_score", "params": {"id": "art_456", "scores": {...}}}
  ],
  "result": "HIGH_PRIORITY_FLAGGED"
}
```

This enables:
- Debugging agent decisions
- Improving prompts based on failures
- Transparency for human reviewers
- Continuous learning from feedback

---

## Success Metrics

### Operational Metrics
- **Coverage:** % of manually-identified critical threats captured
- **Precision:** % of auto-selected articles deemed relevant by human
- **Latency:** Time from article publication to inclusion in draft
- **Cost:** Token usage per newsletter generation

### Quality Metrics
- **Accuracy:** % of summaries with factual errors (target: <2%)
- **Actionability:** % of items leading to team action (target: >30%)
- **Balance:** Coverage across threat categories (target: 4+ types per week)

### Agent-Specific Metrics
- **Research Agent:** Articles found per query, deduplication rate
- **Relevance Agent:** Score correlation with human labels
- **Analysis Agent:** Depth of technical insights (human rating)
- **Summary Agent:** Readability scores, style compliance
- **Quality Agent:** Revision request rate, approval time

---

## Future Enhancements

### Phase 2: Predictive Intelligence
- **Trend Forecasting Agent:** Identify emerging threats before widespread coverage
- **Pattern Recognition:** Connect weak signals across multiple sources
- **Threat Actor Profiling:** Track campaigns over time

### Phase 3: Interactive Intelligence
- **Query Agent:** Answer ad-hoc questions ("What do we know about parked domain fraud?")
- **Briefing Generator:** Create custom threat briefings on demand
- **Alert Agent:** Real-time monitoring for critical threats

### Phase 4: Closed-Loop Learning
- **Feedback Integration:** Learn from human edits to summaries
- **Outcome Tracking:** Did flagged threats materialize? Adjust scoring.
- **A/B Testing:** Experiment with different agent prompts

---

## Next Steps

1. **Build MVP Orchestration** (Week 1)
   - Single Orchestrator + Research Agent integration
   - Manual handoff to Relevance Agent

2. **Add Relevance & Summary Agents** (Week 2)
   - End-to-end pipeline (collection → summary)
   - Human evaluation of quality

3. **Integrate Analysis Agent** (Week 3)
   - Deep threat intelligence layer
   - Connect to Aurora API

4. **Add Quality Agent & Iteration** (Week 4)
   - Automated quality checks
   - Refinement loops

5. **Production Deployment** (Week 5)
   - Schedule weekly runs
   - Monitoring and alerting
   - Human review workflow

---

**Document Status:** Ready for Technical Review
**Owner:** Aurora Project Team
**Reviewers:** [Engineering Lead], [T&S Product Manager]
