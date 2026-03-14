# Installation Guide

This guide covers all methods of installing Kimi Enterprise.

## Prerequisites

Before installing Kimi Enterprise, ensure you have:

- Linux or macOS
- Python 3.9 or higher
- `tmux` installed
- [Kimi CLI](https://code.kimi.com) installed and authenticated
- Git (for Git integration features)
- GitHub CLI (`gh`) - optional, for PR automation

### Checking Prerequisites

```bash
# Check Python version
python3 --version

# Check tmux
tmux -V

# Check Kimi CLI
kimi --version

# Check Git
git --version

# Check GitHub CLI (optional)
gh --version
```

## Method 1: Automated Installation (Recommended)

The easiest way to install Kimi Enterprise:

```bash
curl -fsSL https://raw.githubusercontent.com/abdesselam-tech/kimi-enterprise/main/install.sh | bash
```

This will:
1. Check dependencies
2. Create `~/.kimi-enterprise/` directory
3. Install system files
4. Add `ke` alias to your shell profile

After installation, reload your shell:

```bash
source ~/.bashrc  # or ~/.zshrc
```

## Method 2: Manual Installation

If you prefer manual installation:

```bash
# Clone the repository
git clone https://github.com/abdesselam-tech/kimi-enterprise.git
cd kimi-enterprise

# Install
make install

# Or manually
mkdir -p ~/.kimi-enterprise
cp -r bin lib share ~/.kimi-enterprise/
echo 'export PATH="$PATH:$HOME/.kimi-enterprise/bin"' >> ~/.bashrc
echo 'alias ke="kimi-enterprise-cli"' >> ~/.bashrc
```

## Method 3: Development Installation

For contributing or modifying the code:

```bash
git clone https://github.com/abdesselam-tech/kimi-enterprise.git
cd kimi-enterprise

# Install in development mode
pip install -e .

# Or use the Makefile
make dev-install
```

## Verification

Verify installation:

```bash
# Check command is available
which kimi-enterprise-cli

# Check version
kimi-enterprise-cli --version

# Or use alias
ke --version
```

## Shell Completion (Optional)

Add shell completion for easier usage:

### Bash
```bash
eval "$(_KIMI_ENTERPRISE_COMPLETE=bash_source kimi-enterprise-cli)"
```

### Zsh
```zsh
eval "$(_KIMI_ENTERPRISE_COMPLETE=zsh_source kimi-enterprise-cli)"
```

## Uninstallation

To remove Kimi Enterprise:

```bash
# Remove system directory
rm -rf ~/.kimi-enterprise

# Remove alias from shell profile
sed -i '/kimi-enterprise/d' ~/.bashrc

# If installed via pip
pip uninstall kimi-enterprise
```

## Next Steps

- [Quick Start Tutorial](quickstart.md)
- [Configuration Guide](configuration.md)
