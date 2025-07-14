#!/usr/bin/env python3

# ─── STANDARD LIBRARIES ────────────────────────────────────────────────────────
import os
import sys
import json
import argparse
import subprocess
import platform
import ipaddress
import xml.etree.ElementTree as ET
from datetime import datetime

# ─── THIRD-PARTY ──────────────────────────────────────────────────────────────
import psutil  # for detecting local interfaces

# ─── NMAP CHECK ───────────────────────────────────────────────────────────────
def check_nmap_installed():
    try:
        subprocess.check_output(["nmap", "-V"])
        return True
    except Exception:
        return False

def suggest_nmap_installation():
    system = platform.system()
    print("\n[!] Nmap is not installed or not found in PATH.\n")
    print("➡️  Please install it from: https://nmap.org/download.html\n")
    if system == "Windows":
        print("Windows: https://nmap.org/dist/nmap-7.95-setup.exe")
        print("⚠️ Make sure to check 'Add to PATH' during installation.")
    elif system == "Linux":
        print("Debian/Ubuntu: sudo apt install nmap")
    elif system == "Darwin":
        print("macOS: brew install nmap")
    sys.exit(1)

# ─── INTERFACE DETECTION ──────────────────────────────────────────────────────
def list_all_subnets():
    subnets = []
    for iface, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family.name == 'AF_INET' and not addr.address.startswith("127."):
                ip = addr.address
                netmask = addr.netmask
                if ip and netmask:
                    cidr = sum(bin(int(x)).count('1') for x in netmask.split('.'))
                    subnet = f"{ip}/{cidr}"
                    subnets.append((iface, subnet))
    return subnets

def choose_subnet_interactively():
    subnets = list_all_subnets()
    if not subnets:
        print("[!] No valid subnets found.")
        sys.exit(1)

    print("\nAvailable subnets:\n")
    for i, (iface, subnet) in enumerate(subnets, 1):
        print(f"  {i}. {subnet} ({iface})")
    print("  all. Scan all interfaces\n")

    choice = input("Choose subnet number or 'all': ").strip().lower()
    if choice == "all":
        return [s[1] for s in subnets]
    elif choice.isdigit() and 1 <= int(choice) <= len(subnets):
        return [subnets[int(choice) - 1][1]]
    else:
        print("[!] Invalid choice.")
        sys.exit(1)

# ─── INPUT TARGET BUILD ───────────────────────────────────────────────────────
def build_target_list(args):
    if args.ip:
        return [args.ip]
    elif args.range:
        try:
            start_ip, end_ip = args.range.split("-")
            ips = [str(ip) for ip in ipaddress.summarize_address_range(
                ipaddress.IPv4Address(start_ip),
                ipaddress.IPv4Address(end_ip)
            )]
            return ips
        except:
            print("[!] Invalid IP range format. Use: 192.168.1.10-192.168.1.50")
            sys.exit(1)
    elif args.file:
        try:
            with open(args.file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except:
            print(f"[!] Could not read IP list from file: {args.file}")
            sys.exit(1)
    elif args.subnet == "auto":
        return choose_subnet_interactively()
    else:
        print("[!] No valid scan target specified.")
        sys.exit(1)

# ─── NMAP EXECUTION ───────────────────────────────────────────────────────────
import subprocess

def run_nmap_scan(target, timestamp, outdir, formats, verbose=False):
    safe_name = target.replace('/', '_').replace('.', '_')
    os.makedirs(outdir, exist_ok=True)

    if formats:
        xml_path = os.path.join(outdir, f"nmap_scan_{timestamp}_{safe_name}.xml")
        out_flag = f"-oX \"{xml_path}\""
    else:
        devnull = "NUL" if platform.system() == "Windows" else "/dev/null"
        out_flag = f"-oN {devnull}"
        xml_path = None

    cmd = [
        "nmap",
        "-p", "80,443,515,631,9100,161",
        "-sS", "-sU", "-A", "-T4",
        "--script", "default,discovery,safe,version,snmp*,http*,banner,vuln",
        "--script-args", "unsafe=1,snmpcommunity=public"
    ] + out_flag.split() + [target]

    if verbose:
        print(f"\n[DEBUG] Running command:\n{' '.join(cmd)}\n")
        try:
            process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr)
            process.communicate()
        except KeyboardInterrupt:
            print("\n[!] Scan interrupted by user.")
            sys.exit(1)
    else:
        subprocess.call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return xml_path

