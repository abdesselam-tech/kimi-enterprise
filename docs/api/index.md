# API Reference

Reference for programmatic interaction with Kimi Enterprise.

## Command Line Interface

### Global Options

```bash
kimi-enterprise-cli [GLOBAL_OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--help, -h` | Show help message |
| `--version` | Show version |

### Commands

#### `init`

Initialize enterprise in current directory.

```bash
kimi-enterprise-cli init [OPTIONS]
```

**Options:**

| Option | Default | Description |
|--------|---------|-------------|
| `--name, -n` | Directory name | Project name |
| `--template, -t` | `full` | Template: minimal, startup, full |
| `--budget, -b` | `50.0` | Daily budget in USD |
| `--git` | `true` | Enable Git integration |

**Example:**
```bash
ke init --name MyApp --template startup --budget 30.0
```

#### `start`

Launch the enterprise.

```bash
kimi-enterprise-cli start [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--template` | Override template for this run |

**Example:**
```bash
ke start
```

#### `status`

Show enterprise dashboard.

```bash
kimi-enterprise-cli status [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--detailed, -d` | Show detailed information |

**Output:**
- Agent table (status, load, heartbeat)
- Task queue summary
- Budget status
- System metrics

#### `ceo`

Enter CEO war room (interactive tmux session).

```bash
kimi-enterprise-cli ceo
```

**Interactive Commands:**
- `/status` - Show current status
- `/delegate "task"` - Delegate task
- `/budget` - Show budget
- `/halt` - Emergency halt

Press `Ctrl+B D` to detach.

#### `exec`

Execute one-shot command via CEO.

```bash
kimi-enterprise-cli exec "COMMAND"
```

**Example:**
```bash
ke exec "Create a login page with email and password"
```

#### `scale`

Manual scaling control.

```bash
kimi-enterprise-cli scale [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--target, -t` | Target agent count |

**Example:**
```bash
ke scale --target 10
```

#### `halt`

Shutdown enterprise.

```bash
kimi-enterprise-cli halt [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--emergency, -e` | Emergency halt (force kill) |

**Example:**
```bash
ke halt              # Graceful
ke halt --emergency  # Force kill
```

#### `logs`

View logs.

```bash
kimi-enterprise-cli logs [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--agent, -a` | Agent ID for specific logs |
| `--follow, -f` | Follow log output (tail -f) |

**Examples:**
```bash
ke logs                    # System logs
ke logs --agent ceo        # CEO agent logs
ke logs --follow           # Follow system logs
```

## Python API

### Configuration

```python
from kimi_enterprise.config import EnterpriseConfig, CostConfig, ScalingConfig

# Create configuration
config = EnterpriseConfig(
    name="MyProject",
    template="startup",
    costs=CostConfig(daily_budget_usd=100.0),
    scaling=ScalingConfig(max_agents=20)
)

# Save configuration
config.save(Path("config.json"))

# Load configuration
config = EnterpriseConfig.load(Path("config.json"))
```

### Orchestrator

```python
from kimi_enterprise.core.orchestrator import DynamicOrchestrator

# Initialize
orchestrator = DynamicOrchestrator(project_root, config)

# Get metrics
queue_depth = orchestrator.get_queue_depth()
forecast = orchestrator.get_queue_forecast(minutes_ahead=30)
current_cost = orchestrator.get_current_hourly_cost()

# Check if scaling needed
should_scale, direction, target = orchestrator.should_scale()

# Get health report
report = orchestrator.get_health_report()
```

### Load Balancer

```python
from kimi_enterprise.core.orchestrator import LoadBalancer

# Initialize
lb = LoadBalancer(orchestrator)

# Assign task
task = {"type": "frontend", "complexity": "high"}
agent_id = lb.assign_task(task)
```

### Git Integration

```python
from kimi_enterprise.core.git_integration import GitIntegration

# Initialize
git = GitIntegration(project_root, config)

# Create branch
branch = git.create_branch("senior_fe", "task-123", "add-login-page")

# Commit changes
git.commit_changes("senior_fe", "Add login form", files=["src/Login.tsx"])

# Create PR
pr_url = git.create_pull_request("senior_fe", task, branch)
```

## Database Schema

### Messages Table

```sql
CREATE TABLE messages (
    id INTEGER PRIMARY KEY,
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    sender TEXT NOT NULL,
    recipient TEXT NOT NULL,
    msg_type TEXT NOT NULL,      -- task, response, escalation, directive
    priority TEXT DEFAULT 'normal',  -- low, normal, high, critical
    payload TEXT NOT NULL,       -- JSON
    status TEXT DEFAULT 'pending',   -- pending, delivered, read, completed
    thread_id TEXT,
    delivery_receipts TEXT,      -- JSON
    retry_count INTEGER DEFAULT 0,
    expires_at TEXT
);
```

### Agents Table

```sql
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    role TEXT NOT NULL,
    department TEXT,
    manager TEXT,
    status TEXT DEFAULT 'inactive',  -- active, inactive, paused, error
    last_heartbeat REAL,
    capabilities TEXT,             -- JSON array
    load_factor REAL DEFAULT 0.0,
    session_name TEXT,
    cost_tier TEXT DEFAULT 'mid',  -- executive, director, manager, senior, mid, junior
    metadata TEXT                  -- JSON
);
```

### Tasks Table

```sql
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    assignee TEXT,
    creator TEXT,
    status TEXT DEFAULT 'backlog',  -- backlog, todo, in_progress, blocked, done
    priority TEXT DEFAULT 'medium', -- low, medium, high, critical
    complexity TEXT DEFAULT 'medium', -- low, medium, high
    created_at TEXT,
    updated_at TEXT,
    completed_at TEXT,
    parent_task INTEGER,
    git_branch TEXT,
    pr_url TEXT,
    FOREIGN KEY (parent_task) REFERENCES tasks(id)
);
```

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `KE_PROJECT` | Project root path | `/home/user/project` |
| `KE_AGENT_ID` | Current agent ID | `ceo` |
| `KE_BUS_DB` | Message bus DB path | `/path/to/bus.db` |
| `KE_PROMPT` | System prompt path | `/path/to/prompt.md` |
| `KE_DEBUG` | Enable debug logging | `1` |
| `KE_DAILY_BUDGET` | Override daily budget | `100.0` |
| `KE_MAX_AGENTS` | Override max agents | `50` |

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `130` | Interrupted (Ctrl+C) |
