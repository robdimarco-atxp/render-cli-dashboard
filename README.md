# Render Services Dashboard

A dual-mode terminal tool for managing Render services with both a visual TUI dashboard and lightning-fast CLI commands.

## Features

### 🖥️ TUI Dashboard Mode
- **Real-time monitoring** of all your Render services
- **Auto-refresh** every 30 seconds (configurable)
- **Color-coded status** indicators (running, deploying, suspended, failed)
- **Keyboard navigation** with shortcuts to open logs, events, deploys, and settings
- **Clean, focused interface** built with Textual

### ⚡ CLI Command Mode
- **Lightning-fast access**: `rdash chat logs` opens your chat server logs instantly
- **Smart service matching**: Partial matches and aliases work seamlessly
- **Browser integration**: Opens Render dashboard URLs automatically
- **Quick status checks**: `rdash chat status` shows current status with:
  - Service status with color-coded icons (🟢 available, 🟠 deploying, 🔴 failed)
  - Custom domain URL (or fallback to Render URL)
  - Latest deployment status and time
  - GitHub commit link (commit SHA + full URL)

## Installation

### 1. Clone and Install

```bash
cd /path/to/render-dashboard

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install package in development mode
pip install -e .
```

This creates the `rdash` command in your PATH (within the virtual environment).

**Note:** The command is `rdash` (not `rd`) to avoid conflicts with common shell aliases like `rd` → `rmdir`. No manual PATH setup is needed - the command is automatically available when the venv is activated.

### Optional: Shell Alias for Global Access

To use `rdash` from anywhere without manually activating the virtual environment, add this function to your `~/.zshrc` (or `~/.bashrc` for Bash):

```bash
# Render Dashboard alias
rdash() {
    (
        source "$HOME/path/to/render-dashboard/.venv/bin/activate"
        command rdash "$@"
    )
}
```

**Replace** `$HOME/path/to/render-dashboard` with your actual installation path.

Then reload your shell:
```bash
source ~/.zshrc
```

Now you can run `rdash` from any directory! See [CONFIG_LOADING.md](CONFIG_LOADING.md) for details on how config file discovery works from different directories.

### 2. Get Your Render API Key

1. Go to https://dashboard.render.com/u/settings
2. Click "Account Settings" → "API Keys"
3. Create a new API key
4. Export it in your shell:

```bash
export RENDER_API_KEY="rnd_xxxxxxxxxxxxxxxxxxxx"
```

Add this to your `~/.zshrc` or `~/.bashrc` to persist it.

### 3. Configure Your Services

**Option A: Automatic Discovery (Recommended)**

Use the interactive service manager to discover and add services:

```bash
# Search for a service and add it
rdash service add chat

# It will:
# 1. Search your Render account for services matching "chat"
# 2. Let you select if multiple matches
# 3. Prompt for aliases
# 4. Automatically add to config.yaml
```

**Option B: Manual Configuration**

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` with your service details:

```yaml
render:
  api_key: ${RENDER_API_KEY}
  refresh_interval: 30

services:
  - id: "srv-xxxxxxxxxxxxx"  # From Render dashboard URL
    name: "Chat Server"
    aliases: ["chat", "chat-server"]
    priority: 1
```

**Finding your service IDs manually:**
1. Go to https://dashboard.render.com
2. Click on a service
3. The URL will be: `https://dashboard.render.com/web/srv-xxxxxxxxxxxxx`
4. Copy the `srv-xxxxxxxxxxxxx` part

## Usage

### Service Management Commands

```bash
# Add a service interactively
rdash service add <name>

# List configured services
rdash service list

# Remove a service
rdash service remove <alias>
```

**Examples:**
```bash
# Search and add a service named "chat"
rdash service add chat
# Prompts for aliases, automatically adds to config

# List all configured services
rdash service list

# Remove a service by alias
rdash service remove chat
```

### TUI Dashboard Mode (Interactive)

```bash
rdash
```

**Keyboard shortcuts:**
- `↑/↓` - Navigate between services
- `L` - Open logs for focused service
- `E` - Open events for focused service
- `D` - Open deploys for focused service
- `S` - Open settings for focused service
- `R` - Force refresh all services
- `Q` - Quit

Perfect for keeping open in a tmux pane for at-a-glance monitoring!

### CLI Command Mode (Fast Access)

```bash
rdash <service> <action>
```

