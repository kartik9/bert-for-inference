-- Trust & Safety Newsletter Automation - Database Schema
-- PostgreSQL schema for metadata and workflow state

-- Articles collected by research agents
CREATE TABLE IF NOT EXISTS articles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    source TEXT,
    content TEXT,
    snippet TEXT,
    published_date TIMESTAMP,
    collected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Embedding reference
    embedding_id UUID,

    -- Metadata
    author TEXT,
    fetch_metadata JSONB,

    -- Research context
    collected_by_agent TEXT,
    research_task TEXT,

    CONSTRAINT url_unique UNIQUE (url)
);

-- Article relevance scores
CREATE TABLE IF NOT EXISTS article_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- Multi-dimensional scores
    relevance_score FLOAT CHECK (relevance_score >= 0 AND relevance_score <= 10),
    novelty_score FLOAT CHECK (novelty_score >= 0 AND novelty_score <= 10),
    impact_score FLOAT CHECK (impact_score >= 0 AND impact_score <= 10),
    actionability_score FLOAT CHECK (actionability_score >= 0 AND actionability_score <= 10),
    overall_score FLOAT CHECK (overall_score >= 0 AND overall_score <= 10),

    -- Priority
    priority_level TEXT CHECK (priority_level IN ('HIGH', 'MEDIUM', 'LOW')),

    -- Reasoning
    reasoning TEXT,
    flags JSONB DEFAULT '[]',
    recommended_action TEXT,

    -- Metadata
    scored_by_agent TEXT,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT one_score_per_article UNIQUE (article_id)
);

-- Threat intelligence briefings
CREATE TABLE IF NOT EXISTS threat_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,

    -- Threat classification
    threat_type TEXT,
    attack_vector TEXT,
    evasion_techniques JSONB DEFAULT '[]',

    -- Technical indicators
    indicators JSONB DEFAULT '{}', -- {domains: [...], ips: [...], patterns: [...]}
    attribution TEXT,

    -- Pattern analysis
    related_incidents JSONB DEFAULT '[]',
    is_part_of_campaign BOOLEAN DEFAULT FALSE,
    evolution_from TEXT,

    -- Microsoft implications
    aurora_detection_capable BOOLEAN DEFAULT FALSE,
    detection_gaps JSONB DEFAULT '[]',
    recommended_detection_logic TEXT,

    -- Actions
    immediate_actions JSONB DEFAULT '[]',
    short_term_actions JSONB DEFAULT '[]',
    long_term_actions JSONB DEFAULT '[]',

    -- Full briefing
    full_briefing TEXT,

    -- Metadata
    analyzed_by_agent TEXT,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT one_briefing_per_article UNIQUE (article_id)
);

-- Newsletter items (generated summaries)
CREATE TABLE IF NOT EXISTS newsletter_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    article_id UUID NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    newsletter_id UUID,  -- Reference to newsletter (below)

    -- Content
    headline TEXT NOT NULL,
    emoji TEXT,
    what_happened TEXT,
    key_details JSONB DEFAULT '[]',
    why_it_matters TEXT,
    source_attribution TEXT,

    -- Metadata
    word_count INTEGER,
    priority_level TEXT,
    published_date TEXT,
    source_name TEXT,

    -- Generation metadata
    generated_by_agent TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Newsletters (weekly editions)
CREATE TABLE IF NOT EXISTS newsletters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    week_ending DATE NOT NULL,

    -- Content
    markdown_content TEXT,
    formatted_content TEXT,

    -- Status
    status TEXT CHECK (status IN ('draft', 'in_review', 'approved', 'published')) DEFAULT 'draft',

    -- Quality metrics
    quality_score FLOAT,
    quality_report JSONB,

    -- Workflow metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    published_at TIMESTAMP,

    -- Statistics
    total_articles INTEGER,
    high_priority_count INTEGER,
    average_article_score FLOAT,

    -- Generation metadata
    generated_by_workflow_id UUID,
    orchestrator_agent TEXT,

    CONSTRAINT one_newsletter_per_week UNIQUE (week_ending)
);

-- Add foreign key to newsletter_items
ALTER TABLE newsletter_items
ADD CONSTRAINT fk_newsletter
FOREIGN KEY (newsletter_id) REFERENCES newsletters(id) ON DELETE SET NULL;

-- Agent execution logs
CREATE TABLE IF NOT EXISTS agent_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Agent identification
    agent_name TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    session_id UUID NOT NULL,

    -- Action details
    action_id UUID NOT NULL,
    action_type TEXT NOT NULL,  -- thought, tool_call, observation, decision, error
    content TEXT,

    -- Tool use
    tool_name TEXT,
    tool_args JSONB,
    tool_result JSONB,

    -- Timing
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Context
    workflow_id UUID,
    parent_agent_name TEXT  -- For nested agent calls
);

