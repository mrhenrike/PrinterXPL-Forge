import socket

class PrinterSession:
    def __init__(self, host, port, module):
        self.host = host
        self.port = port
        self.module = module

    def connect(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((self.host, self.port))
        return s

    def run(self, cmd):
        print(f"[>] Connecting to {self.host}:{self.port} using {self.module.upper()} module...")
        print(f"[+] Executing command: {cmd}")

        connection = self.connect()

        if self.module == "pjl":
            from pret.modules.pjl import PJLModule
            handler = PJLModule(connection)
            result = handler.run(cmd)
            print(result)

        elif self.module == "ps":
            from pret.modules.ps import PSModule
            handler = PSModule(connection)
            result = handler.run(cmd)
            print(result)
        
        elif self.module == "payload":
            from pret.payloads import run_payload
            run_payload(self.host, self.port, cmd)
