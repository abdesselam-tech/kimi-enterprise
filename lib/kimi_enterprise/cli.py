#!/usr/bin/env python3
"""
Kimi Enterprise CLI - Enhanced Multi-Agent Orchestration
"""
import os
import sys
import json
import time
import sqlite3
import signal
import subprocess
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich import box

console = Console()

# Installation paths
ENTERPRISE_ROOT = Path.home() / ".kimi-enterprise"
SHARE_DIR = ENTERPRISE_ROOT / "share"


class KimiEnterprise:
    """Main enterprise controller with enhanced orchestration"""
    
    def __init__(self):
        self.cwd = Path.cwd()
        self.project_root = self._find_project_root()
        self.is_inside_project = self.project_root is not None
        self._config = None
        
    def _find_project_root(self) -> Optional[Path]:
        """Walk up directory tree to find kimi.json"""
        current = self.cwd
        while current != current.parent:
            if (current / "kimi.json").exists():
                return current
            current = current.parent
        return None
    
    @property
    def config(self):
        """Lazy load configuration"""
        if self._config is None and self.is_inside_project:
            from config import EnterpriseConfig, ProjectConfig
            pc = ProjectConfig(self.project_root)
            self._config = pc.config
        return self._config
    
    def _ensure_installation(self):
        """Verify system installation exists"""
        if not ENTERPRISE_ROOT.exists():
            console.print("[red]❌ System installation not found.[/red]")
            console.print("[dim]Run: curl -fsSL <install-url> | bash[/dim]")
            sys.exit(1)
    
    def init(self, name: Optional[str] = None, template: str = "full", 
             budget: float = 50.0, git: bool = True) -> int:
        """Initialize enterprise in current directory with enhanced options"""
        self._ensure_installation()
        
        if (self.cwd / "kimi.json").exists():
            console.print("[red]❌ Enterprise already initialized here[/red]")
            return 1
        
        project_name = name or self.cwd.name
        
        # Create directory structure
        ke_dir = self.cwd / ".kimi-enterprise"
        for subdir in ["var/agents", "var/tasks", "var/state", "var/log/agents",
                       "config", "prompts", "docs", "archives"]:
            (ke_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # Create configuration
        from config import EnterpriseConfig, CostConfig, ScalingConfig, GitConfig
        
        config = EnterpriseConfig(
            name=project_name,
            template=template,
            costs=CostConfig(daily_budget_usd=budget),
            scaling=ScalingConfig(
                enabled=True,
                max_agents=30 if template == "full" else (10 if template == "startup" else 3)
            ),
            git=GitConfig(enabled=git)
        )
        
        config.save(ke_dir / "config.json")
        
        # Create manifest
        manifest = {
            "name": project_name,
            "version": "2.0.0",
            "template": template,
            "created_at": datetime.now().isoformat(),
            "enterprise_version": "2.0.0",
            "config_path": str(ke_dir / "config.json")
        }
        
        with open(self.cwd / "kimi.json", "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Copy prompts based on template
        self._install_prompts(template)
        
        # Initialize databases
        self._init_databases()
        
        # Setup git hooks if requested
        if git and (self.cwd / ".git").exists():
            self._setup_git_hooks()
        
        console.print(f"[green]✅ Initialized Kimi Enterprise: {project_name}[/green]")
        console.print(f"   Template: [blue]{template}[/blue]")
        console.print(f"   Budget: [yellow]${budget}/day[/yellow]")
        console.print(f"   Auto-scaling: [green]enabled[/green]")
        console.print(f"   Git integration: [{'green' if git else 'red'}]{'enabled' if git else 'disabled'}[/]")
        console.print(f"\n[dim]Start with: kimi-enterprise-cli start[/dim]")
        return 0
    
    def _install_prompts(self, template: str):
        """Copy system prompts to project"""
        src = SHARE_DIR / "prompts"
        dst = self.cwd / ".kimi-enterprise" / "prompts"
        
        template_configs = {
            "minimal": ["c-suite/ceo.md", "ics/senior-frontend.md"],
            "startup": ["c-suite", "directors", "managers", 
                       "ics/senior-frontend.md", "ics/senior-backend.md"],
            "full": None  # Copy all
        }
        
        allowed = template_configs.get(template)
        
        if allowed is None or not src.exists():
            # Copy everything or create minimal
            if src.exists():
                import shutil
                shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            # Selective copy
            for item in allowed:
                s, d = src / item, dst / item
                if s.exists():
                    d.parent.mkdir(parents=True, exist_ok=True)
                    if s.is_dir():
                        import shutil
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        import shutil
                        shutil.copy2(s, d)
    
    def _init_databases(self):
        """Initialize SQLite databases with enhanced schema"""
        var_dir = self.cwd / ".kimi-enterprise" / "var"
        
        # Message Bus DB
        conn = sqlite3.connect(var_dir / "bus.db")
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
                expires_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_recipient_status ON messages(recipient, status);
            
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
            
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                assignee TEXT,
                creator TEXT,
                status TEXT DEFAULT 'backlog',
                priority TEXT DEFAULT 'medium',
                complexity TEXT DEFAULT 'medium',
                created_at TEXT,
                updated_at TEXT,
                completed_at TEXT,
                parent_task INTEGER,
                git_branch TEXT,
                pr_url TEXT,
                FOREIGN KEY (parent_task) REFERENCES tasks(id)
            );
            
            CREATE TABLE IF NOT EXISTS scaling_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                direction TEXT,
                reason TEXT,
                agents_affected TEXT,
                queue_depth_before INTEGER,
                queue_depth_after INTEGER
            );
        """)
        conn.commit()
        conn.close()
        
        console.print("[dim]   ✓ Databases initialized[/dim]")
    
    def _setup_git_hooks(self):
        """Setup git hooks for enterprise integration"""
        hooks_dir = self.cwd / ".git" / "hooks"
        
        # Pre-commit hook to tag commits
        pre_commit = hooks_dir / "pre-commit"
        pre_commit.write_text("""#!/bin/bash
