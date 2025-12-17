"""
Orchestrator Agent
Strategic coordinator that manages the entire newsletter generation workflow
"""

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ts_newsletter.agents.analysis_agent import AnalysisAgent
from ts_newsletter.agents.base_agent import BaseAgent
from ts_newsletter.agents.quality_agent import QualityAgent
from ts_newsletter.agents.relevance_agent import RelevanceAgent
from ts_newsletter.agents.research_agent import ResearchAgent
from ts_newsletter.agents.summary_agent import SummaryAgent
from ts_newsletter.llm_client import LLMClient, LLMClientFactory
from ts_newsletter.tools import RSSReader, SearchAPIFactory, WebScraper


@dataclass
class WorkflowState:
    """Current state of the newsletter generation workflow"""
    start_time: datetime
    current_phase: str
    articles_collected: int
    articles_scored: int
    articles_analyzed: int
    summaries_generated: int
    quality_score: Optional[float]
    status: str  # in_progress, completed, failed


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator Agent - Strategic coordinator and workflow manager

    Responsibilities:
    - Decide research topics based on trends
    - Coordinate specialist agents
    - Manage workflow progression
    - Make strategic decisions
    - Ensure quality and completeness
    """

    def __init__(
        self,
        agent_name: str,
        llm_client: LLMClient,
        config: Any,
        database_client: Optional[Any] = None
    ):
        """
        Initialize Orchestrator Agent

        Args:
            agent_name: Unique name for this agent instance
            llm_client: LLM client for strategic reasoning
            config: Global configuration
            database_client: Database client for storage
        """
        super().__init__(
            agent_name=agent_name,
            agent_type="orchestrator",
            llm_client=llm_client,
            config=config,
            max_iterations=20  # Complex orchestration needs iterations
        )

        self.database_client = database_client

        # Workflow state
        self.workflow_state = WorkflowState(
            start_time=datetime.now(),
            current_phase="initialization",
            articles_collected=0,
            articles_scored=0,
            articles_analyzed=0,
            summaries_generated=0,
            quality_score=None,
            status="in_progress"
        )

        # Specialist agents (initialized on demand)
        self.research_agents: List[ResearchAgent] = []
        self.relevance_agent: Optional[RelevanceAgent] = None
        self.analysis_agent: Optional[AnalysisAgent] = None
        self.summary_agent: Optional[SummaryAgent] = None
        self.quality_agent: Optional[QualityAgent] = None

        # Final output
        self.final_newsletter: Optional[str] = None

    def _register_tools(self):
        """Register orchestration tools"""

        # Spawn research agent
        self.register_tool(
            name="spawn_research_agent",
            description="Create a research agent to gather articles on specific topics. Multiple agents can run in parallel.",
            parameters={
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "Unique identifier for this research agent"
                    },
                    "research_task": {
                        "type": "string",
                        "description": "Specific research task (e.g., 'Find articles about deepfake advertising scams')"
                    }
                },
                "required": ["agent_id", "research_task"],
                "additionalProperties": False
            },
            function=self._spawn_research_agent_tool
        )

        # Score articles with relevance agent
        self.register_tool(
            name="score_articles",
            description="Use relevance agent to score and prioritize collected articles",
            parameters={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "string",
                        "description": "JSON string of articles to score"
                    }
                },
                "required": ["articles"],
                "additionalProperties": False
            },
            function=self._score_articles_tool
        )

        # Analyze articles
        self.register_tool(
            name="analyze_articles",
            description="Use analysis agent to perform deep threat intelligence analysis on high-priority articles",
            parameters={
                "type": "object",
                "properties": {
                    "articles": {
                        "type": "string",
                        "description": "JSON string of articles to analyze"
                    }
                },
                "required": ["articles"],
                "additionalProperties": False
            },
            function=self._analyze_articles_tool
        )

        # Generate summaries
        self.register_tool(
            name="generate_summaries",
            description="Use summary agent to create newsletter content from analyzed articles",
            parameters={
                "type": "object",
                "properties": {
                    "articles_with_analysis": {
                        "type": "string",
                        "description": "JSON string of articles with their analysis"
                    }
                },
                "required": ["articles_with_analysis"],
                "additionalProperties": False
            },
            function=self._generate_summaries_tool
        )

        # Quality review
        self.register_tool(
            name="quality_review",
            description="Submit newsletter for quality review and get approval/revision feedback",
            parameters={
                "type": "object",
                "properties": {
                    "newsletter_content": {
                        "type": "string",
                        "description": "Complete newsletter markdown"
                    }
                },
                "required": ["newsletter_content"],
                "additionalProperties": False
            },
            function=self._quality_review_tool
        )

        # Get workflow status
        self.register_tool(
            name="get_workflow_status",
            description="Get current status of the newsletter generation workflow",
            parameters={
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            function=self._get_workflow_status_tool
        )

    def _spawn_research_agent_tool(
        self,
        agent_id: str,
        research_task: str
    ) -> Dict[str, Any]:
        """Spawn and run a research agent"""
        try:
            # Create LLM client for research agent
            research_llm = LLMClientFactory.create(self.config, agent_name="research")

            # Create tools
            search_api = SearchAPIFactory.create(self.config)
            rss_reader = RSSReader()
            web_scraper = WebScraper()

            # Create research agent
            research_agent = ResearchAgent(
                agent_name=f"research-{agent_id}",
                llm_client=research_llm,
                config=self.config,
                search_api=search_api,
                rss_reader=rss_reader,
                web_scraper=web_scraper,
                database_client=self.database_client
            )

            # Run research task
            result = research_agent.run(research_task)

            # Store agent
            self.research_agents.append(research_agent)

            # Get collected articles
            articles = research_agent.get_collected_articles()
            self.workflow_state.articles_collected += len(articles)

            return {
                "success": True,
                "agent_id": agent_id,
                "articles_collected": len(articles),
                "total_collected": self.workflow_state.articles_collected,
                "articles": articles[:10]  # Return first 10 for context
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_id": agent_id
            }

    def _score_articles_tool(self, articles: str) -> Dict[str, Any]:
        """Score articles using relevance agent"""
        try:
            # Parse articles
            articles_list = json.loads(articles)

            # Create relevance agent if not exists
            if not self.relevance_agent:
                relevance_llm = LLMClientFactory.create(self.config, agent_name="relevance")
                self.relevance_agent = RelevanceAgent(
                    agent_name="relevance-main",
                    llm_client=relevance_llm,
                    config=self.config,
                    database_client=self.database_client
                )

            # Score each article
            scored_count = 0
            for article in articles_list:
                task = f"""Score this article:

