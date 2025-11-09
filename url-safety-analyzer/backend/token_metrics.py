"""
Token Consumption Metrics Tracker
Tracks GPT token usage across different models and token types (text vs image)
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    """Single token usage record"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    # Image-specific tokens (for multimodal models)
    image_tokens: int = 0
    text_tokens: int = 0

    def to_dict(self) -> Dict[str, int]:
        return asdict(self)


@dataclass
class ModelMetrics:
    """Metrics for a specific model"""
    model_name: str
    call_count: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_image_tokens: int = 0
    total_text_tokens: int = 0
    estimated_cost_usd: float = 0.0

    def add_usage(self, usage: TokenUsage, cost: float = 0.0):
        """Add token usage to model metrics"""
        self.call_count += 1
        self.total_prompt_tokens += usage.prompt_tokens
        self.total_completion_tokens += usage.completion_tokens
        self.total_tokens += usage.total_tokens
        self.total_image_tokens += usage.image_tokens
        self.total_text_tokens += usage.text_tokens
        self.estimated_cost_usd += cost

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class TokenMetricsTracker:
    """
    Comprehensive token consumption tracker

    Features:
    - Per-model token tracking
    - Text vs Image token breakdown
    - Cost estimation
    - Call-level granularity
    - Session and investigation-level aggregation
    """

    # Pricing per 1M tokens (as of Nov 2024)
    PRICING = {
        "gpt-5": {
            "prompt": 3.00,      # $3/1M tokens (estimated)
            "completion": 15.00,  # $15/1M tokens (estimated)
        },
        "gpt-4o": {
            "prompt": 2.50,
            "completion": 10.00,
        },
        "gpt-4o-mini": {
            "prompt": 0.150,
            "completion": 0.600,
        },
        "gpt-4-turbo": {
            "prompt": 10.00,
            "completion": 30.00,
        },
        "gpt-4": {
            "prompt": 30.00,
            "completion": 60.00,
        }
    }

    def __init__(self):
        """Initialize metrics tracker"""
        self.metrics_by_model: Dict[str, ModelMetrics] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.session_start = datetime.utcnow()
        self.investigation_id: Optional[str] = None

    def track_api_call(
        self,
        model: str,
        usage: TokenUsage,
        operation: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Track a single API call

        Args:
            model: Model name (e.g., "gpt-5", "gpt-4o-mini")
            usage: TokenUsage object with token counts
            operation: Operation type (e.g., "investigation_plan", "confidence_assessment")
            metadata: Additional metadata for the call

        Returns:
            Estimated cost in USD for this call
        """
        # Ensure model metrics exist
        if model not in self.metrics_by_model:
            self.metrics_by_model[model] = ModelMetrics(model_name=model)

        # Calculate cost
        cost = self._calculate_cost(model, usage)

        # Add to model metrics
        self.metrics_by_model[model].add_usage(usage, cost)

        # Record in call history
        call_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "model": model,
            "operation": operation,
            "usage": usage.to_dict(),
            "cost_usd": cost,
            "metadata": metadata or {}
        }

        if self.investigation_id:
            call_record["investigation_id"] = self.investigation_id

        self.call_history.append(call_record)

        logger.debug(
            f"Token usage tracked: {model} | {operation} | "
            f"Tokens: {usage.total_tokens} | Cost: ${cost:.4f}"
        )

        return cost

    def track_from_response(
        self,
        response: Any,
        model: str,
        operation: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Track tokens from OpenAI API response object

        Args:
            response: OpenAI ChatCompletion response
            model: Model name
            operation: Operation type
            metadata: Additional metadata

        Returns:
            Estimated cost in USD
        """
        # Extract usage from response
        usage_data = response.usage if hasattr(response, 'usage') else {}

        # Create TokenUsage object
        usage = TokenUsage(
            prompt_tokens=getattr(usage_data, 'prompt_tokens', 0),
            completion_tokens=getattr(usage_data, 'completion_tokens', 0),
            total_tokens=getattr(usage_data, 'total_tokens', 0)
        )

        # Determine if images were used
        has_images = metadata and metadata.get("has_images", False)

        if has_images and model == "gpt-4o":
            # For GPT-4o with images, estimate image tokens
            usage.image_tokens = metadata.get("estimated_image_tokens", 0)
            usage.text_tokens = usage.total_tokens - usage.image_tokens
        else:
            # Text-only
            usage.text_tokens = usage.total_tokens
            usage.image_tokens = 0

        return self.track_api_call(model, usage, operation, metadata)

    def _calculate_cost(self, model: str, usage: TokenUsage) -> float:
        """Calculate estimated cost for token usage"""
        model_key = self._normalize_model_name(model)

        if model_key not in self.PRICING:
            logger.warning(f"No pricing data for model: {model}. Using GPT-4o pricing.")
            model_key = "gpt-4o"

        pricing = self.PRICING[model_key]

        # Calculate cost (pricing is per 1M tokens)
        prompt_cost = (usage.prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (usage.completion_tokens / 1_000_000) * pricing["completion"]

        return prompt_cost + completion_cost

    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup"""
        model_lower = model.lower()

        if "gpt-5" in model_lower:
            return "gpt-5"
        elif "gpt-4o-mini" in model_lower:
            return "gpt-4o-mini"
        elif "gpt-4o" in model_lower:
            return "gpt-4o"
        elif "gpt-4-turbo" in model_lower:
            return "gpt-4-turbo"
        elif "gpt-4" in model_lower:
            return "gpt-4"

        return model_lower

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        total_calls = sum(m.call_count for m in self.metrics_by_model.values())
        total_tokens = sum(m.total_tokens for m in self.metrics_by_model.values())
        total_cost = sum(m.estimated_cost_usd for m in self.metrics_by_model.values())
        total_image_tokens = sum(m.total_image_tokens for m in self.metrics_by_model.values())
        total_text_tokens = sum(m.total_text_tokens for m in self.metrics_by_model.values())

        # Per-model breakdown
        model_breakdown = {
            model: metrics.to_dict()
            for model, metrics in self.metrics_by_model.items()
        }

        # Token type breakdown
        token_breakdown = {
            "text_tokens": total_text_tokens,
            "image_tokens": total_image_tokens,
            "total_tokens": total_tokens,
            "text_percentage": (total_text_tokens / total_tokens * 100) if total_tokens > 0 else 0,
            "image_percentage": (total_image_tokens / total_tokens * 100) if total_tokens > 0 else 0
        }

        # Operation breakdown
        operation_stats = self._get_operation_stats()

        return {
            "session_start": self.session_start.isoformat(),
            "session_duration_seconds": (datetime.utcnow() - self.session_start).total_seconds(),
            "investigation_id": self.investigation_id,
            "total_api_calls": total_calls,
            "total_tokens": total_tokens,
            "total_cost_usd": total_cost,
            "token_breakdown": token_breakdown,
            "model_breakdown": model_breakdown,
            "operation_breakdown": operation_stats,
            "call_history_count": len(self.call_history)
        }

    def _get_operation_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics grouped by operation type"""
        stats = defaultdict(lambda: {
            "count": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "models_used": set()
        })

        for call in self.call_history:
            op = call["operation"]
            stats[op]["count"] += 1
            stats[op]["total_tokens"] += call["usage"]["total_tokens"]
            stats[op]["total_cost"] += call["cost_usd"]
            stats[op]["models_used"].add(call["model"])

        # Convert sets to lists for JSON serialization
        return {
            op: {
                "count": data["count"],
                "total_tokens": data["total_tokens"],
                "total_cost_usd": data["total_cost"],
                "average_tokens_per_call": data["total_tokens"] / data["count"] if data["count"] > 0 else 0,
                "models_used": list(data["models_used"])
            }
            for op, data in stats.items()
        }

    def export_to_json(self, filepath: str):
        """Export metrics to JSON file"""
        summary = self.get_summary()

        export_data = {
            "summary": summary,
            "call_history": self.call_history
        }

        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        logger.info(f"Metrics exported to {filepath}")

    def print_summary(self):
        """Print human-readable metrics summary"""
        summary = self.get_summary()

        print("\n" + "="*80)
        print("TOKEN CONSUMPTION METRICS SUMMARY")
        print("="*80)

        print(f"\nSession Duration: {summary['session_duration_seconds']:.1f} seconds")
        print(f"Total API Calls: {summary['total_api_calls']}")
        print(f"Total Tokens: {summary['total_tokens']:,}")
        print(f"Total Cost: ${summary['total_cost_usd']:.4f}")

        # Token type breakdown
        print("\n" + "-"*80)
        print("TOKEN TYPE BREAKDOWN")
        print("-"*80)
        tb = summary['token_breakdown']
        print(f"Text Tokens:  {tb['text_tokens']:,} ({tb['text_percentage']:.1f}%)")
        print(f"Image Tokens: {tb['image_tokens']:,} ({tb['image_percentage']:.1f}%)")

        # Model breakdown
        print("\n" + "-"*80)
        print("MODEL BREAKDOWN")
        print("-"*80)
        for model, metrics in summary['model_breakdown'].items():
            print(f"\n{model}:")
            print(f"  Calls: {metrics['call_count']}")
            print(f"  Prompt Tokens: {metrics['total_prompt_tokens']:,}")
            print(f"  Completion Tokens: {metrics['total_completion_tokens']:,}")
            print(f"  Total Tokens: {metrics['total_tokens']:,}")
            print(f"  Text Tokens: {metrics['total_text_tokens']:,}")
            print(f"  Image Tokens: {metrics['total_image_tokens']:,}")
            print(f"  Cost: ${metrics['estimated_cost_usd']:.4f}")

        # Operation breakdown
        if summary['operation_breakdown']:
            print("\n" + "-"*80)
            print("OPERATION BREAKDOWN")
            print("-"*80)
            for op, stats in summary['operation_breakdown'].items():
                print(f"\n{op}:")
                print(f"  Calls: {stats['count']}")
                print(f"  Total Tokens: {stats['total_tokens']:,}")
                print(f"  Avg Tokens/Call: {stats['average_tokens_per_call']:.1f}")
                print(f"  Cost: ${stats['total_cost_usd']:.4f}")
                print(f"  Models: {', '.join(stats['models_used'])}")

        print("\n" + "="*80 + "\n")

    def reset(self):
        """Reset all metrics"""
        self.metrics_by_model.clear()
        self.call_history.clear()
        self.session_start = datetime.utcnow()
        self.investigation_id = None

    def set_investigation_id(self, investigation_id: str):
        """Set investigation ID for tracking"""
        self.investigation_id = investigation_id


# Global tracker instance
_global_tracker: Optional[TokenMetricsTracker] = None


def get_global_tracker() -> TokenMetricsTracker:
    """Get or create global metrics tracker"""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = TokenMetricsTracker()
    return _global_tracker


def reset_global_tracker():
    """Reset global metrics tracker"""
    global _global_tracker
    if _global_tracker is not None:
        _global_tracker.reset()
