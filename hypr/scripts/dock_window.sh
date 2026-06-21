#!/usr/bin/env bash

DOCK_CACHE="/tmp/hypr_docked_windows.txt"

# 1. Get the hex address and class of the currently active window
ACTIVE_WINDOW=$(hyprctl activewindow -j)
ADDR=$(echo "$ACTIVE_WINDOW" | jq -r '.address')
CLASS=$(echo "$ACTIVE_WINDOW" | jq -r '.class')

# Safety check: Exit if we are trying to minimize an empty desktop
if [ -z "$ADDR" ] || [ "$ADDR" = "null" ]; then
    exit 0
fi

# 2. Log the window state to our tracking cache (strictly 2 columns)
echo "${ADDR}|${CLASS}" >> "$DOCK_CACHE"

# 3. Send the window away to hidden workspace 100
hyprctl dispatch movetoworkspacesilent 100,address:"${ADDR}"