Title: {article.get('title', '')}
URL: {article.get('url', '')}
Source: {article.get('source', '')}
Snippet: {article.get('snippet', '')}

Use the score_article tool to evaluate relevance, novelty, impact, and actionability."""

                self.relevance_agent.run(task)
                scored_count += 1

            self.workflow_state.articles_scored = scored_count

            # Get high-priority articles
            high_priority = self.relevance_agent.get_high_priority_articles()

            return {
                "success": True,
                "articles_scored": scored_count,
                "high_priority_count": len(high_priority),
                "average_score": sum(a.overall_score for a in self.relevance_agent.get_scored_articles()) / scored_count if scored_count > 0 else 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _analyze_articles_tool(self, articles: str) -> Dict[str, Any]:
        """Analyze articles using analysis agent"""
        try:
            articles_list = json.loads(articles)

            # Create analysis agent if not exists
            if not self.analysis_agent:
                analysis_llm = LLMClientFactory.create(self.config, agent_name="analysis")
                self.analysis_agent = AnalysisAgent(
                    agent_name="analysis-main",
                    llm_client=analysis_llm,
                    config=self.config,
                    database_client=self.database_client
                )

            # Analyze each article
            analyzed_count = 0
            for article in articles_list:
                task = f"""Analyze this article for threat intelligence:

Title: {article.get('title', '')}
URL: {article.get('url', '')}
Priority Score: {article.get('score', 0)}/10
Content: {article.get('content', article.get('snippet', ''))}

