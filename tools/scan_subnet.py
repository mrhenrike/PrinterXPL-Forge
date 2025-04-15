import socket
import ipaddress
import concurrent.futures
import json
import csv
from datetime import datetime

def send_test(ip, port, payload):
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((ip, port))
        s.sendall(payload.encode())
        data = s.recv(1024)
        s.close()
        return data.decode(errors='ignore')
    except:
        return None

def check_host(ip):
    result = {'ip': str(ip), 'PJL': 'closed', 'PS': 'closed'}

    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect((str(ip), 9100))
        s.close()
    except:
        return None  # 9100 closed

    # PJL test
    pjl = send_test(str(ip), 9100, "@PJL INFO STATUS\r\n")
    if pjl: result['PJL'] = 'open'

    # PS test
    ps = send_test(str(ip), 9100, "statusdict /product get ==\n")
    if ps: result['PS'] = 'open'

    print(f"[+] {ip} | PJL: {result['PJL']} | PS: {result['PS']}")
    return result

def save_results(results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join("results", f"printerreaper_scan_{timestamp}.json")
    csv_file = os.path.join("results", f"printerreaper_scan_{timestamp}.csv")

    with open(json_file, "w") as jf:
        json.dump(results, jf, indent=2)

    with open(csv_file, "w", newline='') as cf:
        writer = csv.DictWriter(cf, fieldnames=["ip", "PJL", "PS"])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\n[✓] Exported results to:")
    print(f"    → {json_file}")
    print(f"    → {csv_file}")

def scan_subnet(subnet):
    print(f"[*] Scanning subnet: {subnet}")
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_host, ip) for ip in ipaddress.IPv4Network(subnet)]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r: results.append(r)

    save_results(results)

    print(f"\n[✓] Scan complete. {len(results)} hosts responded on port 9100.")
    print(f"    - PJL enabled : {sum(1 for r in results if r['PJL'] == 'open')}")
    print(f"    - PS enabled  : {sum(1 for r in results if r['PS'] == 'open')}")

if __name__ == '__main__':
    scan_subnet("192.168.18.0/24")
