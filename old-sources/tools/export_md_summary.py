import json
import os
from datetime import datetime

def load_scan(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def export_to_md(data, out_path="results/network_summary.md"):
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f"# PrinterReaper - Executive Summary\n")
        f.write(f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n")
        for device in data:
            f.write(f"## Host: `{device.get('ip')}`\n\n")
            f.write(f"**Vendor**: {device.get('vendor')}\n\n")
            if 'snmp' in device:
                f.write("### SNMP Info\n")
                for k, v in device['snmp'].items():
                    f.write(f"- **{k}**: `{v}`\n")
            else:
                f.write("*No SNMP data available*\n")
            f.write("\n---\n\n")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--scan', required=True, help='Path to .json scan result file')
    args = parser.parse_args()

    data = load_scan(args.scan)
    export_to_md(data)
    print("[✓] Export completed: results/network_summary.md")
