#!/usr/bin/env bash
# Verify render-dashboard installation
set -e

echo "🔍 Verifying Render Dashboard Installation..."
echo ""

# Check Python version
echo "1. Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -ge 3 ]] && [[ $PYTHON_MINOR -ge 9 ]]; then
    echo "   ✓ Python $PYTHON_VERSION (>= 3.9 required)"
else
    echo "   ✗ Python $PYTHON_VERSION is too old (>= 3.9 required)"
    exit 1
fi

# Check if package is installed
echo "2. Checking if package is installed..."
if python3 -c "import render_dashboard" 2>/dev/null; then
    VERSION=$(python3 -c "import render_dashboard; print(render_dashboard.__version__)")
    echo "   ✓ render_dashboard v$VERSION is installed"
else
    echo "   ✗ render_dashboard is not installed"
    echo "     Run: pip install -e ."
    exit 1
fi

# Check if rd command exists
echo "3. Checking if 'rd' command exists..."
if command -v rd &> /dev/null; then
    echo "   ✓ 'rd' command is available in PATH"
else
    echo "   ✗ 'rd' command not found"
    echo "     Run: pip install -e ."
    exit 1
fi

# Check dependencies
echo "4. Checking dependencies..."
DEPS=("textual" "httpx" "yaml" "dateutil")
ALL_DEPS_OK=true

for dep in "${DEPS[@]}"; do
    if python3 -c "import $dep" 2>/dev/null; then
        echo "   ✓ $dep is installed"
    else
        echo "   ✗ $dep is not installed"
        ALL_DEPS_OK=false
    fi
done

if [[ $ALL_DEPS_OK == false ]]; then
    echo "   Run: pip install -r requirements.txt"
    exit 1
fi

# Check for config file
echo "5. Checking for config file..."
if [[ -f "config.yaml" ]]; then
    echo "   ✓ config.yaml found in current directory"
elif [[ -f "$HOME/.config/render-dashboard/config.yaml" ]]; then
    echo "   ✓ config.yaml found in ~/.config/render-dashboard/"
else
    echo "   ℹ No config.yaml found (this is OK for testing)"
    echo "     Create one: cp config.yaml.example config.yaml"
fi

# Check for API key
echo "6. Checking for API key..."
if [[ -n "$RENDER_API_KEY" ]]; then
    echo "   ✓ RENDER_API_KEY is set"
else
    echo "   ℹ RENDER_API_KEY is not set (required for actual usage)"
    echo "     Set it: export RENDER_API_KEY=rnd_xxxxx"
fi

# Check zsh plugin (optional)
echo "7. Checking zsh plugin (optional)..."
if [[ -f "$HOME/.oh-my-zsh/custom/plugins/render-dashboard/render-dashboard.plugin.zsh" ]]; then
    echo "   ✓ Zsh plugin is installed"

    # Check if enabled
    if grep -q "render-dashboard" "$HOME/.zshrc" 2>/dev/null; then
        echo "   ✓ Plugin is enabled in ~/.zshrc"
    else
        echo "   ℹ Plugin is installed but not enabled in ~/.zshrc"
        echo "     Add 'render-dashboard' to your plugins array"
    fi
else
    echo "   ℹ Zsh plugin is not installed (optional)"
    echo "     Install it: ./install-zsh-plugin.sh"
fi

echo ""
echo "✅ Installation verification complete!"
echo ""
echo "Next steps:"
echo "  1. Set RENDER_API_KEY: export RENDER_API_KEY=rnd_xxxxx"
echo "  2. Create config.yaml: cp config.yaml.example config.yaml"
echo "  3. Edit config.yaml with your service IDs"
echo "  4. Run dashboard: rd"
echo "  5. Try CLI: rd <service> logs"
echo ""
echo "Documentation:"
echo "  • Quick start: cat QUICKSTART.md"
echo "  • Full guide: cat README.md"
echo "  • Testing: cat TESTING.md"
echo ""
