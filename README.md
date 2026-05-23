# Red4Blue — Offensive Security Training Lab

Hands-on red team vs blue team lessons.  
Each lesson runs on Kali (attacker) + Windows (victim) on the same LAN.

## Lessons

| # | Topic | Duration |
|---|-------|----------|
| [Lesson 1](lesson1/README.md) | Recon, Initial Access & Phishing | 2 hours |

## Clone & Start

```bash
git clone https://github.com/<your-org>/red4blue.git
cd red4blue/lesson1
sudo bash setup/setup_lab.sh
# open lesson1/GUIDE.md
```

## Lab Requirements

| Role | OS | Notes |
|------|----|-------|
| Attacker | Kali Linux | GoPhish pre-installed (`sudo gophish`) |
| Victim | Windows 10/11 | Same LAN subnet as Kali |
