#!/usr/bin/env python3
import os
import sys
from types import SimpleNamespace

ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.modules.ps import ps
from src.modules.pcl import pcl


class DummyConn:
    def __init__(self):
        self._sock = None
    def close(self):
        pass


def run_shell(ShellClass, mode: str, topic: str):
    args = SimpleNamespace(debug=False, quiet=True, mode=mode, target='test', log=None, load=None)
    shell = ShellClass(args)
    shell.conn = DummyConn()
    print(f"\n=== HELP in {mode.upper()} ===")
    shell.do_help("")
    print(f"=== HELP {topic} ===")
    shell.do_help(topic)


if __name__ == "__main__":
    run_shell(ps, 'ps', 'exec_ps')
    run_shell(pcl, 'pcl', 'execute')


