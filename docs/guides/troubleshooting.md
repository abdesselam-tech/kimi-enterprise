# Troubleshooting

Common issues and solutions for Kimi Enterprise.

## Installation Issues

### "Command not found: kimi-enterprise-cli"

**Problem**: The CLI isn't in your PATH.

**Solutions**:
```bash
# Reload shell
source ~/.bashrc  # or ~/.zshrc

# Check if installed
ls ~/.kimi-enterprise/bin/

# Add manually to PATH
export PATH="$PATH:$HOME/.kimi-enterprise/bin"
```

### "Python 3.9+ required"

**Problem**: Python version is too old.

**Solutions**:
```bash
# Check version
python3 --version

# Install newer Python (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11 python3.11-pip

# Use pyenv
pyenv install 3.11
pyenv global 3.11
```

### "tmux not found"

**Problem**: tmux isn't installed.

**Solutions**:
```bash
# Ubuntu/Debian
sudo apt install tmux

# macOS
brew install tmux

# CentOS/RHEL
sudo yum install tmux
```

## Runtime Issues

### "Enterprise already running"

**Problem**: PID file exists from previous run.

**Solutions**:
```bash
# Check if actually running
ke status

# Force start (removes stale PID)
rm .kimi-enterprise/var/enterprise.pid
ke start

# Or halt and restart
ke halt
ke start
```

### "CEO session not found"

**Problem**: CEO agent isn't running.

**Solutions**:
```bash
# Check enterprise status
ke status

# Restart enterprise
ke halt
ke start

# Check logs
ke logs
```

### "Agents showing as OFFLINE"

**Problem**: Agents crashed or have stale heartbeats.

**Solutions**:
```bash
# Check watchdog logs
tail .kimi-enterprise/var/log/watchdog.log

# Restart specific agent
# (Use tmux to attach and debug)
tmux ls
tmux attach -t ke-project-agentname

# Force restart all
ke halt --emergency
ke start
```

## Cost/Budget Issues

### "Budget exceeded"

**Problem**: Daily budget has been exceeded.

**Solutions**:
```bash
# Check current spend
ke status

# Increase budget (temporary)
# Edit .kimi-enterprise/config.json
# Change daily_budget_usd

# Emergency halt to stop spending
ke halt --emergency
```

### "Austerity mode activated"

**Problem**: Budget reached 75% threshold.

**Solutions**:
```bash
# This is expected behavior
# Non-essential agents are paused

# To resume, either:
# 1. Wait for next day (budget resets)
# 2. Increase budget limit
# 3. Manually resume agents
```

## Database Issues

### "Database is locked"

**Problem**: SQLite database is busy.

**Solutions**:
```bash
# Check for zombie processes
ps aux | grep kimi

# Kill hanging processes
pkill -f kimi-enterprise

# Restart
ke halt
ke start
```

### "Database corrupted"

**Problem**: SQLite database corruption.

**Solutions**:
```bash
# Backup and recreate
mv .kimi-enterprise/var/bus.db .kimi-enterprise/var/bus.db.bak

# Re-initialize (keeps config, resets state)
ke init --name $(jq -r .name kimi.json) --template minimal
```

## Message Bus Issues

### "Messages not being delivered"

**Problem**: Message bus not functioning.

**Solutions**:
```bash
# Check if bus is running
ps aux | grep bus_server

# Check bus logs
tail .kimi-enterprise/var/log/bus.log

# Restart message bus
# (This happens automatically with ke start)
```

### "Circular dependencies"

**Problem**: Agents waiting on each other.

**Solutions**:
```bash
# Check task queue
# Look for tasks with "blocked" status

# Manually unblock via CEO war room
ke ceo
# Then: /unblock task_id
```

## Git Integration Issues

### "GitHub CLI not found"

**Problem**: `gh` command not available.

**Solutions**:
```bash
# Install GitHub CLI
# macOS
brew install gh

# Ubuntu
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
sudo apt update
sudo apt install gh

# Authenticate
gh auth login
```

### "PR creation failed"

**Problem**: Can't create pull requests.

**Solutions**:
```bash
# Check GitHub auth
gh auth status

# Ensure git is configured
git config --global user.name "Your Name"
git config --global user.email "your@email.com"

# Check remote
git remote -v
```

## Performance Issues

### "System running slowly"

**Problem**: Too many agents or high load.

**Solutions**:
```bash
# Check load
ke status

# Reduce max agents
# Edit config.json, lower max_agents

# Halt and restart with fewer agents
ke halt
ke start
```

### "Out of disk space"

**Problem**: Logs consuming too much space.

**Solutions**:
```bash
# Check disk usage
du -sh .kimi-enterprise/var/log/

# Rotate logs manually
rm .kimi-enterprise/var/log/*.gz
find .kimi-enterprise/var/log -name "*.log" -type f -mtime +7 -delete
```

## Debugging

### Enable Debug Logging

```bash
# Set debug mode
export KE_DEBUG=1

# Run command
ke start
```

### Check All Logs

```bash
# System logs
tail -f .kimi-enterprise/var/log/enterprise.log

# Agent logs (specific agent)
tail -f .kimi-enterprise/var/log/agents/ceo.log

# Bus logs
tail -f .kimi-enterprise/var/log/bus.log

# Watchdog logs
tail -f .kimi-enterprise/var/log/watchdog.log
```

### Manual Database Inspection

```bash
# Connect to message bus database
sqlite3 .kimi-enterprise/var/bus.db

# Useful queries
SELECT COUNT(*) FROM messages WHERE status = 'pending';
SELECT * FROM agents WHERE status = 'active';
SELECT * FROM tasks WHERE status = 'in_progress';
.quit
```

## Getting Help

If issues persist:

1. **Check documentation**: [docs/](https://github.com/abdesselam-tech/kimi-enterprise/tree/main/docs)
2. **Search issues**: [GitHub Issues](https://github.com/abdesselam-tech/kimi-enterprise/issues)
3. **Create new issue**: Include logs and reproduction steps
4. **Discussions**: [GitHub Discussions](https://github.com/abdesselam-tech/kimi-enterprise/discussions)

## Emergency Recovery

If everything is broken:

```bash
# 1. Halt everything
ke halt --emergency

# 2. Kill any remaining processes
pkill -f kimi
pkill -f tmux

# 3. Backup and reset
mv .kimi-enterprise/var .kimi-enterprise/var.bak.$(date +%s)

# 4. Re-initialize
ke init --name MyProject --template minimal

# 5. Start fresh
ke start
```