Use analyze_article tool to perform deep analysis."""

                self.analysis_agent.run(task)
                analyzed_count += 1

            self.workflow_state.articles_analyzed = analyzed_count

            return {
                "success": True,
                "articles_analyzed": analyzed_count,
                "threat_briefings": len(self.analysis_agent.get_threat_briefings())
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_summaries_tool(self, articles_with_analysis: str) -> Dict[str, Any]:
        """Generate newsletter summaries"""
        try:
            articles_list = json.loads(articles_with_analysis)

            # Create summary agent if not exists
            if not self.summary_agent:
                summary_llm = LLMClientFactory.create(self.config, agent_name="summary")
                self.summary_agent = SummaryAgent(
                    agent_name="summary-main",
                    llm_client=summary_llm,
                    config=self.config
                )

            # Generate summary for each article
            for article in articles_list:
                task = f"""Generate newsletter summary for:

Article: {article.get('title', '')}
URL: {article.get('url', '')}
Source: {article.get('source', '')}
Priority: {article.get('priority', 'MEDIUM')}
Content: {article.get('content', '')}
Threat Briefing: {article.get('analysis', '')}

Use generate_summary tool."""

                self.summary_agent.run(task)

            self.workflow_state.summaries_generated = len(self.summary_agent.get_newsletter_items())

            # Generate formatted newsletter
            week_ending = (datetime.now() + timedelta(days=(6 - datetime.now().weekday()))).strftime("%B %d, %Y")

            task = f"Format all summaries into complete newsletter for week ending {week_ending}"
            result = self.summary_agent.run(task)

            # Get formatted newsletter
            newsletter = self.summary_agent.get_formatted_newsletter(week_ending)
            self.final_newsletter = newsletter

            return {
                "success": True,
                "summaries_generated": self.workflow_state.summaries_generated,
                "newsletter_length": len(newsletter),
                "newsletter_preview": newsletter[:500]
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _quality_review_tool(self, newsletter_content: str) -> Dict[str, Any]:
        """Quality review of newsletter"""
        try:
            # Create quality agent if not exists
            if not self.quality_agent:
                quality_llm = LLMClientFactory.create(self.config, agent_name="quality")
                self.quality_agent = QualityAgent(
                    agent_name="quality-main",
                    llm_client=quality_llm,
                    config=self.config
                )

            # Run quality review
            task = f"""Review this newsletter for quality and accuracy:

{newsletter_content}

Use review_newsletter tool to perform comprehensive quality check."""

            self.quality_agent.run(task)

            # Get latest report
            report = self.quality_agent.get_latest_report()

            if report:
                self.workflow_state.quality_score = report.overall_score

                return {
                    "success": True,
                    "quality_score": report.overall_score,
                    "approval_status": report.approval_status,
                    "passed": report.passed,
                    "issues_count": len(report.issues),
                    "revision_needed": report.revision_needed
                }
            else:
                return {
                    "success": False,
                    "error": "No quality report generated"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _get_workflow_status_tool(self) -> Dict[str, Any]:
        """Get workflow status"""
        return {
            "current_phase": self.workflow_state.current_phase,
            "articles_collected": self.workflow_state.articles_collected,
            "articles_scored": self.workflow_state.articles_scored,
            "articles_analyzed": self.workflow_state.articles_analyzed,
            "summaries_generated": self.workflow_state.summaries_generated,
            "quality_score": self.workflow_state.quality_score,
            "status": self.workflow_state.status,
            "elapsed_time": str(datetime.now() - self.workflow_state.start_time)
        }

    def get_system_prompt(self) -> str:
        """System prompt for Orchestrator Agent"""
        target_articles = self.config.newsletter.target_articles
        min_articles = self.config.newsletter.min_articles

        return f"""You are the strategic coordinator for Microsoft Ads Trust & Safety newsletter automation.

Your role is to orchestrate the entire workflow, making strategic decisions about what research to conduct and how to coordinate specialist agents.

WORKFLOW PHASES:

