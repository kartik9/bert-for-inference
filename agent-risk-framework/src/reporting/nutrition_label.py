from jinja2 import Environment, FileSystemLoader, BaseLoader
from datetime import datetime
from typing import Dict, Any
import json

from ..scoring.aivss import AIVSSScore, LetterGrade
from ..intake.models import AgentMetadata

class NutritionLabelGenerator:

    GRADE_COLORS = {
        "A": "#22c55e",  # green
        "B": "#84cc16",  # lime
        "C": "#eab308",  # yellow
        "D": "#f97316",  # orange
        "F": "#ef4444",  # red
    }

    HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        * { box-sizing: border-box; }
        .nutrition-label {
            font-family: 'Segoe UI', -apple-system, sans-serif;
            max-width: 420px;
            border: 3px solid #1f2937;
            border-radius: 12px;
            padding: 24px;
            background: #ffffff;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            border-bottom: 3px solid #1f2937;
            padding-bottom: 16px;
            margin-bottom: 16px;
        }
        .agent-info { flex: 1; }
        .agent-name {
            font-size: 1.5em;
            font-weight: 700;
            color: #1f2937;
            margin-bottom: 4px;
        }
        .agent-meta {
            color: #6b7280;
            font-size: 0.9em;
        }
        .grade-badge {
            width: 70px;
            height: 70px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2.2em;
            font-weight: 800;
            color: white;
            margin-left: 16px;
            flex-shrink: 0;
        }
        .score-section {
            text-align: center;
            padding: 16px 0;
            border-bottom: 1px solid #e5e7eb;
        }
        .overall-score {
            font-size: 3em;
            font-weight: 800;
            color: #1f2937;
        }
        .score-max {
            font-size: 1.2em;
            color: #9ca3af;
        }
        .confidence {
            margin-top: 8px;
            color: #6b7280;
        }
        .dimensions {
            padding: 16px 0;
        }
        .dimension-row {
            display: flex;
            align-items: center;
            margin: 12px 0;
        }
        .dimension-name {
            width: 120px;
            font-weight: 500;
            color: #374151;
        }
        .dimension-bar-container {
            flex: 1;
            height: 24px;
            background: #e5e7eb;
            border-radius: 6px;
            overflow: hidden;
            margin: 0 12px;
        }
        .dimension-bar {
            height: 100%;
            border-radius: 6px;
            transition: width 0.3s ease;
        }
        .dimension-score {
            width: 40px;
            text-align: right;
            font-weight: 600;
            color: #1f2937;
        }
        .trust-section {
            background: #f3f4f6;
            padding: 16px;
            border-radius: 8px;
            margin: 16px 0;
        }
        .trust-label {
            font-weight: 600;
            color: #374151;
        }
        .trust-tier {
            font-size: 1.1em;
            font-weight: 700;
            color: #1f2937;
            margin-top: 4px;
        }
        .trust-desc {
            font-size: 0.85em;
            color: #6b7280;
            margin-top: 4px;
        }
        .flags {
            margin-top: 16px;
        }
        .flag {
            padding: 8px 12px;
            border-radius: 6px;
            margin: 8px 0;
            font-size: 0.9em;
        }
        .flag-critical {
            background: #fef2f2;
            color: #dc2626;
            border-left: 4px solid #dc2626;
        }
        .flag-warning {
            background: #fffbeb;
            color: #d97706;
            border-left: 4px solid #d97706;
        }
        .footer {
            margin-top: 16px;
            padding-top: 12px;
            border-top: 1px solid #e5e7eb;
            font-size: 0.8em;
            color: #9ca3af;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="nutrition-label">
        <div class="header">
            <div class="agent-info">
                <div class="agent-name">{{ agent.name }}</div>
                <div class="agent-meta">v{{ agent.version }} • {{ agent.developer }}</div>
                <div class="agent-meta">{{ agent.agent_type.value }}</div>
            </div>
            <div class="grade-badge" style="background: {{ grade_color }};">
                {{ score.letter_grade.value }}
            </div>
        </div>

        <div class="score-section">
            <span class="overall-score">{{ score.overall_score }}</span>
            <span class="score-max">/100</span>
            <div class="confidence">
                Confidence: {{ confidence_stars }}
            </div>
        </div>

        <div class="dimensions">
            {% for dim_name, dim_score in dimensions %}
            <div class="dimension-row">
                <span class="dimension-name">{{ dim_name }}</span>
                <div class="dimension-bar-container">
                    <div class="dimension-bar" style="width: {{ dim_score }}%; background: {{ bar_color(dim_score) }};"></div>
                </div>
                <span class="dimension-score">{{ dim_score|int }}</span>
            </div>
            {% endfor %}
        </div>

        <div class="trust-section">
            <div class="trust-label">Trust Tier</div>
            <div class="trust-tier">Level {{ score.trust_tier.value }}: {{ score.trust_tier.name }}</div>
            <div class="trust-desc">{{ score.trust_tier.description }}</div>
        </div>

        {% if score.flags %}
        <div class="flags">
            {% for flag_key, flag_msg in score.flags.items() %}
            <div class="flag {{ 'flag-critical' if 'critical' in flag_key else 'flag-warning' }}">
                ⚠️ {{ flag_msg }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            Assessment Date: {{ assessment_date }} | Methodology: AIVSS v1.0
        </div>
    </div>
</body>
</html>
'''

    def __init__(self):
        self.env = Environment(loader=BaseLoader())
        self.env.globals['bar_color'] = self._bar_color

    def _bar_color(self, score: float) -> str:
        if score >= 80: return "#22c55e"
        if score >= 60: return "#84cc16"
        if score >= 40: return "#eab308"
        return "#ef4444"

    def generate_html(self, agent: AgentMetadata, score: AIVSSScore) -> str:
        template = self.env.from_string(self.HTML_TEMPLATE)

        dimensions = [
            ("Security", score.dimensions.security),
            ("Privacy", score.dimensions.privacy),
            ("Reliability", score.dimensions.reliability),
            ("Transparency", score.dimensions.transparency),
            ("Autonomy Risk", score.dimensions.autonomy_risk),
        ]

        confidence_level = int(score.confidence * 3)
        confidence_stars = "★" * confidence_level + "☆" * (3 - confidence_level)

        return template.render(
            agent=agent,
            score=score,
            dimensions=dimensions,
            grade_color=self.GRADE_COLORS.get(score.letter_grade.value, "#6b7280"),
            confidence_stars=confidence_stars,
            assessment_date=datetime.now().strftime("%Y-%m-%d")
        )

    def generate_json(self, agent: AgentMetadata, score: AIVSSScore) -> str:
        label = {
            "schema_version": "1.0",
            "methodology": "AIVSS",
            "assessment_date": datetime.now().isoformat(),
            "agent": {
                "id": agent.agent_id,
                "name": agent.name,
                "version": agent.version,
                "developer": agent.developer,
                "type": agent.agent_type.value
            },
            "scores": {
                "overall": score.overall_score,
                "grade": score.letter_grade.value,
                "confidence": score.confidence,
                "dimensions": score.dimensions.to_dict()
            },
            "trust": {
                "tier": score.trust_tier.value,
                "tier_name": score.trust_tier.name,
                "description": score.trust_tier.description
            },
            "flags": score.flags
        }
        return json.dumps(label, indent=2)