-- Workflow executions
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Workflow metadata
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status TEXT CHECK (status IN ('in_progress', 'completed', 'failed')) DEFAULT 'in_progress',

    -- Phase tracking
    current_phase TEXT,

    -- Metrics
    articles_collected INTEGER DEFAULT 0,
    articles_scored INTEGER DEFAULT 0,
    articles_analyzed INTEGER DEFAULT 0,
    summaries_generated INTEGER DEFAULT 0,
    quality_score FLOAT,

    -- Agents used
    research_agent_count INTEGER DEFAULT 0,
    agents_metadata JSONB DEFAULT '{}',

    -- Output
    newsletter_id UUID REFERENCES newsletters(id),

    -- Configuration snapshot
    config_snapshot JSONB
);

-- RSS feed tracking
CREATE TABLE IF NOT EXISTS rss_feed_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    feed_url TEXT NOT NULL,
    feed_name TEXT NOT NULL,

    -- Fetch metadata
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    articles_found INTEGER,
    articles_new INTEGER,

    -- Status
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,

    -- Performance
    fetch_duration_ms INTEGER
);

-- Historical newsletter performance (for learning)
CREATE TABLE IF NOT EXISTS newsletter_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    newsletter_id UUID NOT NULL REFERENCES newsletters(id),

    -- Engagement metrics (manual entry)
    open_rate FLOAT,
    click_rate FLOAT,
    feedback_comments TEXT,

    -- Follow-up actions taken
    investigations_triggered INTEGER,
    policy_changes_initiated INTEGER,

    -- Recorded by
    recorded_by TEXT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_articles_url ON articles(url);
CREATE INDEX idx_articles_collected_date ON articles(collected_date DESC);
CREATE INDEX idx_articles_published_date ON articles(published_date DESC);

CREATE INDEX idx_article_scores_priority ON article_scores(priority_level);
CREATE INDEX idx_article_scores_overall ON article_scores(overall_score DESC);

CREATE INDEX idx_threat_briefings_type ON threat_briefings(threat_type);
CREATE INDEX idx_threat_briefings_aurora ON threat_briefings(aurora_detection_capable);

CREATE INDEX idx_newsletters_week ON newsletters(week_ending DESC);
CREATE INDEX idx_newsletters_status ON newsletters(status);

CREATE INDEX idx_agent_logs_session ON agent_logs(session_id);
CREATE INDEX idx_agent_logs_timestamp ON agent_logs(timestamp DESC);
CREATE INDEX idx_agent_logs_type ON agent_logs(agent_type, action_type);

CREATE INDEX idx_workflow_executions_status ON workflow_executions(status);
CREATE INDEX idx_workflow_executions_start ON workflow_executions(start_time DESC);

-- Views for common queries

-- High-priority articles with all metadata
CREATE OR REPLACE VIEW v_high_priority_articles AS
SELECT
    a.id,
    a.url,
    a.title,
    a.source,
    a.published_date,
    s.overall_score,
    s.priority_level,
    s.reasoning,
    b.threat_type,
    b.aurora_detection_capable,
    b.full_briefing
FROM articles a
JOIN article_scores s ON a.id = s.article_id
LEFT JOIN threat_briefings b ON a.id = b.article_id
WHERE s.priority_level = 'HIGH'
ORDER BY s.overall_score DESC;

-- Recent newsletters with statistics
CREATE OR REPLACE VIEW v_newsletter_summary AS
SELECT
    n.id,
    n.week_ending,
    n.status,
    n.quality_score,
    n.total_articles,
    n.high_priority_count,
    n.average_article_score,
    n.created_at,
    n.completed_at,
    COUNT(ni.id) as items_count
FROM newsletters n
LEFT JOIN newsletter_items ni ON n.id = ni.newsletter_id
GROUP BY n.id
ORDER BY n.week_ending DESC;

-- Agent performance metrics
CREATE OR REPLACE VIEW v_agent_performance AS
SELECT
    agent_type,
    COUNT(DISTINCT session_id) as total_runs,
    AVG(EXTRACT(EPOCH FROM (MAX(timestamp) - MIN(timestamp)))) as avg_duration_seconds,
    COUNT(*) FILTER (WHERE action_type = 'error') as error_count,
    COUNT(*) FILTER (WHERE action_type = 'tool_call') as total_tool_calls
FROM agent_logs
GROUP BY agent_type;

COMMENT ON TABLE articles IS 'Articles collected by research agents from web search and RSS feeds';
COMMENT ON TABLE article_scores IS 'Multi-dimensional relevance scores for articles';
COMMENT ON TABLE threat_briefings IS 'Deep threat intelligence analysis for high-priority articles';
COMMENT ON TABLE newsletter_items IS 'Generated newsletter summaries ready for publication';
COMMENT ON TABLE newsletters IS 'Weekly newsletter editions with metadata and status';
COMMENT ON TABLE agent_logs IS 'Detailed execution traces for all agent actions';
COMMENT ON TABLE workflow_executions IS 'Complete workflow execution tracking from start to finish';
COMMENT ON TABLE newsletter_feedback IS 'Engagement metrics and outcomes for continuous improvement';
