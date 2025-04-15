import socket, ipaddress, concurrent.futures, json, csv, os
from datetime import datetime
from hashlib import sha256
import requests
from pysnmp.hlapi import *

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

from pysnmp.hlapi import *
def get_snmp_info(ip):
    info = {}
    oids = [
        ("1.3.6.1.2.1.1.1.0", "sysDescr"),
        ("1.3.6.1.2.1.1.5.0", "sysName"),
        ("1.3.6.1.2.1.1.6.0", "sysLocation"),
        ("1.3.6.1.2.1.1.4.0", "sysContact"),
        ("1.3.6.1.2.1.25.3.2.1.3.1", "hrDeviceDescr"),
        ("1.3.6.1.2.1.43.5.1.1.16.1", "prtGeneralSerialNumber"),
        ("1.3.6.1.2.1.43.5.1.1.17.1", "prtGeneralModel"),
        ("1.3.6.1.2.1.43.5.1.1.2.1", "prtGeneralPrinterName"),
        ("1.3.6.1.2.1.43.10.2.1.4.1.1", "prtMarkerLifeCount"),
        ("1.3.6.1.2.1.43.11.1.1.6.1.1", "prtAlertDescription")
    ]
    for oid, key in oids:
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData('public', mpModel=0),
                UdpTransportTarget((ip, 161), timeout=2.0, retries=0),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            if not errorIndication and not errorStatus:
                for varBind in varBinds:
                    info[key] = str(varBind[1])
        except:
            continue
    return info if info else None


def get_http_banner(ip):
    try:
        response = requests.get(f"http://{ip}", timeout=2)
        return {
            "title": response.text.split("<title>")[1].split("</title>")[0].strip() if "<title>" in response.text else "N/A",
            "headers": dict(response.headers)
        }
    except:
        return None

def generate_fingerprint(data):
    raw = json.dumps(data, sort_keys=True).encode()
    return sha256(raw).hexdigest()

def check_host(ip):
    result = {'ip': str(ip), 'PJL': 'closed', 'PS': 'closed'}

    try:
        s = socket.socket()
        s.settimeout(1)
        s.connect((str(ip), 9100))
        s.close()
    except:
        return None  # port 9100 closed

    pjl = send_test(str(ip), 9100, "@PJL INFO STATUS\r\n")
    if pjl: result['PJL'] = 'open'

    ps = send_test(str(ip), 9100, "statusdict /product get ==\n")
    if ps: result['PS'] = 'open'

    result['SNMP'] = get_snmp_info(str(ip)) or {}
    result['HTTP'] = get_http_banner(str(ip)) or {}
    result['fingerprint_hash'] = generate_fingerprint(result)

    print(f"[+] {ip} | PJL: {result['PJL']} | PS: {result['PS']}")
    return result

def save_results(results):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = os.path.join("results", f"printerreaper_scan_{timestamp}.json")
    csv_file = os.path.join("results", f"printerreaper_scan_{timestamp}.csv")

    with open(json_file, "w") as jf:
        json.dump(results, jf, indent=2)

    with open(csv_file, "w", newline='') as cf:
        fieldnames = ["ip", "PJL", "PS", "SNMP.sysDescr", "SNMP.sysName", "HTTP.title", "fingerprint_hash"]
        writer = csv.DictWriter(cf, fieldnames=fieldnames)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "ip": r["ip"],
                "PJL": r["PJL"],
                "PS": r["PS"],
                "SNMP.sysDescr": r.get("SNMP", {}).get("sysDescr", ""),
                "SNMP.sysName": r.get("SNMP", {}).get("sysName", ""),
                "HTTP.title": r.get("HTTP", {}).get("title", ""),
                "fingerprint_hash": r["fingerprint_hash"]
            })

    print(f"\n[✓] Exported to {json_file} and {csv_file}")
    return json_file, csv_file

def scan_subnet(subnet):
    print(f"[*] Scanning subnet {subnet} for printers on port 9100...")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(check_host, ip) for ip in ipaddress.IPv4Network(subnet)]
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r: results.append(r)
    print(f"\n[✓] Found {len(results)} device(s) with port 9100 open.")
    return results

if __name__ == "__main__":
    scan_range = "192.168.18.0/24"
    results = scan_subnet(scan_range)
    save_results(results)