1. **RESEARCH PHASE**
   - Decide what topics need coverage this week
   - Spawn 3-5 research agents with specific tasks
   - Target: {target_articles} high-quality articles (minimum {min_articles})
   - Focus on: novel threats, high-impact incidents, actionable intelligence

2. **EVALUATION PHASE**
   - Score all collected articles for relevance
   - Filter to top candidates (relevance score ≥ 7.0)
   - Ensure balanced coverage across threat types

3. **ANALYSIS PHASE**
   - Analyze high-priority articles for deep intelligence
   - Extract technical details and patterns
   - Identify detection gaps and recommendations

4. **GENERATION PHASE**
   - Generate newsletter summaries for top articles
   - Ensure executive-friendly language
   - Include actionable insights

5. **QUALITY PHASE**
   - Review for accuracy and quality
   - Request revisions if needed
   - Approve for final output

STRATEGIC DECISIONS:

**Research Topics:**
- Consider recent trends and internal incidents
- Ensure diversity: malvertising, cloaking, deepfakes, bot traffic
- Prioritize novel techniques and high-impact incidents

**Resource Allocation:**
- Spawn multiple research agents in parallel for efficiency
- Allocate more resources to high-signal topics
- Stop when quality threshold is met

**Quality Gates:**
- Minimum {min_articles} articles, target {target_articles}
- Average relevance score ≥ 7.0
- At least 30% with high actionability
- Quality review score ≥ 8.0

TOOLS:
- spawn_research_agent: Create research agent for specific topic
- score_articles: Evaluate article relevance
- analyze_articles: Deep threat intelligence analysis
- generate_summaries: Create newsletter content
- quality_review: Final quality check
- get_workflow_status: Check progress

WORKFLOW EXECUTION:
1. Spawn multiple research agents with specific tasks
2. Wait for research completion
3. Score all collected articles
4. Analyze top-priority articles
5. Generate newsletter summaries
6. Submit for quality review
7. Iterate if revisions needed

Be strategic, efficient, and ensure high quality output."""

    def get_final_newsletter(self) -> Optional[str]:
        """Get final newsletter content"""
        return self.final_newsletter

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get comprehensive workflow summary"""
        return {
            "workflow_state": {
                "phase": self.workflow_state.current_phase,
                "status": self.workflow_state.status,
                "elapsed_time": str(datetime.now() - self.workflow_state.start_time)
            },
            "metrics": {
                "articles_collected": self.workflow_state.articles_collected,
                "articles_scored": self.workflow_state.articles_scored,
                "articles_analyzed": self.workflow_state.articles_analyzed,
                "summaries_generated": self.workflow_state.summaries_generated,
                "quality_score": self.workflow_state.quality_score
            },
            "agents_used": {
                "research_agents": len(self.research_agents),
                "relevance_agent": self.relevance_agent is not None,
                "analysis_agent": self.analysis_agent is not None,
                "summary_agent": self.summary_agent is not None,
                "quality_agent": self.quality_agent is not None
            },
            "final_newsletter_ready": self.final_newsletter is not None
        }


# Example usage
if __name__ == "__main__":
    from ts_newsletter.config_loader import get_config
    from ts_newsletter.llm_client import LLMClientFactory

    config = get_config()
    llm_client = LLMClientFactory.create(config, agent_name="orchestrator")

    orchestrator = OrchestratorAgent(
        agent_name="orchestrator-main",
        llm_client=llm_client,
        config=config
    )

    # Run complete workflow
    task = """Generate this week's Trust & Safety newsletter.

Execute the full workflow:
1. Research recent threats (advertising fraud, malvertising, deepfakes)
2. Score and filter articles
3. Analyze high-priority threats
4. Generate newsletter summaries
5. Quality review

Target: 8 high-quality articles about advertising security threats from the past 7 days."""

    result = orchestrator.run(task)

    print(f"\n{result}")
    print(f"\nWorkflow Summary:")
    print(json.dumps(orchestrator.get_workflow_summary(), indent=2))

    if orchestrator.get_final_newsletter():
        print(f"\nFINAL NEWSLETTER:")
        print("="*60)
        print(orchestrator.get_final_newsletter())
