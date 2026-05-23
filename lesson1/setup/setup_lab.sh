#!/bin/bash
# One-time lab setup — run before Lesson 1
# Sets up tools, directories, and /etc/hosts entries

set -e
source "$(dirname "$0")/../config.sh"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

echo "=================================================="
echo "  RED4BLUE — Lesson 1 Lab Setup"
echo "  Kali attacker IP: $KALI_IP"
echo "=================================================="

sudo apt-get update -qq

# Tools
for pkg in httrack theharvester golang nmap; do
    sudo apt-get install -y $pkg > /dev/null 2>&1 && ok "$pkg" || warn "$pkg skipped"
done

pip3 install python-docx requests aiosmtpd --break-system-packages && ok "python-docx requests aiosmtpd" || warn "pip3 install failed"

# Evilginx2
if [ ! -f /usr/local/bin/evilginx ]; then
    warn "Building evilginx2 (takes ~2 min)..."
    cd /tmp
    git clone https://github.com/kgretzky/evilginx2.git evilginx2_build 2>/dev/null || true
    cd evilginx2_build && go build -o /usr/local/bin/evilginx 2>/dev/null && ok "evilginx2 built" || warn "evilginx2 build failed — skip for now"
    cd /home/kali/red4blue
else
    ok "evilginx2 already installed"
fi

# /etc/hosts lab domain
DOMAIN="redlab.local"
if ! grep -q "$DOMAIN" /etc/hosts; then
    echo "$KALI_IP  $DOMAIN" | sudo tee -a /etc/hosts > /dev/null
    ok "Added $DOMAIN → $KALI_IP to /etc/hosts"
else
    ok "$DOMAIN already in /etc/hosts"
fi

# Payloads dir
mkdir -p /home/kali/red4blue/lesson1/payloads

echo ""
echo "=================================================="
echo "  DONE. Lab is ready."
echo ""
echo "  GoPhish:   sudo gophish"
echo "             https://127.0.0.1:3333"
echo "             admin / kali-gophish"
echo ""
echo "  Next step: open lesson1/GUIDE.md"
echo "=================================================="
echo ""
echo "  WINDOWS VICTIM — add this to hosts file:"
echo "  (C:\\Windows\\System32\\drivers\\etc\\hosts)"
echo "  $KALI_IP  $DOMAIN"
echo "=================================================="
