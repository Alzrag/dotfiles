"custom/power": {
    "format": "⚡ {}W",
    "exec": "nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits",
    "interval": 5
}
