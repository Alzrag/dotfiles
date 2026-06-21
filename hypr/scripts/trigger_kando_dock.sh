#!/usr/bin/env bash

TARGET_CLASS=$1
DOCK_CACHE="/tmp/hypr_docked_windows.txt"
KANDO_MENU_FILE="$HOME/.config/kando/menus.json"

if [ -z "$TARGET_CLASS" ] || [ ! -f "$DOCK_CACHE" ]; then exit 1; fi

MENU_JSON="{\"menus\": [{\"name\": \"Undock $TARGET_CLASS\", \"id\": \"dynamic-dock\", \"items\": ["
FIRST=true

while IFS='|' read -r ADDR CLASS || [ -n "$ADDR" ]; do
    if [ "$CLASS" == "$TARGET_CLASS" ]; then
        # Query the exact human-readable window title using hyprctl
        TITLE=$(hyprctl clients -j | jq -r ".[] | select(.address == \"$ADDR\") | .title" | sed 's/"/\\"/g')
        if [ -z "$TITLE" ] || [ "$TITLE" == "null" ]; then TITLE="$CLASS ($ADDR)"; fi

        if [ "$FIRST" = true ] ; then FIRST=false; else MENU_JSON+=","; fi

        # Command to restore the exact window instance and clean it from our tracking cache
        CMD="hyprctl dispatch movetoworkspace \$(hyprctl monitors -j | jq -r '.[] | select(.focused == true) | .activeWorkspace.id'),address:$ADDR && hyprctl dispatch focuswindow address:$ADDR && sed -i '/$ADDR/d' $DOCK_CACHE"
        
        # You can use your Candy Icons names here inside Kando's native rendering canvas!
        KANDO_ICON="window"
        if [ "$TARGET_CLASS" == "kitty" ]; then KANDO_ICON="terminal"; fi
        if [ "$TARGET_CLASS" == "opera" ]; then KANDO_ICON="browser"; fi

        MENU_JSON+="{\"name\": \"$TITLE\", \"icon\": \"$KANDO_ICON\", \"command\": \"$CMD\"}"
    fi
done < "$DOCK_CACHE"

MENU_JSON+="]}]}"

# Hot-swap Kando's configuration layer instantly
echo "$MENU_JSON" > "$KANDO_MENU_FILE"

# Fire the global keybind pipeline hook to draw the ring at your cursor coordinates
hyprctl dispatch global menu.kando.Kando:dynamic-dock
