"""
Enhanced Agent Orchestrator with Dynamic Scaling and Load Balancing
"""
import asyncio
import json
import sqlite3
import time
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentInstance:
    """Represents a running agent instance"""
    agent_id: str
    role: str
    department: str
    tier: str
    session_name: str
    pid: Optional[int] = None
    started_at: float = 0
    last_heartbeat: float = 0
    load_factor: float = 0.0
    tasks_completed: int = 0
    status: str = "starting"
    cost_accrued: float = 0.0


@dataclass
class ScalingEvent:
    """Record of a scaling operation"""
    timestamp: float
    direction: str  # "up" or "down"
    reason: str
    agents_affected: List[str]
    queue_depth_before: int
    queue_depth_after: Optional[int] = None


class DynamicOrchestrator:
    """
    Advanced orchestrator with:
    - Predictive load balancing
    - Dynamic auto-scaling
    - Cost-aware scheduling
    - Anomaly detection
    """
    
    def __init__(self, project_root: Path, config):
        self.project = Path(project_root)
        self.var_dir = self.project / ".kimi-enterprise" / "var"
        self.db_path = self.var_dir / "bus.db"
        self.config = config
        self.agents: Dict[str, AgentInstance] = {}
        self.scaling_history: List[ScalingEvent] = []
        self._last_scale_time = 0
        self._load_history: List[Tuple[float, int]] = []  # (timestamp, queue_depth)
        
    def _get_db(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def get_queue_depth(self, status: str = "pending") -> int:
        """Get current queue depth"""
        conn = self._get_db()
        cursor = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE status = ?",
            (status,)
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_queue_forecast(self, minutes_ahead: int = 30) -> int:
        """
        Predict future queue depth using simple trend analysis.
        Returns predicted queue depth.
        """
        if len(self._load_history) < 3:
            return self.get_queue_depth()
        
        # Calculate trend (tasks per minute)
        recent = self._load_history[-10:]  # Last 10 measurements
        if len(recent) < 2:
            return self.get_queue_depth()
        
        time_span = recent[-1][0] - recent[0][0]
        if time_span < 60:  # Need at least 1 minute of data
            return self.get_queue_depth()
        
        queue_change = recent[-1][1] - recent[0][1]
        trend_per_minute = queue_change / (time_span / 60)
        
        predicted = recent[-1][1] + (trend_per_minute * minutes_ahead)
        return max(0, int(predicted))
    
    def get_active_agents(self) -> List[AgentInstance]:
        """Get all active agents from database"""
        conn = self._get_db()
        cursor = conn.execute(
            "SELECT * FROM agents WHERE status = 'active'"
        )
        agents = []
        for row in cursor.fetchall():
            agents.append(AgentInstance(
                agent_id=row['agent_id'],
                role=row['role'],
                department=row['department'] or "",
                tier=row.get('tier', 'mid'),
                session_name=row['session_name'] or "",
                last_heartbeat=row['last_heartbeat'] or 0,
                load_factor=row['load_factor'] or 0.0,
                status=row['status']
            ))
        conn.close()
        return agents
    
    def calculate_optimal_agent_count(self) -> int:
        """
        Calculate optimal number of agents based on:
        - Current and predicted queue depth
        - Agent capacity (assumed 3 concurrent tasks per agent)
        - Cost constraints
        """
        current_depth = self.get_queue_depth()
        predicted_depth = self.get_queue_forecast(minutes_ahead=30)
        
        # Use the higher of current or predicted
        target_depth = max(current_depth, predicted_depth)
        
        # Assume each agent can handle 3 concurrent tasks efficiently
        tasks_per_agent = 3
        optimal = max(
            self.config.scaling.min_agents,
            (target_depth + tasks_per_agent - 1) // tasks_per_agent
        )
        
        # Apply cost constraints
        current_cost = self.get_current_hourly_cost()
        budget = self.config.costs.hourly_budget_usd
        
        if current_cost >= budget * 0.9:
            # At 90% budget, don't scale up
            current_count = len(self.get_active_agents())
            optimal = min(optimal, current_count)
        
        return min(optimal, self.config.scaling.max_agents)
    
    def get_current_hourly_cost(self) -> float:
        """Calculate current hourly burn rate"""
        agents = self.get_active_agents()
        from ..config import AGENT_TIERS
        
        total = 0.0
        for agent in agents:
            tier = AGENT_TIERS.get(agent.tier, AGENT_TIERS['mid'])
            total += tier.hourly_rate
        
        return total
    
    def get_daily_cost_estimate(self) -> float:
        """Estimate daily cost based on current burn rate"""
        hourly = self.get_current_hourly_cost()
        # Assume 8 active hours per day
        return hourly * 8
    
    def should_scale(self) -> Tuple[bool, str, int]:
        """
        Determine if scaling is needed.
        Returns: (should_scale, direction, target_count)
        """
        if not self.config.scaling.enabled:
            return False, "none", 0
        
        # Check cooldown
        time_since_last_scale = time.time() - self._last_scale_time
        if time_since_last_scale < self.config.scaling.cooldown_minutes * 60:
            return False, "cooldown", 0
        
        current_count = len(self.get_active_agents())
        optimal_count = self.calculate_optimal_agent_count()
        queue_depth = self.get_queue_depth()
        
        # Scale up conditions
        if queue_depth >= self.config.scaling.scale_up_threshold:
            if current_count < optimal_count and current_count < self.config.scaling.max_agents:
                target = min(
                    current_count + self.config.scaling.scale_up_agents,
                    self.config.scaling.max_agents,
                    optimal_count
                )
                return True, "up", target
        
        # Scale down conditions
        if queue_depth <= self.config.scaling.scale_down_threshold:
            if current_count > self.config.scaling.min_agents:
                target = max(
                    current_count - 1,
                    self.config.scaling.min_agents,
                    optimal_count
                )
                return True, "down", target
        
        return False, "balanced", current_count
    
    def execute_scaling(self, direction: str, target_count: int) -> ScalingEvent:
        """Execute scaling operation"""
        current_agents = self.get_active_agents()
        current_count = len(current_agents)
        queue_before = self.get_queue_depth()
        
        affected = []
        
        if direction == "up":
            # Spawn additional agents
            to_add = target_count - current_count
            for i in range(to_add):
                agent_id = self._spawn_dynamic_agent()
                if agent_id:
                    affected.append(agent_id)
        
        elif direction == "down":
            # Remove lowest-priority agents first
            to_remove = current_count - target_count
            # Sort by load factor (remove idle agents first)
            sorted_agents = sorted(current_agents, key=lambda a: a.load_factor)
            for agent in sorted_agents[:to_remove]:
                if self._terminate_agent(agent.agent_id):
                    affected.append(agent.agent_id)
        
        self._last_scale_time = time.time()
        
        event = ScalingEvent(
            timestamp=time.time(),
            direction=direction,
            reason=f"Queue depth: {queue_before}, Optimal: {target_count}",
            agents_affected=affected,
            queue_depth_before=queue_before,
            queue_depth_after=self.get_queue_depth()
        )
        self.scaling_history.append(event)
        
        logger.info(f"Scaling {direction}: {len(affected)} agents affected")
        return event
    
    def _spawn_dynamic_agent(self) -> Optional[str]:
        """Spawn a new dynamic agent based on workload needs"""
        # Analyze what type of agent is needed
        pending_tasks = self._get_pending_tasks_by_type()
        
        # Determine best agent type to spawn
        if pending_tasks.get('frontend', 0) > pending_tasks.get('backend', 0):
            role = 'mid_fe'
            prompt = 'ics/mid-frontend.md'
        else:
            role = 'mid_be'
            prompt = 'ics/mid-backend.md'
        
        # Generate unique ID
        agent_id = f"{role}-dynamic-{int(time.time())}"
        
        # Spawn via CLI
        try:
            subprocess.run([
                "kimi-enterprise-cli", "spawn", agent_id,
                "--prompt", prompt,
                "--dynamic"
            ], cwd=str(self.project), check=True, capture_output=True)
            return agent_id
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to spawn dynamic agent: {e}")
            return None
    
    def _terminate_agent(self, agent_id: str) -> bool:
        """Gracefully terminate an agent"""
        try:
            # Send termination signal via message bus
            conn = self._get_db()
            conn.execute(
                "INSERT INTO messages (sender, recipient, msg_type, payload) VALUES (?, ?, ?, ?)",
                ("orchestrator", agent_id, "directive", 
                 json.dumps({"action": "graceful_shutdown", "reason": "scaling_down"}))
            )
            conn.commit()
            conn.close()
            
            # Give 30 seconds to finish current task
            time.sleep(30)
            
            # Force kill if still active
            conn = self._get_db()
            conn.execute(
                "UPDATE agents SET status = 'inactive' WHERE agent_id = ?",
                (agent_id,)
            )
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Failed to terminate agent {agent_id}: {e}")
            return False
    
    def _get_pending_tasks_by_type(self) -> Dict[str, int]:
        """Analyze pending tasks by category"""
        conn = self._get_db()
        cursor = conn.execute(
            "SELECT payload FROM tasks WHERE status = 'pending'"
        )
        
        counts = {"frontend": 0, "backend": 0, "devops": 0, "qa": 0, "other": 0}
        
        for row in cursor.fetchall():
            try:
                payload = json.loads(row[0]) if row[0] else {}
                task_type = payload.get('type', 'other')
                if task_type in counts:
                    counts[task_type] += 1
                else:
                    counts['other'] += 1
            except:
                counts['other'] += 1
        
        conn.close()
        return counts
    
    def detect_anomalies(self) -> List[Dict]:
        """Detect anomalies in system behavior"""
        anomalies = []
        
        # Check for agents with no heartbeat
        conn = self._get_db()
        stale_threshold = time.time() - 300  # 5 minutes
        cursor = conn.execute(
            "SELECT agent_id FROM agents WHERE status = 'active' AND last_heartbeat < ?",
            (stale_threshold,)
        )
        stale = [row[0] for row in cursor.fetchall()]
        
        if stale:
            anomalies.append({
                "type": "stale_agents",
                "severity": "high",
                "agents": stale,
                "message": f"{len(stale)} agents have stale heartbeats"
            })
        
        # Check for unusual queue growth
        if len(self._load_history) >= 5:
            recent_depths = [d for _, d in self._load_history[-5:]]
            if all(recent_depths[i] < recent_depths[i+1] for i in range(len(recent_depths)-1)):
                # Queue growing consistently
                anomalies.append({
                    "type": "queue_growth",
                    "severity": "medium",
                    "message": f"Queue growing consistently: {recent_depths[0]} -> {recent_depths[-1]}"
                })
        
        # Check for cost spike
        current_cost = self.get_current_hourly_cost()
        budget = self.config.costs.hourly_budget_usd
        if current_cost > budget * 1.5:
            anomalies.append({
                "type": "cost_spike",
                "severity": "critical",
                "message": f"Cost {current_cost}/hr exceeds budget {budget}/hr by 50%"
            })
        
        conn.close()
        return anomalies
    
    def update_load_history(self):
        """Record current load for trend analysis"""
        self._load_history.append((time.time(), self.get_queue_depth()))
        # Keep only last 100 measurements
        self._load_history = self._load_history[-100:]
    
    def get_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        agents = self.get_active_agents()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": {
                "total": len(agents),
                "by_tier": {},
                "avg_load": sum(a.load_factor for a in agents) / len(agents) if agents else 0
            },
            "queue": {
                "current_depth": self.get_queue_depth(),
                "predicted_30min": self.get_queue_forecast(30)
            },
            "costs": {
                "current_hourly": self.get_current_hourly_cost(),
                "daily_estimate": self.get_daily_cost_estimate(),
                "budget_remaining": self.config.costs.daily_budget_usd - self.get_daily_cost_estimate()
            },
            "scaling": {
                "last_event": self.scaling_history[-1].__dict__ if self.scaling_history else None,
                "events_24h": len([e for e in self.scaling_history 
                                  if e.timestamp > time.time() - 86400])
            },
            "anomalies": self.detect_anomalies()
        }


