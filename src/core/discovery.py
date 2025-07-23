#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import subprocess
import ipaddress
import shutil
from utils.helper import output, conv
from core.osdetect import get_os

# SNMP OIDs we’ll query
OID_HRDEV_TYPE            = '1.3.6.1.2.1.25.3.2.1.2.1'
OID_HRDEV_DESCR           = '1.3.6.1.2.1.25.3.2.1.3.1'
OID_SYS_UPTIME            = '1.3.6.1.2.1.1.3.0'
OID_PR_STATUS             = '1.3.6.1.2.1.43.16.5.1.2.1.1'
OID_PR_INTERPRETER        = '1.3.6.1.2.1.43.16.5.1.2.1.2'

# HOST-RESOURCES-MIB Printer Table
OID_HRPRINTER_STATUS      = '1.3.6.1.2.1.25.3.5.1.1.1'
OID_HRPRINTER_ERROR_STATE = '1.3.6.1.2.1.25.3.5.1.2.1'
OID_HRPRINTER_JOB_COUNT   = '1.3.6.1.2.1.25.3.5.1.3.1'

# Printer-MIB Supplies & Alerts
OID_PRT_MARKER_SUPPLY_DESC  = '1.3.6.1.2.1.43.11.1.1.6.1.1'
OID_PRT_MARKER_SUPPLY_TYPE  = '1.3.6.1.2.1.43.11.1.1.2.1.1'
OID_PRT_MARKER_SUPPLY_LEVEL = '1.3.6.1.2.1.43.11.1.1.9.1.1'
OID_PRT_INPUT_MEDIA_TYPE    = '1.3.6.1.2.1.43.11.1.1.2.1.1'
OID_PRT_INPUT_STATUS        = '1.3.6.1.2.1.43.11.1.1.8.1.1'
OID_PRT_ALERTS_VALUE        = '1.3.6.1.2.1.43.18.1.1.8.1.1'

# ENTITY-MIB Physical Entities
OID_ENT_PHYS_DESCR         = '1.3.6.1.2.1.47.1.1.1.1.2'
OID_ENT_PHYS_NAME          = '1.3.6.1.2.1.47.1.1.1.1.7'
OID_ENT_PHYS_FIRMWARE_REV  = '1.3.6.1.2.1.47.1.1.1.1.10'
OID_ENT_PHYS_SERIAL        = '1.3.6.1.2.1.47.1.1.1.1.11'
OID_ENT_PHYS_MODEL_NAME    = '1.3.6.1.2.1.47.1.1.1.1.13'


def parse_selection(sel, max_index):
    sel = sel.strip().lower()
    if sel in ('all', 'a', ''):
        return list(range(1, max_index + 1))
    chosen = set()
    for part in sel.split(','):
        if '-' in part:
            start, end = part.split('-', 1)
            chosen.update(range(int(start), int(end) + 1))
        else:
            chosen.add(int(part))
    return sorted(i for i in chosen if 1 <= i <= max_index)


def _get_local_networks(os_type):
    """
    Return a list of IPv4 /24 networks on UP, non-loopback,
    non-link-local interfaces for Linux, WSL and Windows.
    """
    raw = []

    # Linux / WSL
    if os_type in ('linux', 'wsl'):
        try:
            out = subprocess.check_output(
                ['ip', '-o', '-f', 'inet', 'addr', 'show', 'up'],
                text=True
            )
            for line in out.splitlines():
                parts = line.split()
                iface = parts[1].rstrip(':')
                cidr  = next((p for p in parts if '/' in p), None)
                if not cidr or iface == 'lo':
                    continue
                raw.append(ipaddress.ip_network(cidr, strict=False))
        except Exception as e:
            output().warning(f"Could not list Linux interfaces: {e}")

    # Windows / WSL
    if os_type in ('windows', 'wsl'):
        pwsh = shutil.which('powershell.exe') or shutil.which('pwsh.exe')
        if pwsh:
            try:
                cmd = [
                    pwsh, '-NoProfile', '-Command',
                    "Get-NetIPAddress -AddressFamily IPv4 "
                    "| Where { $_.IPAddress -ne '127.0.0.1' } "
                    "| Select -ExpandProperty IPAddress"
                ]
                out = subprocess.check_output(cmd, text=True)
                for ip in out.splitlines():
                    try:
                        raw.append(ipaddress.ip_network(f"{ip}/24", strict=False))
                    except:
                        pass
            except Exception as e:
                output().warning(f"Could not list Windows interfaces: {e}")
        else:
            output().warning("PowerShell not found; skipping Windows IPs.")

    # dedupe and filter out loopback/link-local
    uniq = []
    for net in raw:
        na = net.network_address
        if na.is_loopback or na.is_link_local:
            continue
        if net not in uniq:
            uniq.append(net)
    return uniq


