# PrinterReaper — Package Build Guide

This directory contains the packaging infrastructure to distribute
`printer-reaper` as an OS-level package on Debian/Ubuntu/Kali, RHEL/Fedora/Rocky,
and as a PyPI package installable via `pip`.

---

## Prerequisites (all paths)

```bash
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper
```

---

## Path 1 — PyPI (pip install printer-reaper)

### Build

```bash
pip install build twine

# Build wheel + sdist
python -m build

# Outputs:
#   dist/printer_reaper-3.7.0-py3-none-any.whl
#   dist/printer_reaper-3.7.0.tar.gz
```

### Test locally before publishing

```bash
pip install dist/printer_reaper-3.7.0-py3-none-any.whl
printer-reaper --version
```

### Publish to TestPyPI first

```bash
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ printer-reaper
```

### Publish to PyPI

```bash
twine upload dist/*
```

### Users install with

```bash
pip install printer-reaper                    # core only
pip install printer-reaper[full]              # core + SNMP + SMB + OSINT + ML
pip install printer-reaper[osint]             # + Shodan + Censys
pip install printer-reaper[ml]               # + scikit-learn
```

---

## Path 2 — Debian/Ubuntu/Kali (.deb)

### Build environment

```bash
# Debian/Ubuntu/Kali
sudo apt install debhelper dh-python python3-all python3-setuptools \
                 python3-requests python3-urllib3 python3-colorama python3-yaml

cd PrinterReaper
dpkg-buildpackage -us -uc -b

# Output: ../printer-reaper_3.7.0-1_all.deb
```

### Install

```bash
sudo dpkg -i ../printer-reaper_3.7.0-1_all.deb
sudo apt-get install -f    # resolve any missing dependencies
printer-reaper --version
```

### Uninstall

```bash
sudo apt remove printer-reaper
```

### Where files land after install

| Path | Content |
|------|---------|
| `/usr/bin/printer-reaper` | Main executable |
| `/usr/bin/printerreaper` | Alias |
| `/usr/share/printer-reaper/wordlists/` | Default wordlists |
| `/usr/share/printer-reaper/xpl/` | Exploit library |
| `/usr/share/printer-reaper/config.json.example` | Config template |
| `/usr/share/man/man1/printer-reaper.1.gz` | Man page |
| `/usr/lib/python3/dist-packages/` | Python modules |

### Kali Linux (kali-rolling)

To submit to the official Kali repository, follow the Kali packaging guide:
https://www.kali.org/docs/development/submitting-a-tool-to-kali/

For personal/team use, install the .deb directly or use:
```bash
pipx install printer-reaper    # isolated from system Python
```

---

## Path 3 — RPM (RHEL / Fedora / Rocky / AlmaLinux)

### Build environment

```bash
# Fedora / RHEL / Rocky
sudo dnf install rpm-build python3-devel python3-setuptools rpmdevtools

rpmdev-setuptree    # creates ~/rpmbuild/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Copy spec file
cp packaging/rpm/printer-reaper.spec ~/rpmbuild/SPECS/

# Download source tarball or create from local repo
cd ..
tar czf ~/rpmbuild/SOURCES/printer-reaper-3.7.0.tar.gz \
    --transform 's|^PrinterReaper|PrinterReaper-3.7.0|' PrinterReaper/

# Build
rpmbuild -ba ~/rpmbuild/SPECS/printer-reaper.spec

# Output:
#   ~/rpmbuild/RPMS/noarch/printer-reaper-3.7.0-1.fc40.noarch.rpm
#   ~/rpmbuild/SRPMS/printer-reaper-3.7.0-1.fc40.src.rpm
```

### Install

```bash
sudo dnf install ~/rpmbuild/RPMS/noarch/printer-reaper-3.7.0-1.fc40.noarch.rpm
printer-reaper --version
```

---

## Path 4 — pipx (recommended for isolated installs)

`pipx` installs the tool in an isolated virtual environment but exposes
the `printer-reaper` command globally. No root required.

```bash
# Install pipx if not available
pip install --user pipx
pipx ensurepath

# Install from PyPI (after publishing)
pipx install printer-reaper

# Install from local checkout (development)
pipx install --editable .

# Inject optional extras
pipx inject printer-reaper shodan censys scikit-learn
```

---

## Path 5 — Homebrew (macOS / Linux)

Create a formula at `packaging/homebrew/printer-reaper.rb`:

```ruby
class PrinterReaper < Formula
  include Language::Python::Virtualenv

  desc "Advanced Printer Penetration Testing Toolkit"
  homepage "https://github.com/mrhenrike/PrinterReaper"
  url "https://github.com/mrhenrike/PrinterReaper/archive/refs/tags/v3.7.0.tar.gz"
  version "3.7.0"
  license "MIT"

  depends_on "python@3.11"

  resource "requests" do
    url "https://files.pythonhosted.org/packages/..."
  end

  def install
    virtualenv_install_with_resources
    bin.install "printer-reaper.py" => "printer-reaper"
  end
end
```

Submit to Homebrew-core or a custom tap.

---

## Wordlist path resolution (installed vs development)

When installed as a system package, wordlists are at:
`/usr/share/printer-reaper/wordlists/`

When running from source:
`./wordlists/`

`wordlist_loader.py` resolves the path in this order:
1. Explicit `--bf-wordlist FILE` argument
2. `wordlists/` relative to the current working directory
3. `wordlists/` relative to the script location
4. `/usr/share/printer-reaper/wordlists/`

---

## Version bump checklist

Before packaging a new release:

1. Update `src/version.py` — `__version__`, `__version_info__`, `__release_date__`
2. Update `pyproject.toml` — `version`
3. Update `debian/changelog` — add new entry at top
4. Update `packaging/rpm/printer-reaper.spec` — `Version:` and `%changelog`
5. `git tag v3.7.0 && git push origin v3.7.0`
6. `python -m build && twine upload dist/*`
7. `dpkg-buildpackage -us -uc -b`
8. `rpmbuild -ba ~/rpmbuild/SPECS/printer-reaper.spec`
