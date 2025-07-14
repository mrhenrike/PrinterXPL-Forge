#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from subprocess import call

# ─── MODULE IMPORTS ────────────────────────────────────────────────────────────
from nmap_launcher import (
    check_nmap_installed,
    suggest_nmap_installation,
    build_target_list,
    run_nmap_scan,
    parse_nmap_xml,
    save_outputs,
)

from generate_poc_pdf import PoCPDF, load_file

# ─── PDF WRAPPER ───────────────────────────────────────────────────────────────
def generate_pdf(out_text, md_text, pdf_path, target, verbose=False):
    title = "PrinterReaper - Proof of Concept"

    if verbose:
        print(f"[i] Generating PoC PDF: {pdf_path}")

    pdf = PoCPDF(title=title, target=target)
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Target: {target}", ln=True)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    if md_text:
        pdf.add_section("Technical Summary", md_text)
    if out_text:
        pdf.add_section("Raw Evidence (.out)", out_text, monospaced=True)

    pdf.output(pdf_path)
    print(f"[✓] PDF saved to: {pdf_path}")

# ─── MAIN WRAPPER ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Unified Nmap + PDF PoC Generator")
    parser.add_argument('--ip', help='Scan a single IP address')
    parser.add_argument('--range', help='Scan an IP range (e.g. 192.168.1.10-192.168.1.50)')
    parser.add_argument('--file', help='Scan a list of IPs from file (one per line)')
    parser.add_argument('--subnet', help='Use "auto" to choose from local interfaces')
    parser.add_argument('--formats', help='Output formats: json,md (comma-separated)', default="json,md")
    parser.add_argument('--outdir', help='Output directory (default: ./results)', default="results")
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logs')
    args = parser.parse_args()

    if not check_nmap_installed():
        suggest_nmap_installation()

    if len(sys.argv) == 1:
        print("[i] No parameters provided. Defaulting to: --subnet auto")
        args.subnet = "auto"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    formats = [f.strip().lower() for f in args.formats.split(",") if f.strip()]
    targets = build_target_list(args)

    for target in targets:
        print(f"\n[+] Scanning target: {target}")
        xml_path = run_nmap_scan(target, timestamp, args.outdir, formats, verbose=args.verbose)

        if not xml_path or not os.path.exists(xml_path):
            print(f"[!] XML output not found for {target}")
            continue

        result = parse_nmap_xml(xml_path)
        if formats:
            save_outputs(result, timestamp, target, formats, args.outdir, verbose=args.verbose)

        # Build output paths
        safe = target.replace('/', '_').replace('.', '_')
        md_path = os.path.join(args.outdir, f"nmap_summary_{timestamp}_{safe}.md")
        out_path = os.path.join(args.outdir, f"output_{safe}_{timestamp}.out")
        pdf_path = os.path.join(args.outdir, f"poc_{safe}_{timestamp}.pdf")

        # Touch empty .out if not created
        if not os.path.exists(out_path):
            with open(out_path, "w") as f:
                f.write("")  # Empty raw log

        md_text = load_file(md_path, verbose=args.verbose)
        out_text = load_file(out_path, verbose=args.verbose)
        generate_pdf(out_text, md_text, pdf_path, target, verbose=args.verbose)

if __name__ == "__main__":
    main()
