#!/usr/bin/env bash

DOCK_CACHE="/tmp/hypr_docked_windows.txt"

# If the tracking cache doesn't exist or is empty, output an empty JSON string
if [ ! -f "$DOCK_CACHE" ] || [ ! -s "$DOCK_CACHE" ]; then
    echo "{\"text\":\"\",\"tooltip\":\"\"}"
    exit 0
fi

# Simple associative array to map app classes to font glyphs
declare -A ICON_MAP=(
    ["kitty"]=""
    ["opera"]="󰈹"
    ["firefox"]="󰈹"
    ["chromium"]=""
    ["code-oss"]="󰨞"
    ["default"]=""
)

GLYPH_STRING=""

while IFS='|' read -r ADDR CLASS || [ -n "$ADDR" ]; do
    ICON="${ICON_MAP[$CLASS]}"
    if [ -z "$ICON" ]; then
        ICON="${ICON_MAP["default"]}"
    fi
    GLYPH_STRING+="$ICON  "
done < "$DOCK_CACHE"

# Remove any trailing spaces from the final string output
GLYPH_STRING=$(echo "$GLYPH_STRING" | sed 's/[[:space:]]*$//')

echo "{\"text\":\"$GLYPH_STRING\",\"tooltip\":\"Active Minimized Windows\"}"
