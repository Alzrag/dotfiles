#!/bin/bash

# Get the current workspace ID of the active window
current_ws=$(hyprctl activewindow -j | jq '.workspace.id')

# Decrement if greater than 1
if [ "$current_ws" -gt 1 ]; then
  prev_ws=$((current_ws + 1))
  # 'silent' moves the window without changing the monitor's active workspace
  hyprctl dispatch movetoworkspacesilent "$prev_ws"
fi
