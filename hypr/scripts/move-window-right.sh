#!/bin/bash

# Get the current workspace ID of the active window
current_ws=$(hyprctl activewindow -j | jq '.workspace.id')

# Increment if less than 6
if [ "$current_ws" -lt 6 ]; then
  next_ws=$((current_ws - 1))
  # 'silent' moves the window without changing the monitor's active workspace
  hyprctl dispatch movetoworkspacesilent "$next_ws"
fi
