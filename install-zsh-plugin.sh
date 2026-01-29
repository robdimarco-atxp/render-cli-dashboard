#!/usr/bin/env bash
# Install Render Dashboard ZSH plugin for oh-my-zsh
set -e

PLUGIN_NAME="render-dashboard"
PLUGIN_DIR="${HOME}/.oh-my-zsh/custom/plugins/${PLUGIN_NAME}"
PLUGIN_FILE="${PLUGIN_DIR}/${PLUGIN_NAME}.plugin.zsh"

echo "Installing Render Dashboard ZSH plugin..."

# Check if oh-my-zsh is installed
if [[ ! -d "${HOME}/.oh-my-zsh" ]]; then
    echo "Error: oh-my-zsh not found at ${HOME}/.oh-my-zsh"
    echo "Install oh-my-zsh first: https://ohmyz.sh/"
    exit 1
fi

# Create plugin directory
mkdir -p "${PLUGIN_DIR}"

# Copy plugin file
cp render-dashboard.plugin.zsh "${PLUGIN_FILE}"
echo "✓ Copied plugin file to ${PLUGIN_FILE}"

# Check if plugin is already enabled in .zshrc
if grep -q "plugins=(.*${PLUGIN_NAME}.*)" "${HOME}/.zshrc"; then
    echo "✓ Plugin already enabled in ~/.zshrc"
else
    echo ""
    echo "To enable the plugin, add '${PLUGIN_NAME}' to your plugins in ~/.zshrc:"
    echo ""
    echo "  plugins=("
    echo "    git"
    echo "    zsh-autosuggestions"
    echo "    ${PLUGIN_NAME}  # Add this line"
    echo "  )"
    echo ""
    echo "Then reload your shell: source ~/.zshrc"
fi

echo ""
echo "Installation complete! 🎉"
echo ""
echo "After enabling the plugin and reloading your shell, you'll get:"
echo "  • Tab completion for 'rd <service> <action>'"
echo "  • Autosuggestions based on your command history"
echo ""
