#!/usr/bin/env bash

TARGET_ADDR=$1

if [ -z "$TARGET_ADDR" ]; then exit 0; fi

# Get current active workspace
CURRENT_WS=$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .activeWorkspace.id')

# Pull it straight to your current screen
hyprctl dispatch movetoworkspace "$CURRENT_WS",address:"$TARGET_ADDR"

# Clean up our tracking cache file
sed -i "/$TARGET_ADDR/d" /tmp/hypr_docked_windows.txt
