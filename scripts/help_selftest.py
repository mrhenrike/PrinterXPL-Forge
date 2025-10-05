#!/usr/bin/env python3
"""
Quick self-test for help output across PS and PCL shells.
Runs without connecting to a real printer (uses target='test').
"""
from types import SimpleNamespace
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


