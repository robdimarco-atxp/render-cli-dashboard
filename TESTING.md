# Testing & Verification Guide

This guide helps you verify that the Render Dashboard is working correctly.

## Installation Test

```bash
# Install in development mode
pip install -e .

# Verify installation
which rd
rd --help  # Should show error about missing arguments, which is expected

# Verify Python can import the module
python -c "import render_dashboard; print(render_dashboard.__version__)"
```

Expected output: `0.1.0`

## Configuration Tests

### Test 1: Config Validation

```bash
# Try without config (should show helpful error)
cd /tmp
rd

# Expected: "No config.yaml found. Please create one..."
```

### Test 2: Missing API Key

Create a test config without API key:

```yaml
# /tmp/config.yaml
render:
  api_key: ""
services:
  - id: "srv-test"
    name: "Test"
    aliases: ["test"]
```

```bash
cd /tmp
rd
# Expected: "Missing render.api_key in config"
```

### Test 3: Valid Config

```bash
cd render-dashboard
cp config.yaml.example config.yaml
# Edit config.yaml with real service IDs and API key
export RENDER_API_KEY="your-key-here"

# Validate by checking status
rd yourservice status
# Expected: Service status output or API error (if service ID is wrong)
```

## CLI Mode Tests

### Test 4: Service Matching

```bash
# Test exact match
rd chat logs
# Expected: Opens browser with logs URL

# Test partial match
rd ch logs
# Expected: Opens browser if "ch" uniquely matches "chat"

# Test ambiguous match (if you have chat-api and chat-web)
rd chat logs
# Expected: Either opens if one matches, or shows disambiguation
```

### Test 5: Invalid Service

```bash
rd nonexistent logs
# Expected: "No service found matching 'nonexistent'"
# Should list available services
```

### Test 6: Invalid Action

```bash
rd chat invalid-action
# Expected: "Invalid action: invalid-action"
# Should list valid actions
```

### Test 7: Status Command (No Browser)

```bash
rd chat status
# Expected: Terminal output with service status, NOT browser opening
# Output should include: status emoji, status text, deploy info
```

### Test 8: All Actions

```bash
# Each should open correct URL in browser
rd chat logs      # https://dashboard.render.com/web/srv-xxx/logs
rd chat events    # https://dashboard.render.com/web/srv-xxx/events
rd chat deploys   # https://dashboard.render.com/web/srv-xxx/deploys
rd chat settings  # https://dashboard.render.com/web/srv-xxx
```

## TUI Mode Tests

### Test 9: Launch TUI

```bash
rd
# Expected: Textual TUI launches with header, service cards, status bar, footer
```

### Test 10: Service Display

In the TUI, verify:
- [ ] Each service shows as a card with border
- [ ] Service name is displayed
- [ ] Status indicator (●/○) is shown with color
- [ ] Service ID is shown in gray
- [ ] Deploy information is shown (time ago + status)
- [ ] Action shortcuts are shown ([L]ogs | [E]vents | [D]eploys | [S]ettings)

### Test 11: Navigation

In the TUI:
- [ ] Press `↓` to move to next service (border should highlight)
- [ ] Press `↑` to move to previous service
- [ ] First service should be focused on launch

### Test 12: Actions (Keyboard)

Focus a service card and press:
- [ ] `L` - Opens logs in browser
- [ ] `E` - Opens events in browser
- [ ] `D` - Opens deploys in browser
- [ ] `S` - Opens settings in browser

Verify correct URLs open for the focused service.

### Test 13: Manual Refresh

In the TUI:
- [ ] Press `R` - Should refresh all services
- [ ] Status bar should update "Updated: 0s ago"
- [ ] Service status should update if changed

### Test 14: Auto-Refresh

In the TUI:
- [ ] Wait 30 seconds (or your configured refresh_interval)
- [ ] Status bar should count up: "Updated: 30s ago"
- [ ] Services should refresh automatically
- [ ] Watch a deploying service - status should update

### Test 15: Status Colors

Verify colors match status:
- [ ] Running service: Green ●
- [ ] Deploying service: Yellow ●
- [ ] Suspended service: Gray ○
- [ ] Failed service: Red ●

### Test 16: Quit

- [ ] Press `Q` - Should exit cleanly
- [ ] No error messages
- [ ] Returns to shell prompt

## API Integration Tests

### Test 17: Valid API Key

```bash
rd yourservice status
# Expected: Successful status fetch with real data
```

### Test 18: Invalid API Key

```bash
export RENDER_API_KEY="invalid-key"
rd yourservice status
# Expected: "Authentication failed. Check your RENDER_API_KEY is correct."
```

### Test 19: Invalid Service ID

Edit config.yaml to have an invalid service ID:

```yaml
services:
  - id: "srv-invalidxxxx"
    name: "Invalid"
    aliases: ["invalid"]
```

```bash
rd invalid status
# Expected: "API error 404: Resource not found" or similar
```

### Test 20: Network Error

```bash
# Disconnect from internet
rd yourservice status
# Expected: "Network error: ..." with descriptive message
```

## Edge Cases

### Test 21: Multiple Config Locations

```bash
# Config in current directory takes precedence
cd render-dashboard
rd
# Should use ./config.yaml

# Config in home directory
mkdir -p ~/.config/render-dashboard
cp config.yaml ~/.config/render-dashboard/
cd /tmp
rd
# Should use ~/.config/render-dashboard/config.yaml
```

### Test 22: Empty Config

```yaml
# config.yaml
render:
  api_key: ${RENDER_API_KEY}
services: []
```

```bash
rd
# Expected: "No services configured. Add at least one service to 'services' list"
```

### Test 23: Deploying Service

If you have a service that's currently deploying:

```bash
rd deploying-service status
# Expected: Status should show "deploying" or "build_in_progress"

rd  # TUI mode
# Expected: Yellow ● indicator and "Deploy started: Xm ago"
```

## Performance Tests

### Test 24: Multiple Services

With 5+ services configured:

```bash
rd
# Expected: TUI loads in < 2 seconds
# All services should appear
```

### Test 25: Concurrent API Calls

In TUI mode with multiple services:
- [ ] Initial load should fetch all services concurrently
- [ ] Should not feel slow even with 10+ services
- [ ] Auto-refresh should be smooth

## Integration Tests

### Test 26: Browser Opening

```bash
rd chat logs
# Verify:
# - [ ] Browser opens
# - [ ] Correct URL is loaded
# - [ ] Terminal shows "Opening logs for Chat Server..."
# - [ ] Terminal shows full URL
```

### Test 27: Browser Failure

If browser can't open:
```bash
# Terminal should still show URL
# User can copy/paste manually
```

## Regression Checklist

Before releasing updates, verify:

- [ ] CLI mode works (rd service action)
- [ ] TUI mode works (rd with no args)
- [ ] Config loading from both locations
- [ ] Environment variable substitution (${RENDER_API_KEY})
- [ ] Service matching (exact, partial, aliases)
- [ ] Browser opening for all actions
- [ ] Status command doesn't open browser
- [ ] Keyboard shortcuts in TUI
- [ ] Auto-refresh in TUI
- [ ] Error messages are helpful
- [ ] Installation via pip install -e .
- [ ] No Python import errors

## Bug Reports

If something doesn't work, please include:

1. Command run: `rd chat logs`
2. Config (sanitized): Remove API key, show structure
3. Error message: Full error output
4. Python version: `python --version`
5. OS: macOS, Linux, etc.
6. Installation method: pip install -e .

---

**All tests passing? You're ready to use Render Dashboard!** 🎉
