#!/bin/bash

# Define the save location
DIR="$HOME/Pictures/Screenshots"
NAME="screenshot_$(date +%Y-%m-%d_%H-%M-%S).png"
PATH_FULL="$DIR/$NAME"

# Ensure the directory exists
mkdir -p "$DIR"

# Capture the screenshot
# -g "$(slurp)" allows you to click and drag to select an area
if grim -g "$(slurp)" "$PATH_FULL"; then
  # Copy to clipboard
  cat "$PATH_FULL" | wl-copy --type image/png

  # Optional: Send a notification (requires mako or dunst)
  notify-send "Screenshot Captured" "Saved to $NAME and copied to clipboard" -i "$PATH_FULL"
else
  notify-send "Screenshot Failed" "Selection cancelled or error occurred"
fi
