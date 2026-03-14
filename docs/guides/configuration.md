# Configuration Guide

Kimi Enterprise is highly configurable. This guide covers all configuration options.

## Configuration File Location

Project-specific configuration:
```
.your-project/
└── .kimi-enterprise/
    └── config.json
```

## Configuration Sections

### 1. Scaling Configuration

Control automatic agent scaling:

```json
{
  "scaling": {
    "enabled": true,
    "scale_up_threshold": 10,
    "scale_down_threshold": 2,
    "max_agents": 30,
    "min_agents": 2,
    "cooldown_minutes": 5,
    "scale_up_agents": 2,
    "enable_predictive_scaling": true
  }
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `enabled` | Enable auto-scaling | `true` |
| `scale_up_threshold` | Queue depth to trigger scale-up | `10` |
| `scale_down_threshold` | Queue depth to trigger scale-down | `2` |
| `max_agents` | Maximum concurrent agents | `30` |
| `min_agents` | Minimum agents to maintain | `2` |
| `cooldown_minutes` | Time between scaling events | `5` |
| `enable_predictive_scaling` | Forecast and preemptively scale | `true` |

### 2. Cost Configuration

Control budget and spending:

```json
{
  "costs": {
    "daily_budget_usd": 50.0,
    "hourly_budget_usd": 5.0,
    "emergency_halt_threshold": 0.95,
    "austerity_threshold": 0.75,
    "warning_threshold": 0.5,
    "token_cost_per_1k_input": 0.01,
    "token_cost_per_1k_output": 0.03
  }
}
```

| Option | Description | Default |
|--------|-------------|---------|
| `daily_budget_usd` | Daily spending limit | `50.0` |
| `hourly_budget_usd` | Hourly spending limit | `5.0` |
| `emergency_halt_threshold` | Halt at % of budget | `0.95` |
| `austerity_threshold` | Austerity mode at % | `0.75` |
| `warning_threshold` | Warning at % | `0.50` |

**Budget Actions:**
- **50%**: Warning notification
- **75%**: Austerity mode (pause non-essential agents)
- **95%**: Emergency halt (all agents stopped)

### 3. Git Configuration

Configure Git integration:

```json
{
  "git": {
    "enabled": true,
    "auto_create_prs": true,
    "pr_template": "enterprise",
    "require_reviews": 1,
    "auto_merge_passing_prs": false,
    "branch_prefix": "ke/",
    "commit_message_template": "[KE-{agent}] {message}"
  }
}
```

### 4. Agent Tiers

Different agent levels have different costs:

| Tier | Hourly Rate | Role Examples |
|------|-------------|---------------|
| `executive` | $2.00 | CEO, CTO |
| `director` | $1.50 | Frontend Director |
| `manager` | $1.00 | EM Frontend |
| `senior` | $0.80 | Senior FE |
| `mid` | $0.50 | Mid-level Dev |
| `junior` | $0.30 | Junior Dev |

## Environment Variables

Override configuration with environment variables:

```bash
export KE_DAILY_BUDGET=100.0
export KE_MAX_AGENTS=50
export KE_SCALING_ENABLED=true
export KE_GIT_ENABLED=true
```

## Per-Project Configuration

Each project can have different settings:

```bash
# Project A - High budget, full team
cd project-a
ke init --template full --budget 100.0

# Project B - Low budget, minimal team
cd project-b
ke init --template minimal --budget 10.0
```

## Runtime Configuration Changes

Some settings can be changed at runtime:

```bash
# Update budget
ke config --budget 75.0

# Enable/disable scaling
ke config --scaling on
ke config --scaling off

# View current config
ke config --show
```

## Configuration Validation

Validate your configuration:

```bash
ke validate
```

This checks:
- All required fields present
- Budget values are positive
- Thresholds are valid (0-1)
- Agent counts make sense (min < max)

## Example Configurations

### Conservative (Low Budget)
```json
{
  "scaling": {
    "enabled": true,
    "max_agents": 5,
    "scale_up_threshold": 20
  },
  "costs": {
    "daily_budget_usd": 20.0,
    "emergency_halt_threshold": 0.90
  }
}
```

### Aggressive (Fast Delivery)
```json
{
  "scaling": {
    "enabled": true,
    "max_agents": 50,
    "scale_up_threshold": 5,
    "cooldown_minutes": 2
  },
  "costs": {
    "daily_budget_usd": 200.0,
    "emergency_halt_threshold": 0.98
  }
}
```

### No Scaling (Fixed Team)
```json
{
  "scaling": {
    "enabled": false
  },
  "costs": {
    "daily_budget_usd": 100.0
  }
}
```
