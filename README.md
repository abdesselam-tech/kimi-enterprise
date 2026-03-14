<div align="center">

# 🏢 Kimi Enterprise v2.0

**Enterprise-grade multi-agent orchestration framework for Kimi CLI**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/abdesselam-tech/kimi-enterprise)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

</div>

Run a complete virtual IT company with AI agents—from CEO to Junior Developers—with proper hierarchy, cost control, auto-scaling, and Git integration.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🏗️ **Hierarchical Organization** | CEO → CTO → VPs → Directors → EMs → ICs with clear chain of command |
| 📈 **Dynamic Auto-Scaling** | Automatically scale agents up/down based on workload and predictive forecasting |
| 💰 **Cost Optimization** | Real-time budget tracking with circuit breakers at 50%/75%/95% thresholds |
| 🔗 **Git Integration** | Automatic PR creation, code review coordination, conventional commits |
| 📊 **Rich Dashboard** | Beautiful CLI dashboard with agent status, costs, and queue metrics |
| 🛡️ **Safety Controls** | Emergency halt, anomaly detection, audit trails, resource limits |
| ⚡ **Priority Messaging** | SQLite-backed message bus with guaranteed delivery and aging prevention |

## 🚀 Quick Start

### Installation

```bash
# Install system-wide
curl -fsSL https://raw.githubusercontent.com/abdesselam-tech/kimi-enterprise/main/install.sh | bash

# Or clone and install manually
git clone https://github.com/abdesselam-tech/kimi-enterprise.git
cd kimi-enterprise
make install
```

### Initialize in Your Project

```bash
cd my-project
kimi-enterprise-cli init --name MyProject --template startup
kimi-enterprise-cli start
kimi-enterprise-cli ceo
```

### Use the Short Alias

```bash
ke init --name MyProject --template full
ke start
ke status
ke ceo
```

## 📁 Organization Templates

| Template | Agents | Best For | Est. Daily Cost |
|----------|--------|----------|-----------------|
| `minimal` | 2-3 | Solo projects, scripts | ~$5-10 |
| `startup` | 8-10 | Small teams, MVPs | ~$20-30 |
| `full` | 20+ | Enterprise projects | ~$40-60 |

## 🏗️ Architecture

```
User (Board of Directors)
    └── CEO (Strategic Oversight)
        ├── CTO (Technical Authority)
        │   ├── VP Engineering (Execution)
        │   │   ├── Director Frontend → EM → {Senior, Mid, Junior} Devs
        │   │   ├── Director Backend → EM → {Senior, Mid, Junior} Devs
        │   │   ├── Director DevOps → EM → {Cloud, Security, SRE}
        │   │   └── Director QA → EM → {Automation, Manual, Performance}
        │   └── VP Architecture (Standards)
        └── VP Product (Vision)
            └── Product Managers, Business Analysts

Auto-Scaler (Background Service)
    ├── Predictive Load Forecasting
    ├── Cost-Aware Scheduling
    └── Anomaly Detection
```

## 🎮 Commands

```bash
# Lifecycle
kimi-enterprise-cli init --name PROJECT --template {minimal,startup,full}
kimi-enterprise-cli start                    # Launch with auto-scaling
kimi-enterprise-cli status                   # Rich dashboard
kimi-enterprise-cli halt [--emergency]       # Graceful/emergency shutdown

# Interaction
kimi-enterprise-cli ceo                      # Enter CEO war room (tmux)
kimi-enterprise-cli exec "Build auth API"    # One-shot command dispatch
kimi-enterprise-cli scale --target 10        # Manual scaling

# Monitoring
kimi-enterprise-cli logs                     # System logs
kimi-enterprise-cli logs --agent senior_fe   # Agent-specific logs
kimi-enterprise-cli logs --follow            # Tail -f mode
```

## 📊 Dashboard Preview

```
🏢 MyProject - Enterprise Status

┌───────────────┬─────────────┬──────────┬──────────┬──────┬───────────┐
│ Agent         │ Role        │ Dept     │ Status   │ Load │ Heartbeat │
├───────────────┼─────────────┼──────────┼──────────┼──────┼───────────┤
│ ceo           │ executive   │ exec     │ 🟢 active│ 25%  │ 12s ago   │
│ cto           │ executive   │ exec     │ 🟢 active│ 30%  │ 8s ago    │
│ senior_fe     │ senior      │ frontend │ 🟢 active│ 75%  │ 5s ago    │
└───────────────┴─────────────┴──────────┴──────────┴──────┴───────────┘

╭───────────────────────────────── Task Queue ───────────────────────────────╮
│ 📥 Backlog: 3  ⚙️ In Progress: 5  🚫 Blocked: 1  ✅ Done: 12                 │
╰────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────── 💰 Budget Status ────────────────────────────╮
│ Budget: $50.00  |  Used: $12.40 (25%)  |  Remaining: $37.60                │
╰────────────────────────────────────────────────────────────────────────────╯
```

