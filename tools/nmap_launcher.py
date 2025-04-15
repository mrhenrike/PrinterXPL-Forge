import os
import sys
import json
import argparse
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime
import platform
import ipaddress
import psutil

def check_nmap_installed():
    try:
        subprocess.check_output(["nmap", "-V"])
        return True
    except Exception:
        return False

def suggest_nmap_installation():
    system = platform.system()
    print("\n[!] Nmap is not installed or not in your system PATH.\n")
    print("➡️  Please install it before using this tool.\n")

    if system == "Windows":
        print("🔗 Download: https://nmap.org/dist/nmap-7.95-setup.exe")
        print("📌 Enable 'Add Nmap to PATH' during installation")
    elif system == "Linux":
        print("📦 Debian/Ubuntu: sudo apt install nmap")
    elif system == "Darwin":
        print("🍺 macOS (Homebrew): brew install nmap")
    else:
        print("🔗 See: https://nmap.org/download.html")

    sys.exit(1)

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

def build_target_list(args):
    if args.ip:
        return [args.ip]
    elif args.range:
        try:
            start_ip, end_ip = args.range.split("-")
            ips = [str(ip) for ip in ipaddress.summarize_address_range(ipaddress.IPv4Address(start_ip), ipaddress.IPv4Address(end_ip))]
            return ips
        except:
            print("[!] Invalid IP range format.")
            sys.exit(1)
    elif args.file:
        try:
            with open(args.file, "r") as f:
                return [line.strip() for line in f if line.strip()]
        except:
            print(f"[!] Could not read file: {args.file}")
            sys.exit(1)
    elif args.subnet == "auto":
        return choose_subnet_interactively()
    else:
        print("[!] No valid target provided.")
        sys.exit(1)

def run_nmap_scan(target, timestamp, outdir):
    safe_name = target.replace('/', '_').replace('.', '_')
    base = os.path.join(outdir, f"nmap_scan_{timestamp}_{safe_name}")
    os.makedirs(outdir, exist_ok=True)

    os.system(
        f"nmap -p 80,443,515,631,9100,161 "
        f"-sS -sU -A -T4 "
        f"--script \"default,discovery,safe,version,snmp*,http*,banner,vuln\" "
        f"--script-args=unsafe=1,snmpcommunity=public "
        f"-oA {base} "
        f"{target}"
    )
    return base + ".xml"

def parse_nmap_xml(xml_file):
    try:
        tree = ET.parse(xml_file)
    except:
        return []

    root = tree.getroot()
    report = []

    for host in root.findall("host"):
        status = host.find("status").attrib.get("state")
        if status != "up":
            continue

        addr = host.find("address").attrib.get("addr")
        item = {"ip": addr, "ports": []}

        for port in host.findall(".//port"):
            portid = port.attrib.get("portid")
            protocol = port.attrib.get("protocol")
            state = port.find("state").attrib.get("state")
            service = port.find("service").attrib.get("name", "unknown")
            item["ports"].append({
                "port": portid,
                "protocol": protocol,
                "state": state,
                "service": service
            })

        report.append(item)
    return report

def save_outputs(data, timestamp, target, formats, outdir):
    safe = target.replace('/', '_').replace('.', '_')
    if "json" in formats:
        with open(os.path.join(outdir, f"nmap_scan_{timestamp}_{safe}.json"), "w") as f:
            json.dump(data, f, indent=2)

    if "md" in formats:
        with open(os.path.join(outdir, f"nmap_summary_{timestamp}_{safe}.md"), "w") as f:
            f.write(f"# Nmap Printer Scan Summary\n\n")
            f.write(f"_Target: {target}_  \n_Generated: {timestamp}_\n\n")
            for host in data:
                f.write(f"## Host: `{host['ip']}`\n\n")
                for p in host["ports"]:
                    f.write(f"- `{p['protocol']}/{p['port']}` → **{p['service']}** ({p['state']})\n")
                f.write("\n---\n\n")

if __name__ == "__main__":
    if not check_nmap_installed():
        suggest_nmap_installation()

    parser = argparse.ArgumentParser(description="Nmap launcher for PrinterReaper")
    parser.add_argument('--ip', help='Single IP to scan')
    parser.add_argument('--range', help='IP range (e.g. 192.168.1.10-192.168.1.50)')
    parser.add_argument('--file', help='File with list of IPs')
    parser.add_argument('--subnet', help='Use --subnet auto to select from local interfaces')

    parser.add_argument('--output', help='Output formats: json,md (comma-separated)', default="")
    parser.add_argument('--outdir', help='Output directory (default: ./results)', default="results")

    args = parser.parse_args()

    # Fallback to auto subnet if nothing was passed
    if len(sys.argv) == 1:
        print("[i] No parameters provided. Defaulting to: --subnet auto\n")
        args.subnet = "auto"

    formats = [fmt.strip().lower() for fmt in args.output.split(",") if fmt.strip()]
    if formats:
        os.makedirs(args.outdir, exist_ok=True)

    targets = build_target_list(args)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for target in targets:
        print(f"\n[+] Scanning: {target}")
        xml_path = run_nmap_scan(target, timestamp, args.outdir)
        if os.path.exists(xml_path):
            result = parse_nmap_xml(xml_path)
            if formats:
                save_outputs(result, timestamp, target, formats, args.outdir)
                print(f"[✓] Reports saved to: {args.outdir}")
            else:
                print("[i] No output format specified. Skipping report generation.")
        else:
            print(f"[!] Nmap output missing for {target}")
