#!/usr/bin/env bash

DOCK_CACHE="/tmp/hypr_docked_windows.txt"

if [ ! -f "$DOCK_CACHE" ] || [ ! -s "$DOCK_CACHE" ]; then
    exit 0
fi

# Format lines out of the cache file for user selection (latest additions at the top)
MENU_OPTIONS=$(tac "$DOCK_CACHE" | awk -F'|' '{print $2 " (" $1 ")"}')

# Pipe the structured options straight into wofi's dmenu emulator mode
SELECTION=$(echo "$MENU_OPTIONS" | wofi --dmenu --prompt "Select window to restore:")

if [ -z "$SELECTION" ]; then
    exit 0
fi

# Strip the raw hex memory address out of the parentheses block
TARGET_ADDR=$(echo "$SELECTION" | sed -n 's/.*(\(0x[0-9a-fA-F]*\)).*/\1/p')

if [ -z "$TARGET_ADDR" ]; then
    exit 0
fi

# Query which monitor currently holds mouse focus to grab its active workspace ID
CURRENT_WS=$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .activeWorkspace.id')

# Pull the specific window address into view and give it focus
hyprctl dispatch movetoworkspace "$CURRENT_WS",address:"$TARGET_ADDR"
hyprctl dispatch focuswindow address:"$TARGET_ADDR"

# Delete that specific line out of the cache file cleanly
sed -i "/$TARGET_ADDR/d" "$DOCK_CACHE"
