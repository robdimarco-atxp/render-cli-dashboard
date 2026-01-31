# Config File Loading

The `rdash` command supports multiple ways to specify the configuration file location, with the following priority order:

## Priority Order

1. **Command-line argument** (highest priority)
2. **Environment variable**
3. **Current directory**
4. **Home directory** (lowest priority)

## 1. Command-line Argument

Use the `--config` flag to explicitly specify a config file path:

```bash
rdash --config /path/to/config.yaml chat logs
rdash --config ~/custom-config.yaml service list
```

This works with all commands (CLI mode, service management, and TUI mode):

```bash
# CLI mode
rdash --config ~/config.yaml chat status

# Service management
rdash --config ~/config.yaml service list

# TUI mode (no service specified)
rdash --config ~/config.yaml
```

## 2. Environment Variable

Set the `RENDER_DASHBOARD_CONFIG` environment variable to point to your config file:

```bash
export RENDER_DASHBOARD_CONFIG="$HOME/.config/render-dashboard/config.yaml"
rdash chat logs
```

Add this to your shell profile (`~/.zshrc` or `~/.bashrc`) to make it permanent:

```bash
echo 'export RENDER_DASHBOARD_CONFIG="$HOME/.config/render-dashboard/config.yaml"' >> ~/.zshrc
```

## 3. Current Directory

Place a `config.yaml` file in the directory where you run `rdash`:

```bash
# From /path/to/project
rdash chat logs  # Uses /path/to/project/config.yaml
```

## 4. Home Directory (Default)

If no config is found in the above locations, `rdash` looks for:

```
~/.config/render-dashboard/config.yaml
```

This is the recommended location for system-wide configuration:

```bash
mkdir -p ~/.config/render-dashboard
cp config.yaml ~/.config/render-dashboard/
```

## Example Setups

### Developer Setup (Project-specific config)

For different projects with different services:

```bash
# Project A
cd ~/projects/project-a
cat > config.yaml << EOF
render:
  api_key: \${RENDER_API_KEY}
  refresh_interval: 30
services:
  - id: srv-projecta-service
    name: project-a-api
    aliases: [api, backend]
    priority: 1
EOF

rdash api logs  # Uses ~/projects/project-a/config.yaml
```

### Personal Setup (Single system-wide config)

For managing all your services from anywhere:

```bash
# Set up once
mkdir -p ~/.config/render-dashboard
cat > ~/.config/render-dashboard/config.yaml << EOF
render:
  api_key: \${RENDER_API_KEY}
  refresh_interval: 30
services:
  - id: srv-all-services
    name: my-services
    aliases: [services]
    priority: 1
EOF

# Use from anywhere
cd ~/anywhere
rdash services status
```

### CI/CD Setup (Environment variable)

For automated environments:

```bash
export RENDER_DASHBOARD_CONFIG="/etc/render-dashboard/config.yaml"
rdash chat status
```

## Shell Alias

Since you're using the shell alias from your `~/.zshrc`:

```bash
rdash() {
    (
        source "$HOME/projects/robdimarco/render-dashboard/.venv/bin/activate"
        command rdash "$@"
    )
}
```

All the config loading methods work the same way:

```bash
# Use default config search
rdash chat logs

# Use specific config
rdash --config ~/my-config.yaml chat logs

# Use env var config
export RENDER_DASHBOARD_CONFIG=~/my-config.yaml
rdash chat logs
```
