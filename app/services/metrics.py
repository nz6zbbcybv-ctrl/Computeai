"""
Metrics collection and tracking service.
"""
import time
from typing import Dict, Any, List
from collections import deque
from datetime import datetime, timedelta
from app.config import Config
from app.utils.logger import setup_logger

logger = setup_logger("metrics")


class MetricsService:
    """Service for collecting and tracking application metrics."""
    
    def __init__(self):
        """Initialize metrics service."""
        self.metrics: List[Dict[str, Any]] = []
        self.recent_latencies = deque(maxlen=100)
        self.recent_tokens_per_sec = deque(maxlen=100)
        self.error_count = 0
        self.total_requests = 0
        self.enabled = Config.METRICS_ENABLED
        
        if self.enabled:
            logger.info("Metrics service initialized")
    
    def record_request(
        self,
        latency: float,
        tokens: int,
        tokens_per_sec: float,
        model: str,
        success: bool = True
    ):
        """
        Record a request metric.
        
        Args:
            latency: Request latency in seconds
            tokens: Number of tokens generated
            tokens_per_sec: Tokens per second
            model: Model name used
            success: Whether request was successful
        """
        if not self.enabled:
            return
        
        self.total_requests += 1
        
        if not success:
            self.error_count += 1
        
        metric = {
            "timestamp": datetime.utcnow().isoformat(),
            "latency": latency,
            "tokens": tokens,
            "tokens_per_sec": tokens_per_sec,
            "model": model,
            "success": success
        }
        
        self.metrics.append(metric)
        self.recent_latencies.append(latency)
        self.recent_tokens_per_sec.append(tokens_per_sec)
        
        # Cleanup old metrics
        self._cleanup_old_metrics()
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        if not self.metrics:
            return
        
        cutoff = datetime.utcnow() - timedelta(hours=Config.METRICS_RETENTION_HOURS)
        
        self.metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current metrics statistics.
        
        Returns:
            Dict with aggregated metrics
        """
        if not self.enabled or not self.recent_latencies:
            return {
                "total_requests": self.total_requests,
                "error_count": self.error_count,
                "error_rate": 0.0,
                "avg_latency": 0.0,
                "avg_tokens_per_sec": 0.0
            }
        
        avg_latency = sum(self.recent_latencies) / len(self.recent_latencies)
        avg_tokens_per_sec = (
            sum(self.recent_tokens_per_sec) / len(self.recent_tokens_per_sec)
            if self.recent_tokens_per_sec else 0.0
        )
        
        error_rate = (
            self.error_count / self.total_requests
            if self.total_requests > 0 else 0.0
        )
        
        return {
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "error_rate": error_rate,
            "avg_latency": avg_latency,
            "avg_tokens_per_sec": avg_tokens_per_sec,
            "recent_samples": len(self.recent_latencies)
        }
    
    def reset(self):
        """Reset all metrics (for testing)."""
        self.metrics.clear()
        self.recent_latencies.clear()
        self.recent_tokens_per_sec.clear()
        self.error_count = 0
        self.total_requests = 0
        logger.info("Metrics reset")


# Global metrics instance
metrics_service = MetricsService()

