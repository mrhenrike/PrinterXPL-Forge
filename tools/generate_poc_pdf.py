#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime
from fpdf import FPDF

class PoCPDF(FPDF):
    def __init__(self, title, target):
        super().__init__()
        self.title = title
        self.target = target
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_fill_color(0, 0, 0)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, self.title, ln=True, align="C", fill=True)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.set_text_color(150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def add_section(self, heading, content, monospaced=False):
        self.set_text_color(0)
        self.set_font("Arial", "B", 12)
        self.ln(10)
        self.cell(0, 10, heading, ln=True)

        self.set_font("Courier", "", 10) if monospaced else self.set_font("Arial", "", 11)

        if not content.strip():
            self.set_text_color(150)
            self.multi_cell(0, 8, "[No data]")
            self.set_text_color(0)
        else:
            self.multi_cell(0, 8, content)

def load_file(path, verbose=False):
    if path and os.path.exists(path):
        if verbose:
            print(f"[✓] Loaded: {path}")
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    elif path:
        print(f"[!] File not found: {path}")
        sys.exit(1)
    return ""

def main():
    parser = argparse.ArgumentParser(description="Generate PoC PDF from .out and .md files")
    parser.add_argument("--out", help="Raw payload output file (.out)")
    parser.add_argument("--md", help="Optional Markdown technical summary (.md)")
    parser.add_argument("--output", help="Destination PDF (default: results/poc_<timestamp>.pdf)")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed output")

    args = parser.parse_args()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("results", exist_ok=True)

    pdf_path = args.output or f"results/poc_{timestamp}.pdf"
    title = "PrinterReaper - Proof of Concept"
    target = "Unknown"

    if args.out:
        try:
            target = ".".join(os.path.basename(args.out).split("_")[1:5])
        except:
            pass

    # Validate and load files
    out_content = load_file(args.out, verbose=args.verbose) if args.out else ""
    md_content = load_file(args.md, verbose=args.verbose) if args.md else ""

    if not out_content and not md_content:
        print("[!] At least one valid file is required (--out or --md).")
        sys.exit(1)

    if args.verbose:
        print(f"[i] Generating PDF: {pdf_path}")

    pdf = PoCPDF(title=title, target=target)
    pdf.add_page()
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Target: {target}", ln=True)
    pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)

    if args.md:
        pdf.add_section("Technical Summary", md_content)
    if args.out:
        pdf.add_section("Raw Evidence (.out)", out_content, monospaced=True)

    pdf.output(pdf_path)

    print(f"[✓] PoC report saved to: {pdf_path}")

if __name__ == "__main__":
    main()
