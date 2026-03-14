# Architecture

This document explains the technical architecture of Kimi Enterprise.

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        User Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   CLI Tool   │  │    CEO War   │  │   GitHub     │      │
│  │              │  │    Room      │  │   Actions    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼─────────────────┼─────────────────┼───────────────┘
          │                 │                 │
┌─────────┼─────────────────┼─────────────────┼───────────────┐
│         │   Orchestration Layer              │               │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────▼───────┐      │
│  │   Dynamic    │  │    Load      │  │     Git      │      │
│  │Orchestrator  │  │   Balancer   │  │ Integration  │      │
│  └──────┬───────┘  └──────────────┘  └──────────────┘      │
└─────────┼───────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │      Communication Layer                          │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Message    │  │    Agent     │  │    Task      │      │
│  │    Bus       │  │  Registry    │  │    Queue     │      │
│  │   (MCP)      │  │              │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │      Agent Layer                                  │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Executive   │  │   Director   │  │      IC      │      │
│  │   (CEO/CTO)  │  │    Level     │  │    Level     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │      Infrastructure Layer                         │
│  ┌──────▼───────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Process    │  │   SQLite     │  │    tmux      │      │
│  │   Manager    │  │  Databases   │  │  Sessions    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Message Bus (MCP Server)

Central communication hub using SQLite for persistence.

**Features:**
- Guaranteed message delivery
- Priority-based routing
- Automatic retry (3 attempts)
- Dead letter queue for failed messages
- Delivery receipts

**Database Schema:**
```sql
messages:
  - id, timestamp, sender, recipient
  - msg_type, priority, payload, status
  - thread_id, delivery_receipts, retry_count

agents:
  - agent_id, role, department, manager
  - status, last_heartbeat, load_factor
```

### 2. Dynamic Orchestrator

Manages agent lifecycle based on workload.

**Responsibilities:**
- Monitor queue depth
- Predict future load (30-minute forecast)
- Scale agents up/down
- Cost-aware scheduling
- Anomaly detection

**Scaling Algorithm:**
1. Calculate current queue depth
2. Predict future depth using trend analysis
3. Determine optimal agent count
4. Apply cost constraints
5. Execute scaling decision

### 3. Load Balancer

Intelligent task assignment.

**Scoring Factors:**
- Current load (penalize busy agents)
- Specialization match (boost relevant skills)
- Seniority (match complexity)
- Heartbeat freshness (avoid stale agents)

### 4. Watchdog

Health monitoring and cost tracking.

**Functions:**
- Agent heartbeat monitoring
- Cost tracking with SQLite
- Budget threshold enforcement
- Automatic recovery
- Disk space monitoring

**Circuit Breakers:**
- 50% budget: Warning
- 75% budget: Austerity mode
- 95% budget: Emergency halt

### 5. Git Integration

Automated source control operations.

**Features:**
- Automatic branch creation
- PR generation with templates
- Conventional commits
- Review assignment
- Merge automation (optional)

## Data Flow

### Task Creation Flow

```
1. User submits task via CEO
2. CEO analyzes and delegates
3. Message Bus routes to VP
4. VP breaks down to Directors
5. Directors assign to EMs
6. EMs task ICs
7. ICs execute and update status
8. Status bubbles up chain
```

### Message Flow

```
Sender → Message Bus → Recipient
   ↓         ↓            ↓
Create    Persist      Notify
Queue     Route        Process
```

## Security Model

### Threat Mitigation

| Threat | Mitigation |
|--------|------------|
| Prompt Injection | Strict system prompts, role enforcement |
| Privilege Escalation | Message Bus enforces routing |
| Data Leakage | File system isolation per agent |
| Cost Attack | Budget limits and rate limiting |

### Audit Trail

All actions logged to SQLite:
- Agent lifecycle events
- Message deliveries
- Cost accruals
- Scaling decisions

## Scalability Limits

### Hard Limits
- **Concurrent Agents**: 30 (Kimi API limit)
- **Context per Agent**: 256K tokens
- **Message Queue**: ~1000 TPS (SQLite)

### Soft Limits
- **Optimal Team Size**: 15-20 agents
- **Task Queue Depth**: 100 (alert at 50)
- **Audit Log**: Rotate monthly

## Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.9+ |
| CLI Framework | Click + Rich |
| Process Management | tmux |
| IPC | MCP (Model Context Protocol) |
| Database | SQLite |
| Configuration | JSON + Pydantic |
| Testing | pytest |

## Deployment Modes

### Local Mode (Default)
- All agents on local machine
- SQLite databases locally
- tmux for process management

### Future: Distributed Mode
- Agents across multiple machines
- Central message bus
- Shared storage
