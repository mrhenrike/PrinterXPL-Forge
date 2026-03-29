# PrinterReaper (pt-BR)

*Kit avançado de testes de penetração em impressoras de rede*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Licença](https://img.shields.io/badge/Licença-MIT-green)](LICENSE)
[![Versão](https://img.shields.io/badge/versão-3.14.0-red)](https://github.com/mrhenrike/PrinterReaper/releases)

**English (en-US):** [README.md](README.md) · [CONTRIBUTING.md](CONTRIBUTING.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

**Wiki:** [English](https://github.com/mrhenrike/PrinterReaper/wiki) · [Português](https://github.com/mrhenrike/PrinterReaper/wiki/Home-pt-BR)

---

## O que é

Framework modular para **avaliação de segurança** de impressoras em rede: linguagens **PJL, PostScript, PCL, ESC/P**, protocolos **RAW, IPP, LPD, SMB, HTTP, SNMP, FTP, Telnet**, biblioteca de exploits, motor de credenciais com **wordlists externas** (zero passwords hardcoded), fingerprinting com ML, integração **NVD/CVE**, movimento lateral, firmware, **Cross-Site Printing**, entre outros.

## Início rápido

```bash
git clone https://github.com/mrhenrike/PrinterReaper.git
cd PrinterReaper
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python printer-reaper.py --version
python printer-reaper.py 192.168.1.100 --scan
```

## Documentação completa

A documentação detalhada (comandos, matriz de ataque, descoberta online, brute-force, etc.) está no **[README em inglês](README.md)** e na **[wiki bilíngue](https://github.com/mrhenrike/PrinterReaper/wiki)**.

## Aviso legal

Uso **apenas** em sistemas próprios ou com **autorização explícita**. MIT — ver `LICENSE`.

**Autor:** Andre Henrique ([@mrhenrike](https://github.com/mrhenrike))
