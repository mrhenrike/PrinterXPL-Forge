<div align="center">

# PrinterXPL-Forge (pt-BR)

*Kit avançado de testes de penetração em impressoras de rede*

**Descubra · Identifique · Explore · Pivote · Reporte**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://python.org)
[![Licença](https://img.shields.io/badge/Licença-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/badge/GitHub-mrhenrike-black?logo=github)](https://github.com/mrhenrike/PrinterXPL-Forge)
[![Wiki](https://img.shields.io/badge/Wiki-English-orange)](https://github.com/mrhenrike/PrinterXPL-Forge/wiki)
[![Wiki PT-BR](https://img.shields.io/badge/Wiki-Portugu%C3%AAs-green)](https://github.com/mrhenrike/PrinterXPL-Forge/wiki/Home-pt-BR)
[![Versão](https://img.shields.io/badge/vers%C3%A3o-3.14.0-red)](https://github.com/mrhenrike/PrinterXPL-Forge/releases)

> **"Sua impressora está segura? Descubra antes que outra pessoa o faça."**

**[English (en-US)](README.md)** · **[Wiki (en-us)](https://github.com/mrhenrike/PrinterXPL-Forge/wiki)** · **[Wiki (pt-br)](https://github.com/mrhenrike/PrinterXPL-Forge/wiki/Home-pt-BR)** · **[Issues](https://github.com/mrhenrike/PrinterXPL-Forge/issues)** · **[Releases](https://github.com/mrhenrike/PrinterXPL-Forge/releases)** · **[CONTRIBUTING](CONTRIBUTING.md)** · **[CODE_OF_CONDUCT](CODE_OF_CONDUCT.md)**

</div>

---

## O que é

PrinterXPL-Forge é um framework modular completo para **avaliação de segurança** de impressoras em rede. Cobre todas as principais linguagens de impressora (PJL, PostScript, PCL, ESC/P), todos os protocolos comuns (RAW, IPP, LPD, SMB, HTTP, SNMP, FTP, Telnet), 93 módulos de exploit, motor de credenciais via **wordlists externas** (zero senhas hardcoded), fingerprinting com ML, integração **NVD/CVE**, movimento lateral automatizado, análise de firmware e payloads de Cross-Site Printing.

---

## Arquitetura — Superfície de Ataque

![Superfície de Ataque em Impressoras](img/printer_architecture.png)

---

## Fluxo Operacional

![Fluxo Operacional do PrinterXPL-Forge](img/PrinterXPL-Forge_workflow.png)

> Arquivos de fluxo editáveis em [draw.io](https://app.diagrams.net): `diagrams/PrinterXPL-Forge_workflow.drawio` · `diagrams/credential_flow.drawio` · `diagrams/attack_matrix.drawio`

---

## Matriz de Cobertura de Ataques

![Matriz de Cobertura de Ataques](img/attack_coverage_matrix.png)

---

## Arquitetura de Credenciais — Zero Senhas Hardcoded

![Fluxo de Wordlist de Credenciais](img/credential_wordlist_flow.png)

---

## Início rápido

```bash
git clone https://github.com/mrhenrike/PrinterXPL-Forge.git
cd PrinterXPL-Forge
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python printerxpl-forge.py --version
python printerxpl-forge.py 192.168.1.100 --scan
```

---

## Módulos de Exploit (93 total)

| Origem | Qtd | Descrição |
|--------|-----|-----------|
| **ExploitDB** | 23 | Exploits do ExploitDB adaptados para Python 3 |
| **Metasploit** | 19 | Módulos Metasploit portados como wrappers Python |
| **Research** | 51 | Módulos originais baseados em pesquisa de segurança |

### Tipos de Ataque Cobertos

- **RCE** — PrintNightmare (CVE-2021-1675/34527), CUPS/IPP (CVE-2024-47176), Lexmark SSRF
- **Coleta de Credenciais** — LDAP pass-back, SMTP pass-back, NTLM coercion via MS-RPRN
- **Firmware** — Injeção DLM Xerox, rootkit em firmware, downgrade
- **Enumeração** — PJL INFO, SNMP dump, livro de endereços, logs de trabalhos salvos
- **DoS** — Loop infinito PostScript, exaustão NVRAM Brother
- **Cross-Site Printing** — 5 tipos de payload XSP + spoofing CORS

---

## Fornecedores Suportados

| Fornecedor | Módulos | Vulnerabilidades Notáveis |
|-----------|---------|--------------------------|
| HP | 14 | CVE-2021-39237, CVE-2025-26506, JetDirect SNMP |
| Xerox | 12 | CVE-2024-6333, DLM injection, firmware root |
| Brother | 9 | CVE-2024-51977/51978, NVRAM, default pass derivation |
| Ricoh | 8 | CVE-2019-19363, LDAP pass-back, SOAP |
| Konica | 7 | CVE-2022-1026, SOAP credential dump, bizhub |
| Canon | 6 | CVE-2025-14232, LDIF extraction, PostScript |
| Sharp | 5 | CVE-2022-45796, SMTP/LDAP pass-back |
| Kyocera | 4 | Brute-force, PJL enum, SNMP |
| Lexmark | 5 | CVE-2023-23560, CVE-2023-26067 |
| Outros | 23 | Epson, OKI, Samsung, Dell, Toshiba, generics |

---

## Descoberta Online — Motores de Busca

```bash
# Shodan
python printerxpl-forge.py --shodan --dork "HP LaserJet" --city "São Paulo"

# Censys
python printerxpl-forge.py --censys --dork "Ricoh Aficio" --country "BR"

# FOFA
python printerxpl-forge.py --fofa --dork "Brother MFC" --country "BR"
```

---

## Catálogo de CVEs

50 CVEs documentados cobrindo:
- Print Spooler (PrintNightmare, SpoolFool, PrintDemon)
- CUPS/IPP RCE chain (2024)
- HP, Xerox, Brother, Ricoh, Konica, Canon, Sharp, Lexmark, Kyocera
- FAXPLOIT (HP Officejet)
- PaperCut NG/MF

---

## Documentação completa

A documentação detalhada (comandos, matriz de ataque, descoberta online, brute-force, módulos individuais, etc.) está no **[README em inglês](README.md)** e na **[wiki bilíngue](https://github.com/mrhenrike/PrinterXPL-Forge/wiki)**.

---

## Aviso legal

Este framework é destinado **exclusivamente** para uso em sistemas próprios ou com **autorização explícita por escrito** do proprietário. Uso não autorizado é ilegal. MIT — ver `LICENSE`.

---

<div align="center">

**Autor:** André Henrique ([@mrhenrike](https://github.com/mrhenrike)) | [União Geek](https://github.com/Uniao-Geek)

</div>
