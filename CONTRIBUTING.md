# Contributing to Kimi Enterprise

Thank you for your interest in contributing to Kimi Enterprise!

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/kimi-enterprise.git
cd kimi-enterprise
pip install -e .
```

## Project Structure

```
kimi-enterprise/
├── lib/kimi_enterprise/    # Core Python package
│   ├── cli.py              # Main CLI entry point
│   ├── config.py           # Configuration management
│   ├── core/               # Core orchestration logic
│   └── mcp/                # MCP servers
├── share/prompts/          # Agent system prompts
├── bin/                    # Executable scripts
└── tests/                  # Test suite
```

## Adding New Agent Personas

1. Create a new `.md` file in `share/prompts/<category>/`
2. Follow the existing format with clear:
   - Role definition
   - Chain of command
   - Responsibilities
   - Available tools
   - Prohibited actions

## Code Style

- Python: PEP 8 compliant
- Shell scripts: `shellcheck` clean
- Documentation: Clear, concise, helpful

## Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Update documentation
6. Submit PR with clear description

## Code of Conduct

Be respectful, constructive, and professional in all interactions.
