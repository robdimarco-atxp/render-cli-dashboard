# PATH Setup for `rdash` Command

## How It Works

When you run `pip install -e .`, Python's setuptools automatically:

1. Creates an executable script called `rdash` in your virtual environment's `bin/` directory
2. This happens because of the `console_scripts` entry point in `setup.py`:
   ```python
   entry_points={
       "console_scripts": [
           "rdash=render_dashboard.__main__:main",
       ],
   }
   ```

## No Manual PATH Setup Required

**As long as your virtual environment is activated**, the `rdash` command is automatically available in your PATH.

```bash
# Activate venv (adds .venv/bin to your PATH)
source .venv/bin/activate

# Now rdash is available
rdash service add chat
rdash chat logs
rdash  # Launch TUI
```

## How to Check

```bash
# With venv activated:
which rdash
# Output: /path/to/render-dashboard/.venv/bin/rdash

# View the actual script:
cat .venv/bin/rdash
# It's a Python wrapper that calls render_dashboard.__main__:main()
```

## Making It Always Available

If you want `rdash` available in all terminal sessions without manually activating the venv each time:

### Option 1: Auto-activate venv in shell startup

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# Auto-activate render-dashboard venv
source /path/to/render-dashboard/.venv/bin/activate
```

**Pros:** Simple, automatic
**Cons:** Activates venv for all terminal sessions (may not want this)

### Option 2: Create a shell alias

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
alias rdash='/path/to/render-dashboard/.venv/bin/rdash'
```

**Pros:** No venv activation needed, isolated
**Cons:** Need to specify full path

### Option 3: Symlink to local bin

```bash
# Create a local bin directory (if it doesn't exist)
mkdir -p ~/bin

# Add to PATH if not already (add to ~/.zshrc or ~/.bashrc)
export PATH="$HOME/bin:$PATH"

# Create symlink
ln -s /path/to/render-dashboard/.venv/bin/rdash ~/bin/rdash
```

**Pros:** Clean, works from any directory
**Cons:** Symlink breaks if you recreate the venv

### Option 4: Install in user site-packages (not recommended)

```bash
# Instead of pip install -e .
pip install --user .
```

**Pros:** Globally available
**Cons:**
- Not editable (changes to code won't take effect)
- Harder to uninstall
- Doesn't follow Python best practices

## Recommended Approach

**For development:** Use Option 1 (auto-activate venv in shell)

Add this to your `~/.zshrc`:

```bash
# Render Dashboard venv
if [[ -f "$HOME/projects/render-dashboard/.venv/bin/activate" ]]; then
    source "$HOME/projects/render-dashboard/.venv/bin/activate"
fi
```

This way:
- ✅ `rdash` is always available
- ✅ Virtual environment is properly isolated
- ✅ Changes to code take effect immediately (because of `-e` flag)
- ✅ No path conflicts

## Troubleshooting

### "rdash: command not found"

**Problem:** Virtual environment not activated

**Solution:**
```bash
source .venv/bin/activate
which rdash  # Should show path in .venv/bin/
```

### "rdash is aliased to something else"

**Problem:** Shell alias conflicts (like `rd` → `rmdir`)

**Solution:**
```bash
# Check for conflicts
type rdash

# If aliased, unalias it
unalias rdash

# Or use full path
/path/to/render-dashboard/.venv/bin/rdash
```

### "rdash exists but doesn't work"

**Problem:** Reinstallation needed

**Solution:**
```bash
source .venv/bin/activate
pip uninstall render-dashboard
pip install -e .
```

## Summary

- ✅ **No manual PATH setup needed** when venv is activated
- ✅ `pip install -e .` automatically creates the `rdash` command
- ✅ Command is located at `.venv/bin/rdash`
- ✅ Just activate venv: `source .venv/bin/activate`
- ✅ For permanent access, add activation to shell startup file

---

**Note:** We changed the command from `rd` to `rdash` to avoid conflicts with the common `rd` → `rmdir` alias.