# Kimi Enterprise pre-commit hook
export KE_PROJECT=$(pwd)
""")
        pre_commit.chmod(0o755)
    
    def start(self, template: str = None) -> int:
        """Launch the enterprise with dynamic orchestration"""
        if not self.is_inside_project:
            console.print("[red]❌ Not in a Kimi Enterprise project[/red]")
            return 1
        
        self._ensure_installation()
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        
        # Check if already running
        pid_file = var_dir / "enterprise.pid"
        if pid_file.exists():
            try:
                with open(pid_file) as f:
                    pid = int(f.read().strip())
                os.kill(pid, 0)  # Check if process exists
                console.print("[yellow]⚠️  Enterprise already running (PID: {})[/yellow]".format(pid))
                return 1
            except (OSError, ValueError):
                pid_file.unlink()  # Stale PID file
        
        console.print("[bold blue]🚀 Launching Kimi Enterprise...[/bold blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            
            # Start Message Bus
            task = progress.add_task("[cyan]Starting Message Bus...[/cyan]", total=None)
            self._start_bus()
            time.sleep(1)
            progress.update(task, completed=True)
            
            # Start Watchdog
            task = progress.add_task("[cyan]Starting Watchdog...[/cyan]", total=None)
            self._start_watchdog()
            progress.update(task, completed=True)
            
            # Load and spawn hierarchy
            task = progress.add_task("[cyan]Onboarding Agents...[/cyan]", total=None)
            self._spawn_hierarchy(template)
            progress.update(task, completed=True)
            
            # Start auto-scaler if enabled
            if self.config and self.config.scaling.enabled:
                task = progress.add_task("[cyan]Starting Auto-scaler...[/cyan]", total=None)
                self._start_autoscaler()
                progress.update(task, completed=True)
        
        # Save PID
        with open(pid_file, "w") as f:
            f.write(str(os.getpid()))
        
        console.print(f"\n[green]✅ Enterprise operational![/green]")
        console.print(f"   Project: [bold]{self.project_root.name}[/bold]")
        console.print(f"   Dashboard: [cyan]kimi-enterprise-cli status[/cyan]")
        console.print(f"   CEO Office: [cyan]kimi-enterprise-cli ceo[/cyan]")
        return 0
    
    def _start_bus(self):
        """Start MCP Message Bus"""
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        log_file = var_dir / "log" / "bus.log"
        
        bus_script = ENTERPRISE_ROOT / "lib" / "kimi_enterprise" / "mcp" / "bus_server.py"
        
        proc = subprocess.Popen([
            sys.executable, str(bus_script),
            "--db", str(var_dir / "bus.db"),
            "--port", "8080"
        ], stdout=open(log_file, "a"), stderr=subprocess.STDOUT, 
           start_new_session=True)
        
        with open(var_dir / "bus.pid", "w") as f:
            f.write(str(proc.pid))
    
    def _start_watchdog(self):
        """Start health monitor with cost tracking"""
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        
        watchdog_script = ENTERPRISE_ROOT / "lib" / "kimi_enterprise" / "core" / "watchdog.py"
        
        proc = subprocess.Popen([
            sys.executable, str(watchdog_script),
            "--project", str(self.project_root),
            "--config", str(var_dir / "config.json")
        ], start_new_session=True)
        
        with open(var_dir / "watchdog.pid", "w") as f:
            f.write(str(proc.pid))
    
    def _start_autoscaler(self):
        """Start dynamic auto-scaler"""
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        
        # Autoscaler runs as part of watchdog in this implementation
        console.print("[dim]   Auto-scaler integrated with watchdog[/dim]")
    
    def _spawn_hierarchy(self, template: str = None):
        """Spawn agents in order (C-Suite first)"""
        # Load org chart
        org_file = SHARE_DIR / "org_chart.json"
        
        if not org_file.exists():
            # Spawn minimal set
            self._spawn_agent("ceo", "c-suite/ceo.md", priority=True)
            return
        
        with open(org_file) as f:
            org = json.load(f)
        
        used_template = template or self.config.template if self.config else "full"
        
        # Get agents for template
        if used_template in org.get("templates", {}):
            agent_list = org["templates"][used_template]
            if agent_list is None:
                agent_list = list(org["agents"].keys())
        else:
            agent_list = list(org["agents"].keys())
        
        # Spawn in hierarchy order
        for level in org.get("hierarchy", []):
            for agent_id in level:
                if agent_id in agent_list and agent_id in org["agents"]:
                    config = org["agents"][agent_id]
                    self._spawn_agent(agent_id, config["prompt"], 
                                    priority=(level == org["hierarchy"][0]))
                    time.sleep(0.5)
    
    def _spawn_agent(self, agent_id: str, prompt_path: str, 
                     priority: bool = False, dynamic: bool = False):
        """Spawn individual agent in tmux"""
        session_name = f"ke-{self.project_root.name}-{agent_id}"
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        prompt_full = self.project_root / ".kimi-enterprise" / "prompts" / prompt_path
        
        # Fallback prompt if specific one doesn't exist
        if not prompt_full.exists():
            prompt_full = self.project_root / ".kimi-enterprise" / "prompts" / "ics/generic.md"
            if not prompt_full.exists():
                # Create minimal generic prompt
                prompt_full.parent.mkdir(parents=True, exist_ok=True)
                prompt_full.write_text("# Generic Agent\nYou are a helpful AI assistant.\n")
        
        # Create workspace
        agent_dir = var_dir / "agents" / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare environment
        env = os.environ.copy()
        env.update({
            "KE_PROJECT": str(self.project_root),
            "KE_AGENT_ID": agent_id,
            "KE_BUS_DB": str(var_dir / "bus.db"),
            "KE_PROMPT": str(prompt_full),
            "KE_DYNAMIC": "1" if dynamic else "0"
        })
        
        # Build kimi command
        kimi_cmd = f"kimi --session {agent_id} --system-prompt {prompt_full}"
        
        # Launch in tmux
        cmd = [
            "tmux", "new-session", "-d", "-s", session_name,
            "-c", str(self.project_root),
            f"export KE_AGENT_ID={agent_id}; {kimi_cmd} 2>&1 | tee {agent_dir}/session.log"
        ]
        
        try:
            subprocess.run(cmd, env=env, check=True, capture_output=True)
            
            # Register in DB
            conn = sqlite3.connect(var_dir / "bus.db")
            conn.execute("""
                INSERT OR REPLACE INTO agents 
                (agent_id, role, status, session_name, last_heartbeat)
                VALUES (?, ?, 'active', ?, ?)
            """, (agent_id, agent_id.split("-")[0] if "-" in agent_id else "staff", 
                  session_name, time.time()))
            conn.commit()
            conn.close()
            
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Failed to spawn {agent_id}: {e}[/red]")
    
    def ceo(self) -> int:
        """Enter CEO war room"""
        if not self.is_inside_project:
            console.print("[red]❌ Not in an enterprise project[/red]")
            return 1
        
        session_name = f"ke-{self.project_root.name}-ceo"
        
        result = subprocess.run(["tmux", "has-session", "-t", session_name], 
                              capture_output=True)
        if result.returncode != 0:
            console.print("[red]❌ CEO session not found. Is the enterprise running?[/red]")
            return 1
        
        console.print("[bold blue]🏢 Entering CEO War Room...[/bold blue]")
        console.print("[dim]Commands: /status, /delegate, /budget, /halt[/dim]\n")
        
        os.execvp("tmux", ["tmux", "attach", "-t", session_name])
    
    def status(self, detailed: bool = False) -> int:
        """Show comprehensive enterprise dashboard"""
        if not self.is_inside_project:
            console.print("[red]❌ Not in an enterprise project[/red]")
            return 1
        
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        if not (var_dir / "bus.db").exists():
            console.print("[red]❌ Enterprise not initialized[/red]")
            return 1
        
        # Load manifest
        with open(self.project_root / "kimi.json") as f:
            manifest = json.load(f)
        
        conn = sqlite3.connect(var_dir / "bus.db")
        conn.row_factory = sqlite3.Row
        
        # Header
        console.print(f"\n[bold blue]🏢 {manifest['name']}[/bold blue] [dim]- Enterprise Status[/dim]\n")
        
        # Agent table
        table = Table(box=box.ROUNDED)
        table.add_column("Agent", style="cyan", no_wrap=True)
        table.add_column("Role", style="green")
        table.add_column("Dept", style="blue")
        table.add_column("Status", justify="center")
        table.add_column("Load", justify="right")
        table.add_column("Heartbeat", justify="right")
        
        cursor = conn.execute("""
            SELECT agent_id, role, department, status, load_factor, last_heartbeat 
            FROM agents ORDER BY department, role
        """)
        
        now = time.time()
        for row in cursor.fetchall():
            agent, role, dept, status, load, heartbeat = row
            
            # Status emoji
            if status == "active":
                status_str = "🟢 active"
            elif status == "paused":
                status_str = "⏸️ paused"
            else:
                status_str = "⚪ " + status
            
            # Heartbeat freshness
            if heartbeat:
                age = now - heartbeat
                if age < 60:
                    hb_str = f"{age:.0f}s ago"
                elif age < 3600:
                    hb_str = f"{age/60:.0f}m ago"
                else:
                    hb_str = "[red]stale[/red]"
            else:
                hb_str = "-"
            
            load_str = f"{load:.0%}" if load else "-"
            
            table.add_row(
                agent[:20],
                role[:15],
                (dept or "-")[:10],
                status_str,
                load_str,
                hb_str
            )
        
        console.print(table)
        
        # Task summary
        cursor = conn.execute("SELECT status, COUNT(*) FROM tasks GROUP BY STATUS")
        tasks = dict(cursor.fetchall())
        
        task_panel = Panel(
            f"[cyan]📥 Backlog:[/cyan] {tasks.get('backlog', 0)}  "
            f"[yellow]⚙️ In Progress:[/yellow] {tasks.get('in_progress', 0)}  "
            f"[red]🚫 Blocked:[/red] {tasks.get('blocked', 0)}  "
            f"[green]✅ Done:[/green] {tasks.get('done', 0)}",
            title="Task Queue",
            border_style="blue"
        )
        console.print(task_panel)
        
        # Cost panel
        cost_conn = sqlite3.connect(var_dir / "costs.db") if (var_dir / "costs.db").exists() else None
        if cost_conn:
            daily_spend = cost_conn.execute(
                "SELECT SUM(cost_usd) FROM token_usage WHERE timestamp > datetime('now', '-1 day')"
            ).fetchone()[0] or 0
            cost_conn.close()
        else:
            daily_spend = 0
        
        budget = self.config.costs.daily_budget_usd if self.config else 50.0
        remaining = budget - daily_spend
        pct = daily_spend / budget if budget > 0 else 0
        
        if pct < 0.5:
            cost_style = "green"
        elif pct < 0.75:
            cost_style = "yellow"
        else:
            cost_style = "red"
        
        cost_panel = Panel(
            f"Budget: [bold]${budget:.2f}[/bold]  |  "
            f"Used: [bold {cost_style}]${daily_spend:.2f} ({pct:.0%})[/bold {cost_style}]  |  "
            f"Remaining: [bold]${remaining:.2f}[/bold]",
            title="💰 Budget Status",
            border_style=cost_style
        )
        console.print(cost_panel)
        
        # Message metrics
        cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'pending'")
        pending_msgs = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM agents WHERE status = 'active'")
        active_agents = cursor.fetchone()[0]
        
        metrics_panel = Panel(
            f"Agents: [bold]{active_agents}[/bold]  |  "
            f"Pending Messages: [bold]{pending_msgs}[/bold]",
            title="📊 System Metrics",
            border_style="dim"
        )
        console.print(metrics_panel)
        
        conn.close()
        return 0
    
    def halt(self, emergency: bool = False) -> int:
        """Shutdown enterprise"""
        if not self.is_inside_project:
            console.print("[red]❌ Not in a project[/red]")
            return 1
        
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        
        if emergency:
            console.print("[bold red]🚨 EMERGENCY HALT[/bold red]")
        else:
            console.print("[yellow]🛑 Graceful shutdown...[/yellow]")
        
        # Kill tmux sessions
        prefix = f"ke-{self.project_root.name}-"
        result = subprocess.run(["tmux", "ls"], capture_output=True, text=True)
        
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith(prefix):
                    session = line.split(":")[0]
                    subprocess.run(["tmux", "kill-session", "-t", session],
                                 capture_output=True)
                    console.print(f"  [dim]Stopped {session}[/dim]")
        
        # Kill MCP servers
        for pid_file in ["bus.pid", "watchdog.pid"]:
            pid_path = var_dir / pid_file
            if pid_path.exists():
                with open(pid_path) as f:
                    try:
                        pid = int(f.read().strip())
                        os.kill(pid, signal.SIGKILL if emergency else signal.SIGTERM)
                    except (ProcessLookupError, ValueError):
                        pass
                pid_path.unlink()
        
        # Update DB
        conn = sqlite3.connect(var_dir / "bus.db")
        conn.execute("UPDATE agents SET status='inactive'")
        conn.commit()
        conn.close()
        
        pid_file = var_dir / "enterprise.pid"
        if pid_file.exists():
            pid_file.unlink()
        
        console.print("[green]✅ Shutdown complete[/green]")
        return 0
    
    def logs(self, agent: Optional[str] = None, follow: bool = False) -> int:
        """View logs"""
        if not self.is_inside_project:
            return 1
        
        log_dir = self.project_root / ".kimi-enterprise" / "var" / "log"
        
        if agent:
            log_file = log_dir / "agents" / f"{agent}.log"
        else:
            log_file = log_dir / "enterprise.log"
        
        if not log_file.exists():
            console.print(f"[red]No logs found: {log_file}[/red]")
            return 1
        
        cmd = ["tail"] + (["-f"] if follow else ["-n", "50"]) + [str(log_file)]
        subprocess.run(cmd)
        return 0
    
    def exec_cmd(self, command: str) -> int:
        """Execute one-shot command via CEO"""
        if not self.is_inside_project:
            return 1
        
        console.print(f"[blue]📤 Dispatching:[/blue] {command}")
        
        # Send message to CEO
        var_dir = self.project_root / ".kimi-enterprise" / "var"
        conn = sqlite3.connect(var_dir / "bus.db")
        conn.execute("""
            INSERT INTO messages (sender, recipient, msg_type, payload, priority)
            VALUES (?, 'ceo', 'directive', ?, 'high')
        """, ("user", json.dumps({"command": command, "timestamp": time.time()})))
        conn.commit()
        conn.close()
        
        console.print("[green]✅ Command dispatched to CEO[/green]")
        console.print("[dim]Use 'kimi-enterprise-cli ceo' to interact[/dim]")
        return 0
    
    def scale(self, target: int = None) -> int:
        """Manual scaling operation"""
        if not self.is_inside_project:
            return 1
        
        console.print("[blue]📊 Scaling operation...[/blue]")
        
        # This would trigger the orchestrator
        # For now, just show current status
        return self.status()


def main():
    parser = argparse.ArgumentParser(
        description="Kimi Enterprise - Multi-agent software company orchestration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  init        Initialize enterprise in current directory
  start       Launch all departments with auto-scaling
  ceo         Enter interactive CEO session
  exec        One-shot command execution
  status      Comprehensive dashboard
  scale       Manual scaling control
  halt        Graceful shutdown
  logs        View logs

Examples:
  kimi-enterprise-cli init --name MyApp --template startup
  kimi-enterprise-cli start
  kimi-enterprise-cli status
  kimi-enterprise-cli exec "Build authentication API"
        """
    )
    
    parser.add_argument("command", choices=[
        "init", "start", "ceo", "exec", "status", "scale", "halt", "logs"
    ])
    parser.add_argument("--name", "-n", help="Project name")
    parser.add_argument("--template", "-t", choices=["minimal", "startup", "full"],
                       default="full")
    parser.add_argument("--budget", "-b", type=float, default=50.0)
    parser.add_argument("--git", action="store_true", default=True)
    parser.add_argument("--emergency", "-e", action="store_true")
    parser.add_argument("--agent", "-a", help="Agent ID for logs")
    parser.add_argument("--follow", "-f", action="store_true")
    parser.add_argument("--target", type=int, help="Target agent count for scale")
    parser.add_argument("args", nargs="*", help="Arguments for exec")
    
    args = parser.parse_args()
    
    ke = KimiEnterprise()
    
    commands = {
        "init": lambda: ke.init(args.name, args.template, args.budget, args.git),
        "start": lambda: ke.start(args.template),
        "ceo": ke.ceo,
        "exec": lambda: ke.exec_cmd(" ".join(args.args)) if args.args else ke.exec_cmd(""),
        "status": ke.status,
        "scale": lambda: ke.scale(args.target),
        "halt": lambda: ke.halt(args.emergency),
        "logs": lambda: ke.logs(args.agent, args.follow),
    }
    
    try:
        sys.exit(commands[args.command]())
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)


if __name__ == "__main__":
    main()
