# Project Structure

```
render-dashboard/
├── README.md                           # Comprehensive documentation
├── QUICKSTART.md                       # 5-minute getting started guide
├── TESTING.md                          # Test scenarios and verification
├── PROJECT_STRUCTURE.md                # This file
├── requirements.txt                    # Python dependencies
├── setup.py                            # Package configuration
├── .gitignore                          # Git ignore rules
│
├── config.yaml.example                 # Example configuration file
│
├── render-dashboard.plugin.zsh         # ZSH completion plugin
├── install-zsh-plugin.sh              # Automated plugin installer
│
└── render_dashboard/                   # Main package
    ├── __init__.py                     # Package initialization
    ├── __main__.py                     # Entry point (CLI/TUI router)
    ├── models.py                       # Data models (Service, Deploy, etc.)
    ├── config.py                       # Configuration loading & validation
    ├── cli.py                          # CLI command mode handler
    │
    ├── api/                            # API client layer
    │   ├── __init__.py
    │   └── render.py                   # Async Render API client
    │
    └── ui/                             # TUI layer
        ├── __init__.py
        ├── app.py                      # Main Textual application
        └── widgets.py                  # Custom widgets (ServiceCard, StatusBar)
```

## File Purposes

### Core Application

- **`__main__.py`**: Entry point that routes to CLI or TUI based on arguments
  - No args → TUI dashboard
  - With args → CLI command

- **`models.py`**: Data classes for services and deployments
  - `Service`: Represents a Render service with status
  - `Deploy`: Represents a deployment with status and timing
  - `ServiceStatus`, `DeployStatus`: Enums for status values

- **`config.py`**: Configuration management
  - Loads and validates `config.yaml`
  - Supports environment variable substitution (`${RENDER_API_KEY}`)
  - Service alias matching and resolution

### CLI Mode (`cli.py`)

Handles quick command-line access:
- `rd <service> <action>` syntax
- Service matching by alias (exact, partial, fuzzy)
- Browser URL generation and opening
- Status command (terminal output without browser)

### API Client (`api/render.py`)

Async HTTP client for Render API:
- `get_service()`: Fetch service details and status
- `get_latest_deploy()`: Fetch most recent deployment
- `get_service_with_deploy()`: Combined fetch
- Error handling for auth, rate limits, network issues

### TUI Dashboard (`ui/`)

**`app.py`**: Main Textual application
- Service card container with scrolling
- Auto-refresh loop (configurable interval)
- Keyboard navigation and shortcuts
- Browser URL opening on actions

**`widgets.py`**: Custom UI components
- `ServiceCard`: Display service with status, deploy info, actions
- `StatusBar`: Shows last update time and controls
- Focus handling for keyboard shortcuts

## Data Flow

### TUI Mode Launch

```
rd (no args)
    ↓
__main__.main()
    ↓
ui/app.run_dashboard()
    ↓
DashboardApp.on_mount()
    ↓
config.load_config()  ←  config.yaml
    ↓
api/render.py (fetch all services)
    ↓
ui/widgets.ServiceCard (display each)
    ↓
Auto-refresh loop (every 30s)
```

### CLI Mode Execution

```
rd chat logs
    ↓
__main__.main() → ['chat', 'logs']
    ↓
cli.handle_cli_command()
    ↓
config.load_config()
    ↓
config.find_service_by_alias('chat')
    ↓
cli.get_service_url(service_id, 'logs')
    ↓
webbrowser.open(url)
```

### API Request Flow

```
RenderClient.get_service_with_deploy(service_id)
    ↓
httpx GET /v1/services/{serviceId}
    ↓
httpx GET /v1/services/{serviceId}/deploys?limit=1
    ↓
Parse response → Service + Deploy objects
    ↓
Return to caller (TUI or CLI)
```

## Key Design Decisions

### 1. Async Architecture
- **httpx** for async HTTP (better than requests for concurrent calls)
- **Textual** natively supports async (perfect for auto-refresh)
- Multiple services fetched concurrently for fast TUI load

### 2. Dual Entry Point
- Single `rd` command serves both modes
- Argument detection in `__main__.py` routes appropriately
- Shared config and API client reduce code duplication

### 3. Smart Service Matching
- Aliases from config enable short commands (`rd chat logs`)
- Partial matching for convenience (`rd ch logs`)
- Disambiguation for ambiguous matches

### 4. Browser Integration
- All dashboard actions open Render URLs in browser
- Fallback to printing URL if browser fails
- Status command explicitly doesn't open browser

### 5. Error Handling
- Graceful degradation (service fetch errors don't crash TUI)
- Helpful error messages for config issues
- Validation on startup catches problems early

## Extension Points

### Adding New Features

**New CLI action:**
1. Add to `valid_actions` in `cli.py`
2. Update `get_service_url()` to generate URL
3. Document in README

**New TUI widget:**
1. Create class in `ui/widgets.py` extending Textual widget
2. Add to `DashboardApp.compose()` in `ui/app.py`
3. Wire up interactions with messages/events

**New API endpoint:**
1. Add method to `RenderClient` in `api/render.py`
2. Update `Service` or `Deploy` model if needed
3. Use in TUI or CLI as needed

**New status indicator:**
1. Add to `ServiceStatus` enum in `models.py`
2. Update `get_status_color()` in `Service` class
3. Add CSS class in `widgets.py` if needed

## Dependencies

### Runtime
- **textual**: TUI framework (reactive, async-native)
- **httpx**: Modern async HTTP client
- **pyyaml**: Config file parsing
- **click**: CLI argument parsing (if expanded)
- **python-dateutil**: Timestamp parsing

### Development
- **pytest**: Testing framework (future)
- **black**: Code formatting (future)
- **mypy**: Type checking (future)

## Configuration Flow

```
1. Look for ./config.yaml
   ↓ (not found)
2. Look for ~/.config/render-dashboard/config.yaml
   ↓ (not found)
3. Show error: "No config.yaml found..."

Found config.yaml:
   ↓
Parse YAML
   ↓
Substitute ${RENDER_API_KEY} from environment
   ↓
Validate structure (required fields)
   ↓
Return AppConfig object
```

## Testing Strategy

### Unit Tests (Future)
- `config.py`: Config parsing, env var substitution, alias matching
- `api/render.py`: API client with mocked httpx responses
- `models.py`: Data model validation

### Integration Tests (Future)
- CLI commands with test config
- TUI launch and navigation
- Browser URL generation

### Manual Testing
- See `TESTING.md` for comprehensive checklist

## Performance Considerations

- **Concurrent API calls**: All services fetched in parallel
- **Cached completions**: ZSH plugin caches service list
- **Minimal re-renders**: Textual only updates changed widgets
- **Efficient polling**: Only refresh when TUI is active

## Security

- **API key in env var**: Not stored in code or committed
- **Config in gitignore**: Prevents accidental commit
- **HTTPS only**: All API calls over TLS
- **No sensitive logging**: API key never logged

---

**Questions?** Check README.md for usage or TESTING.md for verification steps.