**Examples:**
```bash
# Open chat server logs
rdash chat logs

# Open auth server events
rdash auth events

# Show accounts API status (no browser)
rdash accounts status

# Open deploys page
rdash chat deploys

# Partial matching works too
rdash ch logs  # matches "chat" if unique
```

**Available actions:**
- `logs` - Open service logs in browser
- `events` - Open service events in browser
- `deploys` - Open service deploys in browser
- `settings` - Open service settings in browser
- `status` - Show current status in terminal (no browser)

## Shell Integration

### Oh-My-Zsh Autosuggestions

To get great autocomplete support with `zsh-autosuggestions`:

#### Quick Install (Automated)

```bash
cd render-dashboard
./install-zsh-plugin.sh
```

Then add `render-dashboard` to your plugins in `~/.zshrc` and reload:

```bash
# In ~/.zshrc
plugins=(
    git
    zsh-autosuggestions
    render-dashboard  # Add this
)

# Reload shell
source ~/.zshrc
```

#### Manual Install

Create `~/.oh-my-zsh/custom/plugins/render-dashboard/render-dashboard.plugin.zsh`:

```bash
# Create the plugin directory
mkdir -p ~/.oh-my-zsh/custom/plugins/render-dashboard

# Create the plugin file
cat > ~/.oh-my-zsh/custom/plugins/render-dashboard/render-dashboard.plugin.zsh << 'EOF'
# Render Dashboard completion for zsh

# Cache file location
_RD_CACHE_FILE="${HOME}/.cache/render-dashboard-completions"

# Generate completions from config.yaml
_rd_generate_completions() {
    local config_file="${HOME}/.config/render-dashboard/config.yaml"
    [[ ! -f "$config_file" ]] && config_file="./config.yaml"
    [[ ! -f "$config_file" ]] && return

    # Extract service aliases from config
    local aliases=($(grep -A2 "aliases:" "$config_file" | grep -E '^\s*-' | sed 's/.*"\(.*\)".*/\1/' | tr '\n' ' '))

    # Create cache directory
    mkdir -p "$(dirname "$_RD_CACHE_FILE")"

    # Write completions to cache
    {
        for alias in $aliases; do
            echo "rdash $alias logs"
            echo "rdash $alias events"
            echo "rdash $alias deploys"
            echo "rdash $alias settings"
            echo "rdash $alias status"
        done
    } > "$_RD_CACHE_FILE"
}

# Completion function
_rd_completion() {
    local -a commands
    local cache_file="$_RD_CACHE_FILE"

    # Generate cache if missing or config is newer
    local config_file="${HOME}/.config/render-dashboard/config.yaml"
    [[ ! -f "$config_file" ]] && config_file="./config.yaml"

    if [[ ! -f "$cache_file" ]] || [[ "$config_file" -nt "$cache_file" ]]; then
        _rd_generate_completions
    fi

    # Load completions from cache
    if [[ -f "$cache_file" ]]; then
        commands=("${(@f)$(cat "$cache_file")}")
    fi

    _describe 'rdash commands' commands
}

# Register completion
compdef _rd_completion rdash

# Generate initial completions
_rd_generate_completions
EOF
```

#### 2. Enable the plugin

Add `render-dashboard` to your plugins in `~/.zshrc`:

```bash
plugins=(
    git
    zsh-autosuggestions
    render-dashboard  # Add this
    # ... other plugins
)
```

#### 3. Reload your shell

```bash
source ~/.zshrc
```

Now when you type `rdash `, zsh-autosuggestions will suggest your configured service commands based on your history! Type `rdash chat` and it will suggest `rdash chat logs`, `rdash chat events`, etc.

### Bash Completion

For bash users, add this to your `~/.bashrc`:

```bash
_rdash_completion() {
    local cur prev services actions
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Extract service aliases from config
    services=$(grep -A2 "aliases:" config.yaml 2>/dev/null | grep -E '^\s*-' | sed 's/.*"\(.*\)".*/\1/' | tr '\n' ' ')
    actions="logs events deploys settings status"

    if [[ ${COMP_CWORD} -eq 1 ]]; then
        COMPREPLY=($(compgen -W "$services" -- "$cur"))
    elif [[ ${COMP_CWORD} -eq 2 ]]; then
        COMPREPLY=($(compgen -W "$actions" -- "$cur"))
    fi
}

complete -F _rdash_completion rdash
```

## Configuration Reference