def _snmp_get(ip, oid):
    """
    Run snmpget and return the value or None.
    """
    cmd = shutil.which('snmpget')
    if not cmd:
        return None
    try:
        return subprocess.check_output(
            [cmd, '-v1', '-c', 'public', '-Oqv', '-t', '1', '-r', '1', f'{ip}:161', oid],
            stderr=subprocess.DEVNULL,
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        return None


class discovery:
    def __init__(self, usage=False):
        os_type = get_os()
        print(f"Detected OS: {os_type}")
        if os_type == 'unsupported':
            output().warning("This OS is not supported for SNMP-based discovery.")
            return

        if usage:
            print("No target given — discovering printers on local network.")
            print("Press CTRL+C at any time to cancel.\n")

        if not shutil.which('snmpget'):
            output().warning("Please install 'snmpget' (e.g. apt install snmp).")
            return

        networks = _get_local_networks(os_type)
        if not networks:
            output().warning("No eligible networks found to scan.")
            return

        print(f"Found {len(networks)} network(s) to consider:")
        for idx, net in enumerate(networks, 1):
            hosts = net.num_addresses - 2 if net.num_addresses > 2 else net.num_addresses
            print(f"  [{idx}] {net} ({hosts} hosts)")

        sel = input("\nSelect networks to scan [e.g. 1,1-3,all]: ")
        chosen = parse_selection(sel, len(networks))
        if not chosen:
            print("Nothing selected, exiting.")
            return

        verb = input("Verbose probing? [y/N]: ").strip().lower()
        verbose = verb in ('y', 'yes')

        results = {}
        total = 0
        try:
            for i in chosen:
                net = networks[i - 1]
                print(f"\nScanning {net} (Ctrl+C to cancel)...")
                for host in net.hosts():
                    ip = str(host)
                    total += 1

                    typ = _snmp_get(ip, OID_HRDEV_TYPE)
                    if typ != '1.3.6.1.2.1.25.3.1.5':
                        if verbose:
                            print(f"  {ip}: not a printer ({typ})")
                        continue

                    # collect all SNMP fields
                    descr       = _snmp_get(ip, OID_HRDEV_DESCR) or '?'
                    upv         = _snmp_get(ip, OID_SYS_UPTIME)
                    uptime      = conv().elapsed(int(upv), 100, True) if upv and upv.isdigit() else '?'
                    pr_status   = _snmp_get(ip, OID_PR_STATUS) or '?'
                    interp      = _snmp_get(ip, OID_PR_INTERPRETER) or '?'
                    hp_status   = _snmp_get(ip, OID_HRPRINTER_STATUS) or '?'
                    err_state   = _snmp_get(ip, OID_HRPRINTER_ERROR_STATE) or '?'
                    job_count   = _snmp_get(ip, OID_HRPRINTER_JOB_COUNT) or '?'
                    m_desc      = _snmp_get(ip, OID_PRT_MARKER_SUPPLY_DESC) or '?'
                    m_type      = _snmp_get(ip, OID_PRT_MARKER_SUPPLY_TYPE) or '?'
                    m_level     = _snmp_get(ip, OID_PRT_MARKER_SUPPLY_LEVEL) or '?'
                    in_media    = _snmp_get(ip, OID_PRT_INPUT_MEDIA_TYPE) or '?'
                    in_status   = _snmp_get(ip, OID_PRT_INPUT_STATUS) or '?'
                    alerts      = _snmp_get(ip, OID_PRT_ALERTS_VALUE) or '?'
                    phys_descr  = _snmp_get(ip, OID_ENT_PHYS_DESCR) or '?'
                    phys_name   = _snmp_get(ip, OID_ENT_PHYS_NAME) or '?'
                    phys_fw      = _snmp_get(ip, OID_ENT_PHYS_FIRMWARE_REV) or '?'
                    phys_serial = _snmp_get(ip, OID_ENT_PHYS_SERIAL) or '?'
                    phys_model  = _snmp_get(ip, OID_ENT_PHYS_MODEL_NAME) or '?'

                    results[ip] = [
                        descr, uptime, pr_status, interp,
                        hp_status, err_state, job_count,
                        m_desc, m_type, m_level,
                        in_media, in_status, alerts,
                        phys_name, phys_model, phys_serial, phys_fw
                    ]

                    if verbose:
                        print(f"  {ip}:")
                        print(f"    Description: {descr}")
                        print(f"    Uptime:      {uptime}")
                        print(f"    PJL Status:  {pr_status}")
                        print(f"    Interpreter: {interp}")
                        print(f"    hrStatus:    {hp_status}")
                        print(f"    Errors:      {err_state}")
                        print(f"    Jobs:        {job_count}")
                        print(f"    Supplies:    {m_desc} / {m_type} @ {m_level}")
                        print(f"    Input:       {in_media} / {in_status}")
                        print(f"    Alerts:      {alerts}")
                        print(f"    Entity:      {phys_name} ({phys_model})")
                        print(f"    Serial:      {phys_serial}")
                        print(f"    FW Rev:      {phys_fw}")
                    else:
                        print(f"  {ip}: Printer → {descr}, uptime={uptime}, status={pr_status}")

        except KeyboardInterrupt:
            print()
            output().warning("[!] Discovery interrupted by user. Exiting...\n")

        print(f"\nProbed {total} hosts in total.\n")
        if results:
            print("Discovered printers:")
            hdr = (
                'address',
                ('descr','uptime','pjl_status','interp','hr_status','errors',
                 'jobs','sup_desc','sup_type','sup_lvl',
                 'in_media','in_status','alerts',
                 'ent_name','ent_model','ent_serial','ent_fw')
            )
            output().discover(hdr)
            output().hline(79)
            for entry in sorted(results.items(), key=lambda i: socket.inet_aton(i[0])):
                output().discover(entry)
            print()
        else:
            output().info("No printers found via SNMP scan")
            print()
