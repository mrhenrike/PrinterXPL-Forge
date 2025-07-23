#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from utils.helper import output

def help_cve(self):
    print()
    print("cve")
    print("    List known CVEs for the connected printer based on its device ID.")
    print()
    print("Usage:")
    print("    cve")
    print()
    print("Examples:")
    print("    cve")
    print()
    print("Note: uses the printer’s Device: string to look up CVEs via NVD’s REST API.")
    print()

def do_cve(self, arg):
    """
    List known CVEs for the connected printer based on its device ID.
    """
    device = getattr(self, "device_info", None)
    if not device:
        output().errmsg("CVE", "No device information available.")
        return

    # parse manufacturer/model out of the Device string
    parts = device.split(None, 1)
    vendor = parts[0]
    model  = parts[1] if len(parts) > 1 else ""

    query = f"{vendor}%20{model}"
    url = f"https://services.nvd.nist.gov/rest/json/cves/1.0?keyword={query}&resultsPerPage=20"

    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        output().errmsg("CVE", f"Failed to fetch CVEs: {e}")
        return

    items = data.get("result", {}).get("CVE_Items", [])
    if not items:
        output().info(f"No CVEs found for {device}")
        return

    # build rows
    rows = []
    for idx, item in enumerate(items, start=1):
        cve_id = item["cve"]["CVE_data_meta"]["ID"]
        link   = f"https://nvd.nist.gov/vuln/detail/{cve_id}"
        rows.append((str(idx), vendor, model, cve_id, link))

    # print table
    headers = ("ORD", "Vendor", "Model", "CVE-ID", "Link")
    col_widths = [ max(len(r[i]) for r in ([headers] + rows)) for i in range(len(headers)) ]

    print()
    print("  ".join(headers[i].ljust(col_widths[i]) for i in range(len(headers))))
    print("  ".join("-" * col_widths[i] for i in range(len(headers))))
    for r in rows:
        print("  ".join(r[i].ljust(col_widths[i]) for i in range(len(headers))))
    print()
