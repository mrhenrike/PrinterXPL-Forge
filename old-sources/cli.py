# PrinterReaper - Modern Fork of PRET (Printer Exploitation Toolkit)

# Initial project structure based on PRET, adapted for modularity, clarity, and modern CLI style

# CLI principal
# File: cli.py
import argparse
from pret.core import PrinterSession
from pret.payloads import run_payload

def parse_substitutions(sub_list):
    substitutions = {}
    if sub_list:
        for item in sub_list:
            if "=" in item:
                key, val = item.split("=", 1)
                substitutions[key] = val
    return substitutions

def main():
    parser = argparse.ArgumentParser(
        prog='PrinterReaper',
        description='Modern pentest tool for printer exploitation and enumeration',
        epilog='Beware... the reaper prints.')

    parser.add_argument('--host', required=True, help='Target printer IP address')
    parser.add_argument('--module', choices=['pjl', 'ps', 'pcl', 'payload'], required=True, help='Protocol module to use')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--cmd', help='Command to execute (depends on module)')
    group.add_argument('--chain', help='Comma-separated list of payloads to execute in order')
    parser.add_argument('--port', type=int, default=9100, help='Target port (default: 9100)')
    parser.add_argument('--sub', nargs='*', help='Substitutions for payload (key=value)')

    args = parser.parse_args()

    if args.module == "payload":
        subs = parse_substitutions(args.sub)
        if args.chain:
            for path in args.chain.split(","):
                run_payload(args.host, args.port, path.strip(), subs)
        elif args.cmd:
            run_payload(args.host, args.port, args.cmd, subs)
        else:
            print("[!] You must provide --cmd or --chain for module 'payload'")


if __name__ == '__main__':
    main()
