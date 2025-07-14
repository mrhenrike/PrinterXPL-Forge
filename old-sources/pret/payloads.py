import socket, re, os
def load_payload(filepath, substitutions={}):
    base_dir = os.path.dirname(os.path.dirname(__file__))  # volta da pasta /pret
    full_path = os.path.join(base_dir, filepath)

    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
        placeholders = re.findall(r"\{\{(.*?)\}\}", content)
        missing = [p for p in placeholders if p not in substitutions]
        if missing:
            raise ValueError(f"Missing substitution(s): {', '.join(missing)}")
        for key, value in substitutions.items():
            content = content.replace(f"{{{{{key}}}}}", value)
        return content


def send_payload(ip, port, payload):
    try:
        s = socket.socket()
        s.settimeout(3)
        s.connect((ip, port))
        s.sendall(payload.encode())
        data = b""
        try:
            while True:
                chunk = s.recv(2048)
                if not chunk: break
                data += chunk
        except socket.timeout:
            pass
        s.close()
        return data.decode(errors='ignore')
    except Exception as e:
        return f"[ERROR] {e}"

from datetime import datetime
def run_payload(ip, port, filepath, substitutions={}):
    print(f"[>] Executing payload: {filepath} → {ip}:{port}")
    payload = load_payload(filepath, substitutions)
    response = send_payload(ip, port, payload)
    
    print("[RAW OUTPUT]\n" + response)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"results/output_{ip.replace('.', '_')}_{timestamp}.out"

    with open(out_file, "w", encoding='utf-8') as f:
        f.write(response)

    print(f"[✓] Output saved to: {out_file}")
    return response
