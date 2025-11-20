"""
Performance Monitoring and Metrics for GeneFlow.

Tracks agent execution metrics, token usage, latency, and quality metrics.
"""

import logging
import time
import psutil
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from dataclasses import dataclass, asdict
import json
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """
    Single point-in-time metric measurement with timestamp and labels.
    
    Attributes:
        timestamp (str): ISO format timestamp
        metric_name (str): Metric identifier
        value (float): Measured value
        labels (Dict[str, str]): Optional classification labels
    
    Methods:
        to_dict: Converts to dictionary for serialization
    """
    timestamp: str
    metric_name: str
    value: float
    labels: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AgentExecutionMetrics:
    """
    Comprehensive metrics for a single agent execution including timing and costs.
    
    Attributes:
        agent_name (str): Agent identifier
        execution_id (str): Unique execution ID for tracking
        start_time (float): Unix timestamp when execution started
        end_time (float): Unix timestamp when execution completed
        duration_seconds (float): Total execution duration
        tokens_input (int): Input tokens consumed
        tokens_output (int): Output tokens generated
        tokens_total (int): Total tokens used
        cost_estimate (float): Estimated cost in USD
        success (bool): Whether execution completed successfully
        error (str, optional): Error message if failed
        tool_calls (List[str]): Names of tools called
    
    Methods:
        to_dict: Converts to dictionary for serialization and storage
    """
    agent_name: str
    execution_id: str
    start_time: float
    end_time: float
    duration_seconds: float
    tokens_input: int
    tokens_output: int
    tokens_total: int
    cost_estimate: float
    success: bool
    error: Optional[str] = None
    tool_calls: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PerformanceMonitor:
    """
    Real-time performance monitoring and metrics collection for agent execution.
    
    Tracks timing, token usage, costs, and system resources for all agent
    executions. Provides detailed statistics, cost estimation, and metrics export.
    Thread-safe implementation for concurrent agent execution.
    
    Attributes:
        storage_path (Path): Directory for metric persistence
        metrics (List): Collected metric snapshots
        executions (List): Agent execution records
        counters, gauges, timers (Dict): Metric collections
        pricing (Dict): Model-specific token pricing
    
    Methods:
        start_execution: Begin execution tracking
        end_execution: Complete execution tracking  
        get_summary_stats: Generate time-windowed statistics
        get_agent_stats: Retrieve agent-specific metrics
        export_metrics: Save all metrics to file
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path("metrics")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.metrics: List[MetricSnapshot] = []
        self.executions: List[AgentExecutionMetrics] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.timers: Dict[str, List[float]] = defaultdict(list)
        
        self._lock = threading.Lock()
        
        # Define model pricing per million tokens
        self.pricing = {
            "gemini-2.0-flash": {"input": 0.15, "output": 0.60},
            "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
            "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
        }
        
        logger.info(f"PerformanceMonitor initialized with storage: {self.storage_path}")
    
    def start_execution(self, agent_name: str) -> str:
        """Start tracking an agent execution"""
        import uuid
        execution_id = str(uuid.uuid4())
        
        with self._lock:
            self.gauges[f"active_executions_{agent_name}"] = \
                self.gauges.get(f"active_executions_{agent_name}", 0) + 1
        
        return execution_id
    
    def end_execution(
        self,
        agent_name: str,
        execution_id: str,
        start_time: float,
        tokens_input: int,
        tokens_output: int,
        model: str = "gemini-2.0-flash",
        success: bool = True,
        error: str = None,
        tool_calls: List[str] = None
    ):
        """End tracking an agent execution"""
        end_time = time.time()
        duration = end_time - start_time
        
        # Compute execution cost
        cost = self._calculate_cost(model, tokens_input, tokens_output)
        
        metrics = AgentExecutionMetrics(
            agent_name=agent_name,
            execution_id=execution_id,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_input + tokens_output,
            cost_estimate=cost,
            success=success,
            error=error,
            tool_calls=tool_calls or []
        )
        
        with self._lock:
            self.executions.append(metrics)
            self.counters[f"executions_{agent_name}"] += 1
            self.counters[f"tokens_total"] += tokens_input + tokens_output
            self.timers[f"duration_{agent_name}"].append(duration)
            
            if not success:
                self.counters[f"errors_{agent_name}"] += 1
            
            self.gauges[f"active_executions_{agent_name}"] = \
                max(0, self.gauges.get(f"active_executions_{agent_name}", 1) - 1)
        
        # Persist metrics periodically
        if len(self.executions) % 10 == 0:
            self._save_metrics()
    
    def record_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None):
        """Record a custom metric"""
        with self._lock:
            snapshot = MetricSnapshot(
                timestamp=datetime.now().isoformat(),
                metric_name=metric_name,
                value=value,
                labels=labels or {}
            )
            self.metrics.append(snapshot)
    
    def increment_counter(self, counter_name: str, value: int = 1):
        """Increment a counter"""
        with self._lock:
            self.counters[counter_name] += value
    
    def set_gauge(self, gauge_name: str, value: float):
        """Set a gauge value"""
        with self._lock:
            self.gauges[gauge_name] = value
    
    def record_timer(self, timer_name: str, duration: float):
        """Record a timer value"""
        with self._lock:
            self.timers[timer_name].append(duration)
    
    def get_summary_stats(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get summary statistics for the time window"""
        cutoff_time = time.time() - (time_window_hours * 3600)
        
        with self._lock:
            recent_executions = [
                e for e in self.executions
                if e.start_time >= cutoff_time
            ]
            
            if not recent_executions:
                return {
                    "time_window_hours": time_window_hours,
                    "total_executions": 0,
                    "message": "No executions in time window"
                }
            
            total_tokens = sum(e.tokens_total for e in recent_executions)
            total_cost = sum(e.cost_estimate for e in recent_executions)
            successful = sum(1 for e in recent_executions if e.success)
            failed = len(recent_executions) - successful
            
            durations = [e.duration_seconds for e in recent_executions]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Calculate token statistics
            avg_tokens = total_tokens / len(recent_executions)
            
            # Aggregate agent-specific statistics
            agent_stats = defaultdict(lambda: {"count": 0, "tokens": 0, "cost": 0})
            for e in recent_executions:
                agent_stats[e.agent_name]["count"] += 1
                agent_stats[e.agent_name]["tokens"] += e.tokens_total
                agent_stats[e.agent_name]["cost"] += e.cost_estimate
            
            return {
                "time_window_hours": time_window_hours,
                "total_executions": len(recent_executions),
                "successful_executions": successful,
                "failed_executions": failed,
                "success_rate": (successful / len(recent_executions)) * 100,
                "total_tokens": total_tokens,
                "avg_tokens_per_execution": avg_tokens,
                "total_cost_estimate_usd": round(total_cost, 4),
                "avg_duration_seconds": round(avg_duration, 3),
                "min_duration_seconds": round(min_duration, 3),
                "max_duration_seconds": round(max_duration, 3),
                "agent_breakdown": dict(agent_stats),
                "system_metrics": self._get_system_metrics()
            }
    
    def get_agent_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get statistics for a specific agent"""
        with self._lock:
            agent_executions = [e for e in self.executions if e.agent_name == agent_name]
            
            if not agent_executions:
                return {"agent_name": agent_name, "executions": 0}
            
            total_tokens = sum(e.tokens_total for e in agent_executions)
            total_cost = sum(e.cost_estimate for e in agent_executions)
            successful = sum(1 for e in agent_executions if e.success)
            
            durations = [e.duration_seconds for e in agent_executions]
            
            return {
                "agent_name": agent_name,
                "total_executions": len(agent_executions),
                "successful": successful,
                "failed": len(agent_executions) - successful,
                "success_rate": (successful / len(agent_executions)) * 100,
                "total_tokens": total_tokens,
                "total_cost_usd": round(total_cost, 4),
                "avg_duration_seconds": round(sum(durations) / len(durations), 3),
                "min_duration": round(min(durations), 3),
                "max_duration": round(max(durations), 3)
            }
    
    def get_token_usage(self) -> Dict[str, Any]:
        """Get detailed token usage statistics"""
        with self._lock:
            total_input = sum(e.tokens_input for e in self.executions)
            total_output = sum(e.tokens_output for e in self.executions)
            total = total_input + total_output
            
            return {
                "total_tokens": total,
                "input_tokens": total_input,
                "output_tokens": total_output,
                "input_percentage": (total_input / total * 100) if total > 0 else 0,
                "output_percentage": (total_output / total * 100) if total > 0 else 0,
                "estimated_total_cost_usd": round(sum(e.cost_estimate for e in self.executions), 4)
            }
    
    def _calculate_cost(self, model: str, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost estimate for tokens"""
        if model not in self.pricing:
            model = "gemini-2.0-flash"  # Default
        
        pricing = self.pricing[model]
        cost_input = (tokens_input / 1_000_000) * pricing["input"]
        cost_output = (tokens_output / 1_000_000) * pricing["output"]
        
        return cost_input + cost_output
    
    def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            logger.warning(f"Failed to get system metrics: {e}")
            return {}
    
    def _save_metrics(self):
        """Save metrics to disk"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Persist execution metrics to disk
            executions_file = self.storage_path / f"executions_{timestamp}.json"
            with open(executions_file, 'w') as f:
                json.dump([e.to_dict() for e in self.executions[-100:]], f, indent=2)
            
            # Persist summary statistics
            summary_file = self.storage_path / "summary_latest.json"
            with open(summary_file, 'w') as f:
                json.dump(self.get_summary_stats(), f, indent=2)
                
            logger.debug(f"Metrics saved to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    def export_metrics(self, filepath: str = None) -> str:
        """Export all metrics to file"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = str(self.storage_path / f"full_export_{timestamp}.json")
        
        with self._lock:
            data = {
                "exported_at": datetime.now().isoformat(),
                "executions": [e.to_dict() for e in self.executions],
                "metrics": [m.to_dict() for m in self.metrics],
                "counters": dict(self.counters),
                "gauges": self.gauges,
                "summary": self.get_summary_stats()
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        
        logger.info(f"Metrics exported to {filepath}")
        return filepath
