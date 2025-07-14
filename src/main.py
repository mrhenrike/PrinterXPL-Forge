import argparse
import sys
from core.discovery import discovery
from core.capabilities import capabilities
from modules.pjl import pjl
from modules.postscript import postscript
from modules.pcl import pcl

def get_args():
    parser = argparse.ArgumentParser(description="Printer Exploitation Toolkit - PrinterReaper")
    parser.add_argument("target", help="Printer IP address or hostname")
    parser.add_argument("mode", choices=["ps", "pjl", "pcl"], help="Printer language to abuse")
    parser.add_argument("-s", "--safe", help="Verify if language is supported", action="store_true")
    parser.add_argument("-q", "--quiet", help="Suppress warnings and chit-chat", action="store_true")
    parser.add_argument("-d", "--debug", help="Enter debug mode (show traffic)", action="store_true")
    parser.add_argument("-i", "--load", metavar="file", help="Load and run commands from file")
    parser.add_argument("-o", "--log", metavar="file", help="Log raw data sent to the target")
    parser.add_argument("--osint", help="Check target exposure on search engines", action="store_true")
    return parser.parse_args()

def main():
    args = get_args()
    if not args.quiet:
        print(">> Iniciando PrinterReaper (base PRET-Enhanced)\n")

    capabilities(args)

    if args.mode == "ps":
        postscript(args)
    elif args.mode == "pjl":
        shell = pjl(args)
        shell.cmdloop()
    elif args.mode == "pcl":
        pcl(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Execução interrompida pelo usuário.")
        sys.exit(0)