```yaml
render:
  # Your Render API key (use env var substitution)
  api_key: ${RENDER_API_KEY}

  # How often to refresh in TUI mode (seconds)
  refresh_interval: 30

services:
  - id: "srv-xxxxx"        # Required: Render service ID
    name: "Chat Server"    # Required: Display name
    aliases: ["chat"]      # Required: CLI aliases (at least one)
    priority: 1            # Optional: Display order (lower = higher)
```

**Configuration file locations** (checked in priority order):
1. `--config <path>` flag (explicit override)
2. `RENDER_DASHBOARD_CONFIG` environment variable
3. `./config.yaml` (current directory)
4. `~/.config/render-dashboard/config.yaml` (user default)

**Examples:**
```bash
# Use specific config file
rdash --config ~/my-config.yaml chat logs

# Use environment variable (good for the shell alias)
export RENDER_DASHBOARD_CONFIG="$HOME/.config/render-dashboard/config.yaml"
rdash chat logs  # Works from any directory

# Use default search (current dir, then ~/.config/render-dashboard/)
rdash chat logs
```

See [CONFIG_LOADING.md](CONFIG_LOADING.md) for comprehensive configuration examples and setup patterns.

## Recommended Workflow

1. **Keep TUI running in tmux**: Monitor all services at a glance
   ```bash
   # In your render-dashboard directory
   source .venv/bin/activate
   tmux new-session -s render
   rdash
   # Ctrl+B, D to detach
   ```

2. **Use CLI for quick actions**: Fast access from any terminal
   ```bash
   # Remember to activate venv first (or add to shell startup)
   source /path/to/render-dashboard/.venv/bin/activate
   rdash chat logs      # Opens in browser instantly
   rdash auth status    # Quick status check
   ```

3. **Global access**: Use the shell alias (recommended) or set up config environment variable
   ```bash
   # Option A: Shell function alias (see Installation section above)
   rdash() {
       (
           source "$HOME/path/to/render-dashboard/.venv/bin/activate"
           command rdash "$@"
       )
   }

   # Option B: Set config location to use from any directory
   export RENDER_DASHBOARD_CONFIG="$HOME/.config/render-dashboard/config.yaml"

   # Then activate venv when needed
   source /path/to/render-dashboard/.venv/bin/activate
   ```

4. **Set up shell aliases** for frequently accessed services:
   ```bash
   # In ~/.zshrc or ~/.bashrc
   alias chat-logs='rdash chat logs'
   alias auth-logs='rdash auth logs'
   ```

## Troubleshooting

### "Authentication failed"
- Check that `RENDER_API_KEY` is set: `echo $RENDER_API_KEY`
- Verify the key is valid at https://dashboard.render.com/u/settings

### "No service found matching..."
- Check your `config.yaml` service IDs and aliases
- Run `rdash` (TUI mode) to see which services are configured
- Verify service IDs at https://dashboard.render.com

### "Config file not found"
- Create `config.yaml` in current directory or `~/.config/render-dashboard/`
- Copy from `config.yaml.example` as a starting point

### TUI not updating
- Check your internet connection
- Verify API key has correct permissions
- Try manual refresh with `R` key

## Architecture

```
render-dashboard/
├── config.yaml              # User configuration
├── render_dashboard/
│   ├── __main__.py         # Entry point (CLI vs TUI routing)
│   ├── cli.py              # CLI command handler
│   ├── config.py           # Config parsing
│   ├── models.py           # Data models
│   ├── api/
│   │   └── render.py       # Async Render API client
│   └── ui/
│       ├── app.py          # Textual TUI app
│       └── widgets.py      # Custom widgets
```

**Key design decisions:**
- **Textual framework**: Native async support perfect for API polling
- **Dual entry point**: Single `rdash` command routes to CLI or TUI
- **Async HTTP**: httpx for efficient concurrent API calls
- **Smart caching**: Service data cached between refreshes

## Future Enhancements

Potential features for future versions:
- [ ] Log streaming in TUI
- [ ] Deploy triggering from TUI
- [ ] Desktop notifications on deploy completion
- [ ] Multiple configuration profiles
- [ ] Service health metrics and graphs
- [ ] Filter services by status
- [ ] Search/filter in TUI

## License

MIT License - feel free to use and modify!

## Contributing

Contributions welcome! Please open an issue or PR.

---

**Made with ❤️ for developers who live in the terminal**