## ⚙️ Configuration

Edit `.kimi-enterprise/config.json`:

```json
{
  "scaling": {
    "enabled": true,
    "scale_up_threshold": 10,      // Queue depth to trigger scale-up
    "scale_down_threshold": 2,     // Queue depth to trigger scale-down
    "max_agents": 30,
    "min_agents": 2,
    "cooldown_minutes": 5
  },
  "costs": {
    "daily_budget_usd": 50.0,
    "hourly_budget_usd": 5.0,
    "emergency_halt_threshold": 0.95,  // 95% of budget = halt
    "austerity_threshold": 0.75        // 75% = pause non-essential
  },
  "git": {
    "enabled": true,
    "auto_create_prs": true,
    "branch_prefix": "ke/",
    "commit_message_template": "[KE-{agent}] {message}"
  }
}
```

## 💰 Cost Control

Kimi Enterprise includes multiple safeguards:

1. **Circuit Breakers**
   - 50% budget: Warning notification
   - 75% budget: Austerity mode (pause non-essential agents)
   - 95% budget: Emergency halt (all agents stopped)

2. **Dynamic Scaling**
   - Scale up only when queue depth justifies it
   - Scale down when load decreases
   - Cost-aware scheduling (prefers cheaper agent tiers)

3. **Predictive Forecasting**
   - Analyzes queue trends to preemptively scale
   - Prevents reactive scaling spikes

## 🔒 Safety Features

- **Emergency Halt**: `kimi-enterprise-cli halt --emergency` kills everything
- **Audit Trail**: Immutable SQLite logs of all agent actions
- **Disk Monitoring**: Auto-rotates logs at 75% and 90% disk usage
- **Stale Agent Detection**: Auto-restarts unresponsive agents
- **Resource Limits**: Configurable max agents, budget caps

## 🛠️ Requirements

- Linux/macOS
- Python 3.9+
- tmux
- [Kimi CLI](https://code.kimi.com) (v1.20+)
- (Optional) GitHub CLI (`gh`) for PR automation

## 📁 Project Structure

```
~/.kimi-enterprise/
├── bin/
│   └── kimi-enterprise-cli      # Main entry point
├── lib/kimi_enterprise/
│   ├── cli.py                   # CLI with Rich UI
│   ├── config.py                # Configuration management
│   ├── core/
│   │   ├── orchestrator.py      # Dynamic scaling & load balancing
│   │   ├── watchdog.py          # Health monitoring & cost tracking
│   │   └── git_integration.py   # Git/PR automation
│   └── mcp/
│       └── bus_server.py        # Message bus MCP server
├── share/prompts/               # Agent system prompts
│   ├── c-suite/                 # CEO, CTO, VP personas
│   ├── directors/               # Department heads
│   ├── managers/                # Engineering managers
│   └── ics/                     # Individual contributors
└── var/                         # Runtime state (created at runtime)
```

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📜 License

MIT License - See [LICENSE](LICENSE)

## 🙏 Acknowledgments

- Built for [Kimi CLI](https://code.kimi.com)
- Inspired by multi-agent orchestration research
- Uses [MCP](https://github.com/modelcontextprotocol) for agent communication

---

<div align="center">

**[Documentation](https://github.com/abdesselam-tech/kimi-enterprise#readme)** •
**[Report Bug](https://github.com/abdesselam-tech/kimi-enterprise/issues)** •
**[Request Feature](https://github.com/abdesselam-tech/kimi-enterprise/issues)**

</div>

---

## 💖 Sponsors

Love Kimi Enterprise? [Become a sponsor](https://github.com/sponsors/abdesselam-tech) to help us build the future of AI-driven development!

### 🚀 Founding Sponsors
*Your logo here - [Become a Founding Sponsor](https://github.com/sponsors/abdesselam-tech)*

### 🏢 Enterprise Supporters
*Your logo here - [Become an Enterprise Supporter](https://github.com/sponsors/abdesselam-tech)*

### 💻 Developer Sponsors
*Your name here - [Become a Developer Sponsor](https://github.com/sponsors/abdesselam-tech)*

### ☕ Coffee Supporters
*Your name here - [Buy us a coffee](https://github.com/sponsors/abdesselam-tech)*

---

**[❤️ Sponsor This Project](https://github.com/sponsors/abdesselam-tech)** | See all [sponsor tiers and perks](SPONSORS.md)

