# Quick Start Tutorial

This tutorial will get you up and running with Kimi Enterprise in 5 minutes.

## Step 1: Initialize Your Project

Navigate to your project directory and initialize Kimi Enterprise:

```bash
cd /path/to/your/project

# Initialize with minimal template (2-3 agents)
kimi-enterprise-cli init --name MyProject --template minimal

# Or use the short alias
ke init --name MyProject --template minimal
```

### Template Options

| Template | Agents | Best For | Est. Daily Cost |
|----------|--------|----------|-----------------|
| `minimal` | 2-3 | Solo projects | ~$5-10 |
| `startup` | 8-10 | Small teams | ~$20-30 |
| `full` | 20+ | Enterprise | ~$40-60 |

For your first time, we recommend `minimal` to test the system.

## Step 2: Review Configuration

Check the generated configuration:

```bash
cat .kimi-enterprise/config.json
```

Key settings to review:
- `daily_budget_usd`: Your daily spending limit (default: $50)
- `max_agents`: Maximum concurrent agents
- `scaling.enabled`: Auto-scaling on/off

## Step 3: Start the Enterprise

Launch all agents:

```bash
kimi-enterprise-cli start
```

You'll see output like:
```
🚀 Launching Kimi Enterprise...
✓ Message Bus started
✓ Watchdog started
✓ Agents onboarded

✅ Enterprise operational!
   Project: MyProject
   Dashboard: kimi-enterprise-cli status
   CEO Office: kimi-enterprise-cli ceo
```

## Step 4: Check Status

View the enterprise dashboard:

```bash
kimi-enterprise-cli status
```

This shows:
- Active agents and their status
- Task queue summary
- Budget usage
- System metrics

## Step 5: Enter the War Room

Enter the CEO's interactive session:

```bash
kimi-enterprise-cli ceo
```

You're now in a tmux session with the CEO agent. Try commands like:

```
/status                    # Show current status
/delegate "Build auth API" # Delegate a task
/budget                    # Show budget status
```

Press `Ctrl+B D` to detach (agents keep running).

## Step 6: Execute a Task

From outside the war room, dispatch a command:

```bash
kimi-enterprise-cli exec "Create a login page with email and password"
```

The CEO will:
1. Analyze the request
2. Delegate to appropriate teams
3. Track progress
4. Report back

## Step 7: Monitor Progress

Watch the logs:

```bash
# System logs
kimi-enterprise-cli logs

# Specific agent logs
kimi-enterprise-cli logs --agent senior_fe --follow
```

## Step 8: Shutdown

When finished:

```bash
# Graceful shutdown
kimi-enterprise-cli halt

# Emergency halt (kills everything immediately)
kimi-enterprise-cli halt --emergency
```

## What's Next?

- Learn about [configuration options](configuration.md)
- Explore [agent personas](../agents/index.md)
- Understand the [architecture](architecture.md)
- Read [troubleshooting tips](troubleshooting.md)

## Cost Tips

- Start with `minimal` template (~$5-10/day)
- Set conservative budget limits
- Use `ke status` to monitor spend
- Auto-scaling prevents unnecessary costs
- Emergency halt available if needed
