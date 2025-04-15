# File: tools/autodetect.py
import socket

def send_test(ip, port, payload):
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((ip, port))
        s.sendall(payload.encode())
        data = s.recv(2048)
        s.close()
        return data.decode(errors='ignore')
    except Exception:
        return None

def detect_printer(ip):
    print(f"[*] Scanning {ip}...")

    result = {}

    # Test PJL
    pjl_payload = "@PJL INFO STATUS\r\n"
    pjl = send_test(ip, 9100, pjl_payload)
    result['PJL'] = 'open' if pjl else 'closed'

    # Test PostScript
    ps_payload = "statusdict /product get ==\n"
    ps = send_test(ip, 9100, ps_payload)
    result['PS'] = 'open' if ps else 'closed'

    print(f"[+] {ip} | PJL: {result['PJL']} | PS: {result['PS']}")
    return result

# Run against single IP (test)
if __name__ == '__main__':
    detect_printer("192.168.18.37")
