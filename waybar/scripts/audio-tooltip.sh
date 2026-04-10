#!/usr/bin/env bash

# Active sink
sink=$(wpctl status | awk '/\*.*Audio\/Sink/ {getline; print}' | sed 's/^[[:space:]]*//')

# Media info
player=$(playerctl -l 2>/dev/null | head -n1)

if [ -n "$player" ]; then
  title=$(playerctl metadata title 2>/dev/null)
  artist=$(playerctl metadata artist 2>/dev/null)
  media="🎵 $artist – $title"
else
  media="🎵 No media playing"
fi

echo -e "$media\n🔊 $sink"
