#!/usr/bin/env zsh
# Render Dashboard ZSH Plugin
#
# Installation:
# 1. Copy to: ~/.oh-my-zsh/custom/plugins/render-dashboard/render-dashboard.plugin.zsh
# 2. Add 'render-dashboard' to plugins in ~/.zshrc
# 3. Reload: source ~/.zshrc

# Cache file location
_RDASH_CACHE_FILE="${HOME}/.cache/render-dashboard/completions"

# Generate completions from config.yaml
_rdash_generate_completions() {
    # Look for config in standard locations
    local config_file=""
    if [[ -f "${HOME}/.config/render-dashboard/config.yaml" ]]; then
        config_file="${HOME}/.config/render-dashboard/config.yaml"
    elif [[ -f "./config.yaml" ]]; then
        config_file="./config.yaml"
    else
        return 1
    fi

    # Extract service aliases from config
    local aliases=()
    while IFS= read -r line; do
        # Match lines like: - "chat"
        if [[ $line =~ ^[[:space:]]*-[[:space:]]*[\"\'](.*)[\"\']\s*$ ]]; then
            aliases+=("${match[1]}")
        fi
    done < <(awk '/aliases:/{flag=1;next}/^[[:space:]]*-[[:space:]]*id:/{flag=0}flag' "$config_file")

    # Actions that can be performed on services
    local actions=(logs events deploys settings status)

    # Create cache directory
    mkdir -p "$(dirname "$_RDASH_CACHE_FILE")"

    # Write completions to cache
    {
        for alias in $aliases; do
            for action in $actions; do
                echo "rdash ${alias} ${action}"
            done
        done
    } > "$_RDASH_CACHE_FILE"
}

# Completion function
_rdash_completion() {
    local -a commands
    local state

    # Generate cache if missing or config is newer
    local config_file=""
    if [[ -f "${HOME}/.config/render-dashboard/config.yaml" ]]; then
        config_file="${HOME}/.config/render-dashboard/config.yaml"
    elif [[ -f "./config.yaml" ]]; then
        config_file="./config.yaml"
    fi

    if [[ -n "$config_file" ]] && { [[ ! -f "$_RDASH_CACHE_FILE" ]] || [[ "$config_file" -nt "$_RDASH_CACHE_FILE" ]]; }; then
        _rdash_generate_completions
    fi

    # Define completion spec
    _arguments -C \
        '1:service:->services' \
        '2:action:->actions' \
        && return 0

    case $state in
        services)
            # Extract unique service aliases from cache
            if [[ -f "$_RDASH_CACHE_FILE" ]]; then
                local -a services
                services=($(awk '{print $2}' "$_RDASH_CACHE_FILE" | sort -u))
                _describe 'service' services
            fi
            ;;
        actions)
            local -a actions
            actions=(
                'logs:Open service logs in browser'
                'events:Open service events in browser'
                'deploys:Open service deploys in browser'
                'settings:Open service settings in browser'
                'status:Show current service status in terminal'
            )
            _describe 'action' actions
            ;;
    esac
}

# Register completion
compdef _rdash_completion rdash

# Generate initial completions on plugin load
_rdash_generate_completions 2>/dev/null

# Helpful aliases (optional - can be commented out if not wanted)
# Uncomment these if you want quick aliases
# alias rd='rdash'  # If you want to use 'rd' as shorthand
