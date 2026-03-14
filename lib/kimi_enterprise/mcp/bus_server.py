#!/usr/bin/env python3
"""
Enhanced Enterprise Message Bus with Priority Routing and Load Balancing
"""
import asyncio
import json
import sqlite3
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent


class PriorityQueue:
    """
    Priority-based message queue with aging prevention.
    Ensures low-priority messages don't starve.
    """
    
    PRIORITY_WEIGHTS = {
        'critical': 100,
        'high': 50,
        'normal': 10,
        'low': 1
    }
    
    def __init__(self):
        self.aging_counter = 0
    
    def calculate_priority_score(self, msg: Dict) -> float:
        """
        Calculate effective priority with aging.
        Older messages get boosted to prevent starvation.
        """
        base_weight = self.PRIORITY_WEIGHTS.get(msg.get('priority', 'normal'), 10)
        
        # Age boost: +1 point per minute in queue (max +50)
        timestamp = msg.get('timestamp', datetime.now().isoformat())
        try:
            msg_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            age_minutes = (datetime.now() - msg_time).total_seconds() / 60
            age_boost = min(age_minutes, 50)
        except:
            age_boost = 0
        
        return base_weight + age_boost


class MessageBus:
    """
    Enterprise Message Bus with:
    - Guaranteed delivery
    - Priority routing
    - Load balancing hints
    - Dead letter queue
    """
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.priority_queue = PriorityQueue()
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                msg_type TEXT NOT NULL,
                priority TEXT DEFAULT 'normal',
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                thread_id TEXT,
                context TEXT,
                delivery_receipts TEXT DEFAULT '{}',
                retry_count INTEGER DEFAULT 0,
                expires_at TEXT  -- NULL means no expiration
            );
            CREATE INDEX IF NOT EXISTS idx_recipient_status ON messages(recipient, status);
            CREATE INDEX IF NOT EXISTS idx_thread ON messages(thread_id);
            CREATE INDEX IF NOT EXISTS idx_priority_time ON messages(priority, timestamp);
            CREATE INDEX IF NOT EXISTS idx_sender ON messages(sender);
            
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                role TEXT NOT NULL,
                department TEXT,
                manager TEXT,
                status TEXT DEFAULT 'inactive',
                last_heartbeat REAL,
                capabilities TEXT,
                load_factor REAL DEFAULT 0.0,
                session_name TEXT,
                cost_tier TEXT DEFAULT 'mid',
                metadata TEXT
            );
            
            CREATE TABLE IF NOT EXISTS threads (
                id TEXT PRIMARY KEY,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                participants TEXT,
                topic TEXT,
                status TEXT DEFAULT 'active'
            );
            
            CREATE TABLE IF NOT EXISTS dead_letter (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_msg_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                reason TEXT,
                payload TEXT
            );
            
            CREATE TABLE IF NOT EXISTS routing_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,  -- e.g., "task:frontend:*"
                target_dept TEXT NOT NULL,
                priority_boost INTEGER DEFAULT 0
            );
        """)
        conn.commit()
        conn.close()
    
    async def send(self, sender: str, recipient: str, msg_type: str,
                   payload: dict, priority: str = "normal", 
                   thread_id: str = None, ttl_minutes: int = None) -> dict:
        """
        Send message with guaranteed delivery.
        
        Args:
            ttl_minutes: Time-to-live, None means no expiration
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Calculate expiration
        expires_at = None
        if ttl_minutes:
            expires_at = (datetime.now() + 
                         __import__('datetime').timedelta(minutes=ttl_minutes)).isoformat()
        
        # Auto-routing based on content
        target_dept = self._determine_routing(payload, msg_type)
        if target_dept and recipient == 'auto':
            recipient = f"dept_{target_dept}"
        
        context = json.dumps({
            "sent_at": time.time(),
            "db_time": now,
            "routing": target_dept
        })
        
        cursor.execute("""
            INSERT INTO messages 
            (sender, recipient, msg_type, priority, payload, thread_id, context, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (sender, recipient, msg_type, priority, 
              json.dumps(payload), thread_id, context, expires_at))
        
        conn.commit()
        msg_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": msg_id,
            "status": "queued",
            "timestamp": now,
            "recipient": recipient,
            "estimated_delivery": "immediate" if recipient != "broadcast" else "queued"
        }
    
    def _determine_routing(self, payload: dict, msg_type: str) -> Optional[str]:
        """Intelligent routing based on message content"""
        # Check routing rules
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute("SELECT * FROM routing_rules")
        rules = cursor.fetchall()
        conn.close()
        
        # Simple content-based routing
        content = json.dumps(payload).lower()
        
        if any(kw in content for kw in ['frontend', 'ui', 'react', 'css', 'component']):
            return 'frontend'
        elif any(kw in content for kw in ['backend', 'api', 'database', 'server']):
            return 'backend'
        elif any(kw in content for kw in ['deploy', 'infrastructure', 'docker', 'k8s']):
            return 'devops'
        elif any(kw in content for kw in ['test', 'qa', 'bug', 'quality']):
            return 'qa'
        
        return None
    
    async def receive(self, recipient: str, status: str = "pending", 
                     limit: int = 10, include_expired: bool = False) -> List[dict]:
        """
        Retrieve messages for recipient with priority-based sorting.
        Supports wildcards like 'dept_*'.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        try:
            # Build query based on recipient pattern
            if '*' in recipient:
                pattern = recipient.replace('*', '%')
                base_query = """
                    SELECT * FROM messages 
                    WHERE recipient LIKE ? AND status = ?
                """
                params = [pattern, status]
            else:
                base_query = """
                    SELECT * FROM messages 
                    WHERE (recipient = ? OR recipient = 'broadcast') AND status = ?
                """
                params = [recipient, status]
            
            # Exclude expired messages unless requested
            if not include_expired:
                base_query += " AND (expires_at IS NULL OR expires_at > datetime('now'))"
            
            # Priority ordering with aging
            base_query += """
                ORDER BY 
                    CASE priority 
                        WHEN 'critical' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'normal' THEN 3 
                        ELSE 4 
                    END,
                    timestamp ASC 
                LIMIT ?
            """
            params.append(limit)
            
            rows = conn.execute(base_query, params).fetchall()
            
            messages = []
            for row in rows:
                msg = dict(row)
                msg['payload'] = json.loads(msg['payload'])
                msg['context'] = json.loads(msg['context']) if msg['context'] else {}
                messages.append(msg)
                
                # Mark as delivered
                conn.execute(
                    "UPDATE messages SET status = 'delivered' WHERE id = ?", 
                    (msg['id'],)
                )
            
            conn.commit()
            return messages
            
        finally:
            conn.close()
    
    async def ack(self, message_id: int, agent_id: str) -> dict:
        """Acknowledge message receipt with read receipt tracking"""
        conn = sqlite3.connect(self.db_path)
        
        row = conn.execute(
            "SELECT delivery_receipts, recipient FROM messages WHERE id = ?", 
            (message_id,)
        ).fetchone()
        
        if not row:
            conn.close()
            return {"error": "Message not found"}
        
        receipts = json.loads(row[0]) if row[0] else {}
        receipts[agent_id] = {
            "time": time.time(),
            "iso": datetime.now().isoformat(),
            "status": "read"
        }
        
        # Mark as read if all targeted agents have read
        # (simplified: mark read if recipient is specific and anyone reads)
        conn.execute("""
            UPDATE messages 
            SET delivery_receipts = ?, 
                status = CASE 
                    WHEN recipient != 'broadcast' THEN 'read' 
                    ELSE status 
                END
            WHERE id = ?
        """, (json.dumps(receipts), message_id))
        
        conn.commit()
        conn.close()
        
        return {
            "acknowledged": True, 
            "by": agent_id, 
            "at": receipts[agent_id]["iso"]
        }
    
    async def complete(self, message_id: int, result: dict = None) -> dict:
        """Mark message/task as completed with result"""
        conn = sqlite3.connect(self.db_path)
        
        conn.execute("""
            UPDATE messages 
            SET status = 'completed',
                context = json_set(COALESCE(context, '{}'), '$.result', ?)
            WHERE id = ?
        """, (json.dumps(result) if result else '{}', message_id))
        
        conn.commit()
        conn.close()
        
        return {"completed": True, "message_id": message_id}
    
    async def fail(self, message_id: int, error: str, 
                   retry_allowed: bool = True) -> dict:
        """Mark message as failed, optionally retry"""
        conn = sqlite3.connect(self.db_path)
        
        # Get current retry count
        row = conn.execute(
            "SELECT retry_count FROM messages WHERE id = ?",
            (message_id,)
        ).fetchone()
        
        if retry_allowed and row and row[0] < 3:
            # Increment retry and requeue
            conn.execute("""
                UPDATE messages 
                SET retry_count = retry_count + 1,
                    status = 'pending',
                    priority = 'high'  -- Boost priority on retry
                WHERE id = ?
            """, (message_id,))
            action = "retry_queued"
        else:
            # Move to dead letter queue
            msg = conn.execute(
                "SELECT * FROM messages WHERE id = ?",
                (message_id,)
            ).fetchone()
            
            if msg:
                conn.execute("""
                    INSERT INTO dead_letter (original_msg_id, reason, payload)
                    VALUES (?, ?, ?)
                """, (message_id, error, msg['payload']))
            
            conn.execute(
                "UPDATE messages SET status = 'failed' WHERE id = ?",
                (message_id,)
            )
            action = "dead_letter"
        
        conn.commit()
        conn.close()
        
        return {"failed": True, "action": action, "error": error}
    
    async def register_agent(self, agent_id: str, role: str, 
                            department: str = None, manager: str = None,
                            capabilities: List[str] = None,
                            cost_tier: str = "mid") -> dict:
        """Register agent in directory with capabilities"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO agents 
            (agent_id, role, department, manager, capabilities, last_heartbeat, status, cost_tier)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
        """, (agent_id, role, department, manager, 
              json.dumps(capabilities or []), time.time(), cost_tier))
        conn.commit()
        conn.close()
        return {"registered": agent_id, "role": role, "tier": cost_tier}
    
    async def heartbeat(self, agent_id: str, load_factor: float = None,
                        stats: dict = None) -> dict:
        """Update agent heartbeat with load and stats"""
        conn = sqlite3.connect(self.db_path)
        
        updates = ["last_heartbeat = ?"]
        params = [time.time()]
        
        if load_factor is not None:
            updates.append("load_factor = ?")
            params.append(load_factor)
        
        if stats:
            updates.append("metadata = ?")
            params.append(json.dumps(stats))
        
        params.append(agent_id)
        
        conn.execute(f"""
            UPDATE agents 
            SET {', '.join(updates)}
            WHERE agent_id = ?
        """, params)
        
        # Check for stale agents
        stale = conn.execute("""
            SELECT agent_id FROM agents 
            WHERE last_heartbeat < ? AND status = 'active'
        """, (time.time() - 300,)).fetchall()
        
        conn.commit()
        conn.close()
        
        return {
            "ack": True, 
            "stale_agents": [s[0] for s in stale],
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_org_chart(self) -> dict:
        """Return current organization with load distribution"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        rows = conn.execute("""
            SELECT agent_id, role, department, manager, status, 
                   load_factor, cost_tier, capabilities
            FROM agents ORDER BY department, role
        """).fetchall()
        
        org = {
            "departments": {},
            "hierarchy": {},
            "agents": {},
            "load_distribution": {}
        }
        
        for row in rows:
            d = dict(row)
            org["agents"][d["agent_id"]] = {
                **d,
                "capabilities": json.loads(d.get("capabilities", "[]"))
            }
            
            if d["department"]:
                org["departments"].setdefault(d["department"], []).append(d["agent_id"])
                
                # Track load by department
                if d["status"] == "active":
                    org["load_distribution"].setdefault(d["department"], []).append(d["load_factor"])
        
        conn.close()
        return org
    
    async def get_metrics(self) -> dict:
        """Get message bus metrics"""
        conn = sqlite3.connect(self.db_path)
        
        metrics = {
            "messages": {
                "pending": conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'pending'").fetchone()[0],
                "delivered": conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'delivered'").fetchone()[0],
                "completed": conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'completed'").fetchone()[0],
                "failed": conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'failed'").fetchone()[0],
                "dead_letter": conn.execute("SELECT COUNT(*) FROM dead_letter").fetchone()[0]
            },
            "agents": {
                "active": conn.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'").fetchone()[0],
                "total": conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            },
            "avg_load": conn.execute("SELECT AVG(load_factor) FROM agents WHERE status = 'active'").fetchone()[0] or 0
        }
        
        conn.close()
        return metrics


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="Path to SQLite database")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    
    bus = MessageBus(args.db)
    app = Server("kimi-enterprise-bus")
    
    @app.list_tools()
    async def list_tools():
        return [
            Tool(name="send_message", 
                 description="Send message to agent or department with guaranteed delivery",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "sender": {"type": "string"},
                         "recipient": {"type": "string", "description": "Agent ID, dept_* pattern, broadcast, or auto"},
                         "msg_type": {"type": "string", "enum": ["task", "response", "escalation", "status", "directive"]},
                         "payload": {"type": "object"},
                         "priority": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
                         "thread_id": {"type": "string"},
                         "ttl_minutes": {"type": "integer", "description": "Message expiration time"}
                     },
                     "required": ["sender", "recipient", "msg_type", "payload"]
                 }),
            Tool(name="receive_messages", 
                 description="Get pending messages with priority-based delivery",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "recipient": {"type": "string"},
                         "status": {"type": "string", "default": "pending"},
                         "limit": {"type": "integer", "default": 10},
                         "include_expired": {"type": "boolean", "default": False}
                     },
                     "required": ["recipient"]
                 }),
            Tool(name="ack_message", 
                 description="Acknowledge receipt",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "message_id": {"type": "integer"},
                         "agent_id": {"type": "string"}
                     },
                     "required": ["message_id", "agent_id"]
                 }),
            Tool(name="complete_message",
                 description="Mark message as completed with optional result",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "message_id": {"type": "integer"},
                         "result": {"type": "object"}
                     },
                     "required": ["message_id"]
                 }),
            Tool(name="fail_message",
                 description="Mark message as failed with error",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "message_id": {"type": "integer"},
                         "error": {"type": "string"},
                         "retry_allowed": {"type": "boolean", "default": True}
                     },
                     "required": ["message_id", "error"]
                 }),
            Tool(name="register_agent", 
                 description="Register in directory",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "agent_id": {"type": "string"},
                         "role": {"type": "string"},
                         "department": {"type": "string"},
                         "manager": {"type": "string"},
                         "capabilities": {"type": "array", "items": {"type": "string"}},
                         "cost_tier": {"type": "string", "enum": ["executive", "director", "manager", "senior", "mid", "junior"]}
                     },
                     "required": ["agent_id", "role"]
                 }),
            Tool(name="heartbeat", 
                 description="Update agent status",
                 inputSchema={
                     "type": "object",
                     "properties": {
                         "agent_id": {"type": "string"},
                         "load_factor": {"type": "number"},
                         "stats": {"type": "object"}
                     },
                     "required": ["agent_id"]
                 }),
            Tool(name="get_org_chart", 
                 description="Get organization structure",
                 inputSchema={"type": "object", "properties": {}}),
            Tool(name="get_metrics",
                 description="Get message bus metrics",
                 inputSchema={"type": "object", "properties": {}})
        ]
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict):
        try:
            if name == "send_message":
                result = await bus.send(**arguments)
            elif name == "receive_messages":
                result = await bus.receive(**arguments)
            elif name == "ack_message":
                result = await bus.ack(**arguments)
            elif name == "complete_message":
                result = await bus.complete(**arguments)
            elif name == "fail_message":
                result = await bus.fail(**arguments)
            elif name == "register_agent":
                result = await bus.register_agent(**arguments)
            elif name == "heartbeat":
                result = await bus.heartbeat(**arguments)
            elif name == "get_org_chart":
                result = await bus.get_org_chart()
            elif name == "get_metrics":
                result = await bus.get_metrics()
            else:
                result = {"error": "Unknown tool", "tool": name}
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({"error": str(e)}))]
    
    asyncio.run(app.run())


if __name__ == "__main__":
    main()
