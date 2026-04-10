#!/usr/bin/env bash

# Get volume
raw=$(wpctl get-volume @DEFAULT_AUDIO_SINK@)
vol=$(echo "$raw" | awk '{print int($2*100)}')
mute=$(echo "$raw" | grep -q MUTED && echo 1 || echo 0)

# Volume to level (0–5)
level=$((vol / 20))
[ "$level" -gt 5 ] && level=5

# Character sets to simulate motion
frames=("▁▂▃▄▅" "▂▃▄▅▆" "▃▄▅▆▇" "▄▅▆▇█")
frame=${frames[$((RANDOM % ${#frames[@]}))]}

bars=""
for i in {1..5}; do
  if [ "$i" -le "$level" ]; then
    bars+="${frame:$((i - 1)):1}"
  else
    bars+="▯"
  fi
done

# Icon
icon="󰕾"
[ "$mute" -eq 1 ] && icon="󰖁"

# Get current active audio device (PipeWire 1.4.9 compatible)
active_dev=$(wpctl status | awk '
/Sinks:/ {s=1}
s && /\*/ {
    # Remove everything up to the first alphabetic character
    match($0, /[A-Za-z].*/)
    if (RSTART) print substr($0, RSTART)
    exit
}')
[ -z "$active_dev" ] && active_dev="Unknown device"

# Output single JSON object
printf '{"text":"%s %d%% %s","class":"vol-%d","tooltip":"%s"}\n' \
  "$icon" "$vol" "$bars" "$level" "$active_dev"