# ─── XML PARSER ───────────────────────────────────────────────────────────────
def parse_nmap_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
    except:
        return []

    root = tree.getroot()
    report = []

    for host in root.findall("host"):
        if host.find("status").attrib.get("state") != "up":
            continue

        ip = host.find("address").attrib.get("addr")
        entry = {"ip": ip, "ports": []}

        for port in host.findall(".//port"):
            entry["ports"].append({
                "port": port.attrib.get("portid"),
                "protocol": port.attrib.get("protocol"),
                "state": port.find("state").attrib.get("state"),
                "service": port.find("service").attrib.get("name", "unknown")
            })
        report.append(entry)
    return report

# ─── OUTPUT HANDLER ───────────────────────────────────────────────────────────
def save_outputs(data, timestamp, target, formats, outdir, verbose=False):
    safe = target.replace('/', '_').replace('.', '_')

    if "json" in formats:
        path = os.path.join(outdir, f"nmap_scan_{timestamp}_{safe}.json")
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        if verbose: print(f"[✓] JSON saved: {path}")

    if "md" in formats:
        path = os.path.join(outdir, f"nmap_summary_{timestamp}_{safe}.md")
        with open(path, "w") as f:
            f.write(f"# Nmap Scan Summary\n\n")
            f.write(f"_Target: {target}_  \n_Generated: {timestamp}_\n\n")
            for host in data:
                f.write(f"## Host: `{host['ip']}`\n")
                for p in host["ports"]:
                    f.write(f"- `{p['protocol']}/{p['port']}` → **{p['service']}** ({p['state']})\n")
                f.write("\n---\n\n")
        if verbose: print(f"[✓] Markdown saved: {path}")

# ─── MAIN EXECUTION ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not check_nmap_installed():
        suggest_nmap_installation()

    parser = argparse.ArgumentParser(description="PrinterReaper - Nmap Launcher")
    parser.add_argument('--ip', help='Scan a single IP address')
    parser.add_argument('--range', help='Scan an IP range (e.g. 192.168.1.10-192.168.1.50)')
    parser.add_argument('--file', help='Scan a list of IPs from file (one per line)')
    parser.add_argument('--subnet', help='Use "auto" to choose from local interfaces')

    parser.add_argument('--output', help='Output formats: json,md (comma-separated)', default="")
    parser.add_argument('--outdir', help='Output directory (default: ./results)', default="results")
    parser.add_argument('--verbose', action='store_true', help='Enable detailed logs')

    args = parser.parse_args()

    if len(sys.argv) == 1:
        print("[i] No parameters provided. Defaulting to: --subnet auto\n")
        args.subnet = "auto"

    formats = [f.strip().lower() for f in args.output.split(",") if f.strip()]
    if formats and args.verbose:
        print(f"[DEBUG] Output formats: {formats}")
        print(f"[DEBUG] Output directory: {args.outdir}")

    targets = build_target_list(args)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for target in targets:
        print(f"\n[+] Scanning: {target}")
        xml_path = run_nmap_scan(target, timestamp, args.outdir, formats, verbose=args.verbose)

        if xml_path and os.path.exists(xml_path):
            result = parse_nmap_xml(xml_path)
            if args.verbose:
                print(f"[DEBUG] Parsed {len(result)} host(s)")
            if formats:
                save_outputs(result, timestamp, target, formats, args.outdir, verbose=args.verbose)
            else:
                print("[i] No output format specified. Skipping report generation.")
        elif not formats:
            print("[i] No report generation requested. Scan complete.")
        else:
            print(f"[!] No XML output found for target: {target}")
