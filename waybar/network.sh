#!/usr/bin/env bash
eth_ip=$(ip -4 addr show enp12s0 | grep -oP "(?<=inet\s)\d+(\.\d+){3}")
if [ ! -z "$eth_ip" ]; then
    echo "󰈀 $eth_ip"
else
    wifi_essid=$(nmcli -t -f active,ssid dev wifi | grep ^yes | cut -d: -f2)
    if [ ! -z "$wifi_essid" ]; then
        echo " $wifi_essid"
    else
        echo "󰖪 Disconnected"
    fi
fi
