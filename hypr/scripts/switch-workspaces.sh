#!/bin/bash
# Switch all 3 monitors to a workspace group
# Group 1: DP-2=1, DP-1=2, HDMI-A-1=3
# Group 2: DP-2=4, DP-1=5, HDMI-A-1=6
# Group 3: DP-2=7, DP-1=8, HDMI-A-1=9

INDEX=$1
case $INDEX in
1)
  LEFT=1
  MID=2
  RIGHT=3
  ;;
2)
  LEFT=4
  MID=5
  RIGHT=6
  ;;
3)
  LEFT=7
  MID=8
  RIGHT=9
  ;;
*) exit 1 ;;
esac

hyprctl dispatch focusmonitor DP-2 && hyprctl dispatch workspace $LEFT
hyprctl dispatch focusmonitor DP-1 && hyprctl dispatch workspace $MID
hyprctl dispatch focusmonitor HDMI-A-1 && hyprctl dispatch workspace $RIGHT

# Signal Waybar to update
pkill -USR2 waybar
