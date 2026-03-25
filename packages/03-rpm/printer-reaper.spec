Name:           printer-reaper
Version:        %{?version_override}%{!?version_override:3.14.0}
Release:        1%{?dist}
Summary:        Advanced Printer Penetration Testing Toolkit
License:        MIT
URL:            https://github.com/mrhenrike/PrinterReaper
Source0:        printer-reaper-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip

Requires:       python3 >= 3.8
Requires:       python3-requests >= 2.31.0
Requires:       python3-urllib3 >= 2.0.0
Requires:       python3-colorama
Requires:       python3-pyyaml

Recommends:     python3-pysnmp
Recommends:     python3-scikit-learn
Recommends:     python3-impacket
Recommends:     nmap
Recommends:     net-snmp-utils

%description
PrinterReaper is a modular framework for security assessment of network printers.
It covers PJL, PostScript, PCL and ESC/P across common protocols:
RAW/9100, IPP/631, LPD/515, HTTP/HTTPS, SNMP, FTP, SMB and Telnet.

%prep
%autosetup -n PrinterReaper-%{version}

%build
%py3_build

%install
%py3_install

install -d %{buildroot}%{_datadir}/%{name}/wordlists
install -m 644 wordlists/*.txt %{buildroot}%{_datadir}/%{name}/wordlists/

install -d %{buildroot}%{_datadir}/%{name}/xpl
cp -r xpl/. %{buildroot}%{_datadir}/%{name}/xpl/

install -d %{buildroot}%{_datadir}/%{name}
install -m 644 config.json.example %{buildroot}%{_datadir}/%{name}/config.json.example

install -d %{buildroot}%{_mandir}/man1
install -m 644 packages/man/printer-reaper.1 %{buildroot}%{_mandir}/man1/printer-reaper.1

%files
%license LICENSE
%doc README.md
%{_bindir}/printer-reaper
%{_bindir}/printerreaper
%{python3_sitelib}/*
%{_datadir}/%{name}/
%{_mandir}/man1/printer-reaper.1*

%changelog
* Tue Mar 24 2026 Andre Henrique <mrhenrike@users.noreply.github.com> - 3.14.0-1
- Unified packaging hub under packages/
- Added RPM build scripts and spec baseline

