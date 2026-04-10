#!/bin/bash
# Set wallpapers for all monitors
for m in $(hyprctl monitors | awk 'NR>1 {print $2}'); do
    hyprpaper --set "$m" /home/alzrag/Pictures/wallpaper.png
done
