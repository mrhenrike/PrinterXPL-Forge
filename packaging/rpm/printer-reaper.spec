Name:           printer-reaper
Version:        3.7.0
Release:        1%{?dist}
Summary:        Advanced Printer Penetration Testing Toolkit
License:        MIT
URL:            https://github.com/mrhenrike/PrinterReaper
Source0:        https://github.com/mrhenrike/PrinterReaper/archive/refs/tags/v%{version}.tar.gz#/printer-reaper-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip

Requires:       python3 >= 3.8
Requires:       python3-requests >= 2.31.0
Requires:       python3-urllib3 >= 2.0.0
Requires:       python3-colorama
Requires:       python3-pyyaml

# Optional — install for full functionality
Recommends:     python3-pysnmp
Recommends:     python3-scikit-learn
Recommends:     python3-impacket
Recommends:     nmap
Recommends:     net-snmp-utils

%description
PrinterReaper is a complete, modular framework for security assessment
of network printers covering PJL, PostScript, PCL, and ESC/P printer
languages across all common network protocols (RAW/9100, IPP/631,
LPD/515, HTTP/HTTPS, SNMP, FTP, SMB, Telnet).

Features:
- Banner grab + NVD/CVE lookup with ML-assisted fingerprinting
- 39+ exploit modules (ExploitDB, Metasploit, Research)
- Wordlist-driven brute-force (HTTP, FTP, SNMP, Telnet)
- Lateral movement via SSRF/IPP, network mapping, LDAP hash capture
- Storage audit (FTP, web file manager, SNMP MIB, saved jobs)
- Firmware analysis, NVRAM read/write, factory reset
- Cross-Site Printing (XSP) payload generator
- Online discovery via Shodan/Censys
- Interactive PJL/PS/PCL shell with 109+ commands

%prep
%autosetup -n PrinterReaper-%{version}

%build
%py3_build

%install
%py3_install

# Install wordlists
install -d %{buildroot}%{_datadir}/%{name}/wordlists
install -m 644 wordlists/*.txt %{buildroot}%{_datadir}/%{name}/wordlists/

# Install exploit library
install -d %{buildroot}%{_datadir}/%{name}/xpl
cp -r xpl/. %{buildroot}%{_datadir}/%{name}/xpl/

# Install config example
install -m 644 config.json.example %{buildroot}%{_datadir}/%{name}/config.json.example

# Install man page
install -d %{buildroot}%{_mandir}/man1
install -m 644 man/man1/printer-reaper.1 %{buildroot}%{_mandir}/man1/printer-reaper.1

%files
%license LICENSE
%doc README.md
%{_bindir}/printer-reaper
%{_bindir}/printerreaper
%{python3_sitelib}/*
%{_datadir}/%{name}/
%{_mandir}/man1/printer-reaper.1*

%changelog
* Tue Mar 25 2026 Andre Henrique <mrhenrike@users.noreply.github.com> - 3.7.0-1
- v3.7.0: Zero hardcoded credentials, wordlist engine, draw.io diagrams
- Replace SVG diagrams with PNG + draw.io source files
- Restore União Geek branding to README
- Add PRET benchmark comparison table

* Mon Mar 24 2026 Andre Henrique <mrhenrike@users.noreply.github.com> - 3.6.2-1
- v3.6.2: LDAP NTLM hash capture, CVE-2024-51978, 5 new vendors

* Mon Mar 24 2026 Andre Henrique <mrhenrike@users.noreply.github.com> - 3.0.0-1
- Initial RPM package
- Rewritten from PRET with IPv6, SMB, ML, NVD/CVE scanner
