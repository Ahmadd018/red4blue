#!/bin/bash
# Lab configuration — edit this file before the lesson
# All tools and scripts read KALI_IP from here

# Auto-detect Kali IP (picks the first non-loopback IPv4 address)
KALI_IP=$(ip -4 addr show scope global | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)

# Override here if auto-detection picks the wrong interface:
# KALI_IP="192.168.11.149"

KALI_PORT=8080
LAB_DOMAIN="redlab.local"

export KALI_IP KALI_PORT LAB_DOMAIN
