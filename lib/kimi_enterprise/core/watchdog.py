"""
Enhanced Enterprise Watchdog with Cost Tracking and Predictive Monitoring
"""
import os
import sys
import time
import json
import sqlite3
import signal
import subprocess
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CostTracker:
    """
    Tracks API costs in real-time with budget enforcement.
    Integrates with Kimi CLI token usage tracking.
    """
    
    def __init__(self, var_dir: Path, config):
        self.var_dir = var_dir
        self.config = config
        self.db_path = var_dir / "costs.db"
        self._init_db()
        self._token_buffer: List[Dict] = []
    
    def _init_db(self):
        """Initialize cost tracking database"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS token_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                input_tokens INTEGER DEFAULT 0,
                output_tokens INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0,
                model TEXT DEFAULT 'unknown'
            );
            CREATE INDEX IF NOT EXISTS idx_agent_time ON token_usage(agent_id, timestamp);
            CREATE INDEX IF NOT EXISTS idx_session ON token_usage(session_id);
            
            CREATE TABLE IF NOT EXISTS budget_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                level TEXT NOT NULL,  -- warning, austerity, critical
                message TEXT NOT NULL,
                current_spend REAL,
                budget_limit REAL
            );
            
            CREATE TABLE IF NOT EXISTS agent_costs (
                agent_id TEXT PRIMARY KEY,
                total_input_tokens INTEGER DEFAULT 0,
                total_output_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0,
                last_updated TEXT
            );
        """)
        conn.commit()
        conn.close()
    
    def record_usage(self, agent_id: str, input_tokens: int, 
                     output_tokens: int, model: str = "kimi-default"):
        """Record token usage for an agent"""
        # Calculate cost
        input_cost = (input_tokens / 1000) * self.config.costs.token_cost_per_1k_input
        output_cost = (output_tokens / 1000) * self.config.costs.token_cost_per_1k_output
        total_cost = input_cost + output_cost
        
        # Buffer for batch insert
        self._token_buffer.append({
            'agent_id': agent_id,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_usd': total_cost,
            'model': model,
            'timestamp': datetime.now().isoformat()
        })
        
        # Flush buffer every 10 records
        if len(self._token_buffer) >= 10:
            self._flush_buffer()
    
    def _flush_buffer(self):
        """Write buffered records to database"""
        if not self._token_buffer:
            return
        
        conn = sqlite3.connect(self.db_path)
        for record in self._token_buffer:
            conn.execute("""
                INSERT INTO token_usage 
                (agent_id, input_tokens, output_tokens, cost_usd, model, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record['agent_id'],
                record['input_tokens'],
                record['output_tokens'],
                record['cost_usd'],
                record['model'],
                record['timestamp']
            ))
            
            # Update agent totals
            conn.execute("""
                INSERT INTO agent_costs (agent_id, total_input_tokens, total_output_tokens, total_cost, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(agent_id) DO UPDATE SET
                    total_input_tokens = total_input_tokens + ?,
                    total_output_tokens = total_output_tokens + ?,
                    total_cost = total_cost + ?,
                    last_updated = ?
            """, (
                record['agent_id'],
                record['input_tokens'],
                record['output_tokens'],
                record['cost_usd'],
                record['timestamp'],
                record['input_tokens'],
                record['output_tokens'],
                record['cost_usd'],
                record['timestamp']
            ))
        
        conn.commit()
        conn.close()
        self._token_buffer = []
    
    def get_current_spend(self, period: str = "day") -> float:
        """Get current spend for specified period"""
        self._flush_buffer()
        
        conn = sqlite3.connect(self.db_path)
        
        if period == "day":
            since = (datetime.now() - timedelta(days=1)).isoformat()
        elif period == "hour":
            since = (datetime.now() - timedelta(hours=1)).isoformat()
        else:
            since = "1970-01-01"
        
        cursor = conn.execute(
            "SELECT SUM(cost_usd) FROM token_usage WHERE timestamp > ?",
            (since,)
        )
        result = cursor.fetchone()[0] or 0
        conn.close()
        return result
    
    def get_spend_by_agent(self, limit: int = 20) -> List[Dict]:
        """Get spending breakdown by agent"""
        self._flush_buffer()
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        cursor = conn.execute("""
            SELECT agent_id, 
                   SUM(input_tokens) as input_tokens,
                   SUM(output_tokens) as output_tokens,
                   SUM(cost_usd) as total_cost,
                   COUNT(*) as request_count
            FROM token_usage 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY agent_id
            ORDER BY total_cost DESC
            LIMIT ?
        """, (limit,))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results
    
    def check_budget_thresholds(self) -> Optional[str]:
        """
        Check if budget thresholds are exceeded.
        Returns action to take: None, "warn", "austerity", "halt"
        """
        daily_spend = self.get_current_spend("day")
        budget = self.config.costs.daily_budget_usd
        
        ratio = daily_spend / budget if budget > 0 else 0
        
        if ratio >= self.config.costs.emergency_halt_threshold:
            return "halt"
        elif ratio >= self.config.costs.austerity_threshold:
            return "austerity"
        elif ratio >= self.config.costs.warning_threshold:
            return "warn"
        
        return None
    
    def record_alert(self, level: str, message: str):
        """Record a budget alert"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO budget_alerts (level, message, current_spend, budget_limit)
            VALUES (?, ?, ?, ?)
        """, (
            level,
            message,
            self.get_current_spend("day"),
            self.config.costs.daily_budget_usd
        ))
        conn.commit()
        conn.close()
    
    def get_cost_report(self) -> Dict:
        """Generate comprehensive cost report"""
        self._flush_buffer()
        
        return {
            "daily_spend": self.get_current_spend("day"),
            "hourly_spend": self.get_current_spend("hour"),
            "budget": self.config.costs.daily_budget_usd,
            "remaining": self.config.costs.daily_budget_usd - self.get_current_spend("day"),
            "utilization": self.get_current_spend("day") / self.config.costs.daily_budget_usd,
            "by_agent": self.get_spend_by_agent(),
            "projected_daily": self.get_current_spend("hour") * 8,  # 8-hour projection
        }


class Watchdog:
    """
    Enhanced health monitoring with cost tracking, 
    predictive alerts, and automatic recovery.
    """
    
    def __init__(self, project_path: str, config):
        self.project = Path(project_path)
        self.config = config
        self.var_dir = self.project / ".kimi-enterprise" / "var"
        self.db_path = self.var_dir / "bus.db"
        self.log_path = self.var_dir / "log" / "watchdog.log"
        self.running = True
        self.cycle_count = 0
        
        # Initialize components
        self.cost_tracker = CostTracker(self.var_dir, config)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [WATCHDOG] %(message)s',
            handlers=[
                logging.FileHandler(self.log_path),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        self.logger.info("Shutting down watchdog...")
        self.cost_tracker._flush_buffer()
        self.running = False
    
    def _get_db(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def check_agent_health(self):
        """Check health of all registered agents"""
        conn = self._get_db()
        
        stale_threshold = time.time() - 300  # 5 minutes
        
        cursor = conn.execute("""
            SELECT agent_id, session_name, last_heartbeat, status, role 
            FROM agents 
            WHERE status = 'active'
        """)
        
        issues = []
        for row in cursor.fetchall():
            agent_id = row['agent_id']
            session = row['session_name']
            last_beat = row['last_heartbeat'] or 0
            
            # Check tmux session
            result = subprocess.run(
                ["tmux", "has-session", "-t", session],
                capture_output=True
            )
            
            if result.returncode != 0:
                issues.append({
                    'agent': agent_id,
                    'issue': 'dead_session',
                    'severity': 'high'
                })
                self.logger.warning(f"{agent_id}: Dead session detected")
                continue
            
            # Check heartbeat staleness
            if last_beat < stale_threshold:
                time_stale = time.time() - last_beat
                issues.append({
                    'agent': agent_id,
                    'issue': 'stale_heartbeat',
                    'severity': 'medium',
                    'details': f"{time_stale:.0f}s stale"
                })
                
                # Send probe
                subprocess.run([
                    "tmux", "send-keys", "-t", session,
                    "C-c", "echo 'WATCHDOG_PING'", "Enter"
                ], capture_output=True)
        
        conn.close()
        return issues
    
    def check_budget_constraints(self) -> List[Dict]:
        """Check and enforce budget constraints"""
        actions = []
        
        threshold_action = self.cost_tracker.check_budget_thresholds()
        
        if threshold_action == "halt":
            self.logger.critical("🚨 BUDGET EXHAUSTED - EMERGENCY HALT")
            self.cost_tracker.record_alert("critical", "Emergency halt triggered")
            actions.append({
                'type': 'emergency_halt',
                'reason': 'Budget exhausted'
            })
            self.trigger_emergency_halt()
            
        elif threshold_action == "austerity":
            self.logger.warning("⚠️ AUSTERITY MODE - Pausing non-essential agents")
            self.cost_tracker.record_alert("austerity", "Austerity mode activated")
            actions.append({
                'type': 'austerity_mode',
                'reason': 'Budget at 75%'
            })
            self.trigger_austerity_mode()
            
        elif threshold_action == "warn":
            self.logger.warning("💰 Budget at 50%")
            self.cost_tracker.record_alert("warning", "Budget at 50% warning")
        
        return actions
    
    def trigger_emergency_halt(self):
        """Emergency shutdown of all non-essential agents"""
        try:
            subprocess.run([
                "kimi-enterprise-cli", "halt", "--emergency"
            ], cwd=str(self.project), check=False)
        except Exception as e:
            self.logger.error(f"Emergency halt failed: {e}")
    
    def trigger_austerity_mode(self):
        """Pause non-essential agents to reduce costs"""
        conn = self._get_db()
        
        # Get non-essential agents (keep executives and senior devs)
        cursor = conn.execute("""
            SELECT agent_id, session_name 
            FROM agents 
            WHERE status = 'active' 
            AND role NOT IN ('ceo', 'cto', 'senior_fe', 'senior_be')
        """)
        
        for row in cursor.fetchall():
            try:
                # Send pause signal
                subprocess.run([
                    "tmux", "send-keys", "-t", row['session_name'],
                    "C-c", "echo 'AUSTERITY_PAUSE'", "Enter"
                ], capture_output=True)
                
                # Update status
                conn.execute(
                    "UPDATE agents SET status = 'paused' WHERE agent_id = ?",
                    (row['agent_id'],)
                )
                self.logger.info(f"Paused {row['agent_id']} for austerity")
            except Exception as e:
                self.logger.error(f"Failed to pause {row['agent_id']}: {e}")
        
        conn.commit()
        conn.close()
    
    def check_disk_space(self):
        """Monitor disk usage and rotate logs if needed"""
        try:
            result = subprocess.run(
                ["df", str(self.var_dir)],
                capture_output=True,
                text=True
            )
            
            # Parse df output
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                usage = lines[1].split()[4].rstrip('%')
                usage_pct = int(usage)
                
                if usage_pct > 90:
                    self.logger.critical(f"Disk usage critical: {usage_pct}%")
                    self.rotate_logs(aggressive=True)
                elif usage_pct > 75:
                    self.logger.warning(f"Disk usage high: {usage_pct}%")
                    self.rotate_logs()
                    
        except Exception as e:
            self.logger.error(f"Disk check failed: {e}")
    
    def rotate_logs(self, aggressive: bool = False):
        """Rotate and compress logs"""
        log_dir = self.var_dir / "log"
        
        try:
            # Compress old logs
            for log_file in log_dir.glob("*.log"):
                if log_file.stat().st_mtime < time.time() - 86400:  # 1 day old
                    subprocess.run([
                        "gzip", str(log_file)
                    ], capture_output=True)
            
            # In aggressive mode, delete old compressed logs
            if aggressive:
                for gz_file in log_dir.glob("*.gz"):
                    if gz_file.stat().st_mtime < time.time() - 604800:  # 1 week old
                        gz_file.unlink()
                        
            self.logger.info("Log rotation completed")
        except Exception as e:
            self.logger.error(f"Log rotation failed: {e}")
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        return {
            "timestamp": datetime.now().isoformat(),
            "cycle": self.cycle_count,
            "agent_health": self.check_agent_health(),
            "costs": self.cost_tracker.get_cost_report(),
            "disk": self.check_disk_space(),
        }
    
    def run(self):
        """Main watchdog loop"""
        self.logger.info(f"🐕 Watchdog started for {self.project.name}")
        self.logger.info(f"   Budget: ${self.config.costs.daily_budget_usd}/day")
        self.logger.info(f"   Max agents: {self.config.scaling.max_agents}")
        
        while self.running:
            try:
                self.cycle_count += 1
                
                # Check agent health
                health_issues = self.check_agent_health()
                if health_issues:
                    for issue in health_issues:
                        self.logger.warning(
                            f"Health issue: {issue['agent']} - {issue['issue']}"
                        )
                
                # Check budget constraints
                budget_actions = self.check_budget_constraints()
                
                # Check disk space every 10 cycles
                if self.cycle_count % 10 == 0:
                    self.check_disk_space()
                
                # Flush cost buffer
                self.cost_tracker._flush_buffer()
                
                # Sleep until next cycle
                time.sleep(30)
                
            except Exception as e:
                self.logger.error(f"Watchdog error: {e}")
                time.sleep(5)


if __name__ == "__main__":
    import argparse
    from ..config import EnterpriseConfig
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True)
    parser.add_argument("--config", help="Path to config file")
    args = parser.parse_args()
    
    config = EnterpriseConfig.load(Path(args.config) if args.config else Path())
    dog = Watchdog(args.project, config)
    dog.run()