class LoadBalancer:
    """
    Intelligent task assignment based on:
    - Agent specialization
    - Current load
    - Historical performance
    - Cost efficiency
    """
    
    def __init__(self, orchestrator: DynamicOrchestrator):
        self.orchestrator = orchestrator
    
    def assign_task(self, task: Dict) -> Optional[str]:
        """
        Find the best agent for a task.
        Returns agent_id or None if no suitable agent.
        """
        agents = self.orchestrator.get_active_agents()
        if not agents:
            return None
        
        # Score each agent
        scores = []
        for agent in agents:
            score = self._score_agent_for_task(agent, task)
            scores.append((agent.agent_id, score))
        
        # Sort by score (highest first)
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores[0][0] if scores else None
    
    def _score_agent_for_task(self, agent: AgentInstance, task: Dict) -> float:
        """Score an agent's suitability for a task"""
        score = 100.0
        
        # Penalize high load (avoid overloading)
        score -= agent.load_factor * 50
        
        # Boost for specialization match
        task_type = task.get('type', '')
        if task_type in agent.role or task_type in agent.department:
            score += 30
        
        # Boost for seniority on complex tasks
        complexity = task.get('complexity', 'medium')
        if complexity == 'high' and 'senior' in agent.role:
            score += 20
        elif complexity == 'low' and 'junior' in agent.role:
            score += 10  # Cost-efficient for simple tasks
        
        # Penalize stale heartbeats
        time_since_heartbeat = time.time() - agent.last_heartbeat
        if time_since_heartbeat > 60:
            score -= 20
        
        return max(0, score)
    
    def rebalance_load(self):
        """Redistribute tasks if load is uneven"""
        # Implementation would check for overloaded agents
        # and reassign tasks to underloaded ones
        pass
