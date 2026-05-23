#!/usr/bin/env python3
"""
Fake SMTP server — captures emails GoPhish sends.
GoPhish sending profile: host=127.0.0.1 port=1025 no-auth no-TLS

Usage: python3 tools/smtp_server.py
"""

import asyncio, datetime, json, os
from email import message_from_bytes
from email.header import decode_header

LOG = "smtp_captured.log"

def decode_h(v):
    parts = decode_header(v or "")
    out = []
    for text, cs in parts:
        out.append(text.decode(cs or "utf-8", errors="replace") if isinstance(text, bytes) else text)
    return " ".join(out)

class Handler:
    async def handle_DATA(self, server, session, envelope):
        msg = message_from_bytes(envelope.content)
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = decode_h(msg.get("Subject", "(none)"))
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        entry = {"time": ts, "from": envelope.mail_from,
                 "to": envelope.rcpt_tos, "subject": subject, "preview": body[:300]}

        print(f"\n{'='*55}")
        print(f"  [EMAIL CAPTURED] {ts}")
        print(f"  From:    {envelope.mail_from}")
        print(f"  To:      {', '.join(envelope.rcpt_tos)}")
        print(f"  Subject: {subject}")
        print(f"{'='*55}")

        with open(LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return "250 OK"

def main():
    host, port = "127.0.0.1", 1025
    print(f"SMTP capture server on {host}:{port}")
    print(f"Emails logged to: {LOG}")
    print("GoPhish sending profile → Host: 127.0.0.1  Port: 1025  (no auth, no TLS)")
    print("Ctrl+C to stop\n")
    try:
        from aiosmtpd.controller import Controller
        ctrl = Controller(Handler(), hostname=host, port=port)
        ctrl.start()
        asyncio.get_event_loop().run_forever()
    except ImportError:
        print("[!] pip3 install aiosmtpd")
        print(f"    Alternative: python3 -m smtpd -n -c DebuggingServer {host}:{port}")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
