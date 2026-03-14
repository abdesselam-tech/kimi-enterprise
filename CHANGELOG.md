# Changelog

All notable changes to Kimi Enterprise will be documented in this file.

## [2.0.0] - 2024-03-13

### Added
- Dynamic auto-scaling based on queue depth and predictive load forecasting
- Real-time cost tracking with budget circuit breakers (50%/75%/95% thresholds)
- Git integration with automatic PR creation and conventional commits
- Priority-based message routing with aging prevention
- Anomaly detection for stale agents, cost spikes, and queue growth
- Load balancer for intelligent task assignment
- Enhanced CLI with Rich-based dashboard
- SQLite-backed message bus with guaranteed delivery
- Watchdog with automatic agent recovery
- Multi-tier agent cost model (executive/director/manager/senior/mid/junior)

### Architecture
- Hierarchical multi-agent system (CEO → CTO → VPs → Directors → EMs → ICs)
- MCP (Model Context Protocol) for agent communication
- Separation of concerns: Strategic, Tactical, Operational, Execution layers
- Event sourcing for audit trails

## [1.0.0] - 2024-01-01

### Added
- Initial release with basic multi-agent orchestration
- Simple message bus
- Basic agent personas
- Tmux-based process management

---

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
