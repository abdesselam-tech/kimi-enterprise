# Kimi Enterprise Documentation

Welcome to the Kimi Enterprise documentation! This guide will help you set up and run a complete virtual IT company using AI agents.

## What is Kimi Enterprise?

Kimi Enterprise is an enterprise-grade multi-agent orchestration framework for [Kimi CLI](https://code.kimi.com). It simulates a complete technology organization with proper hierarchy, cost control, auto-scaling, and Git integration.

## Quick Start

```bash
# Install
curl -fsSL https://raw.githubusercontent.com/abdesselam-tech/kimi-enterprise/main/install.sh | bash

# Initialize in your project
cd my-project
kimi-enterprise-cli init --name MyProject --template startup

# Launch
kimi-enterprise-cli start

# Enter CEO war room
kimi-enterprise-cli ceo
```

## Features

- 🏗️ **Hierarchical Organization**: CEO → CTO → VPs → Directors → EMs → ICs
- 📈 **Dynamic Auto-Scaling**: Automatically scale agents based on workload
- 💰 **Cost Optimization**: Real-time budget tracking with circuit breakers
- 🔗 **Git Integration**: Automatic PR creation and code review
- 📊 **Rich Dashboard**: Beautiful CLI with agent status and metrics
- 🛡️ **Safety Controls**: Emergency halt, anomaly detection, audit trails

## Documentation Sections

- [Installation Guide](guides/installation.md)
- [Quick Start Tutorial](guides/quickstart.md)
- [Configuration](guides/configuration.md)
- [Agent Personas](agents/index.md)
- [Architecture](guides/architecture.md)
- [API Reference](api/index.md)
- [Troubleshooting](guides/troubleshooting.md)

## Architecture Overview

```
User (Board of Directors)
    └── CEO (Strategic Oversight)
        ├── CTO (Technical Authority)
        │   ├── VP Engineering (Execution)
        │   │   ├── Director Frontend → EM → ICs
        │   │   ├── Director Backend → EM → ICs
        │   │   ├── Director DevOps → EM → ICs
        │   │   └── Director QA → EM → ICs
        │   └── VP Architecture (Standards)
        └── VP Product (Vision)
```

## Support

- [GitHub Issues](https://github.com/abdesselam-tech/kimi-enterprise/issues)
- [Discussions](https://github.com/abdesselam-tech/kimi-enterprise/discussions)

## License

[MIT License](https://github.com/abdesselam-tech/kimi-enterprise/blob/main/LICENSE)
