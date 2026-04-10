#!/bin/bash
wpctl set-volume @DEFAULT_AUDIO_SINK@ 5%-
pkill -RTMIN+8 waybar
