# Quick Start Guide

Get up and running with Render Dashboard in 5 minutes!

## Step 1: Install (1 minute)

```bash
cd render-dashboard

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install package
pip install -e .
```

## Step 2: Get API Key (2 minutes)

1. Go to https://dashboard.render.com/u/settings
2. Click "API Keys" → "Create API Key"
3. Copy the key and export it:

```bash
export RENDER_API_KEY="rnd_xxxxxxxxxxxx"
```

Add to `~/.zshrc` or `~/.bashrc` to persist:

```bash
echo 'export RENDER_API_KEY="rnd_xxxxxxxxxxxx"' >> ~/.zshrc
source ~/.zshrc
```

## Step 3: Add Your Services (2 minutes)

Use the interactive service manager to discover and add services:

```bash
# Search for your service (e.g., "api", "chat", "web")
rd service add api

# Follow the prompts:
# 1. Select service if multiple matches
# 2. Enter alias (or press Enter for default)
# 3. Optionally add more aliases
```

The service is automatically added to `config.yaml` - no manual editing needed!

**Add more services:**
```bash
rd service add chat
rd service add auth
```

**View configured services:**
```bash
rd service list
```

## Step 4: Try It!

**Make sure venv is activated:**
```bash
source .venv/bin/activate
```

**TUI Dashboard:**
```bash
rd
```

**CLI Commands:**
```bash
rd api logs      # Opens logs in browser
rd api status    # Shows status in terminal
```

## Common First Commands

```bash
# View all services (TUI)
rd

# Quick status check
rd api status

# Open logs
rd api logs

# Open events
rd api events

# List available services if you forget aliases
rd unknown logs  # Shows list of configured services
```

## Tips

1. **Auto-activate venv**: Add to `~/.zshrc` or `~/.bashrc`:
   ```bash
   source /path/to/render-dashboard/.venv/bin/activate
   ```
2. **Keep it running**: Run `rd` in a tmux pane for monitoring
3. **Use aliases**: Set up `alias api-logs='rd api logs'` in your shell
4. **Quick access**: Type `rd ` and let zsh-autosuggestions do the rest

## Need Help?

- Check `README.md` for full documentation
- Issues? Run `rd api status` to verify connection
- Config problems? The error messages tell you exactly what's wrong

---

That's it! You're ready to manage your Render services from the terminal. 🚀
