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

PrinterXPL-Forge é um framework modular completo para **avaliação de segurança** de impressoras em rede. Cobre todas as principais linguagens de impressora (PJL, PostScript, PCL, ESC/P), todos os protocolos comuns (RAW, IPP, LPD, SMB, HTTP, SNMP, FTP, Telnet), 126 módulos de exploit, motor de credenciais via **wordlists externas** (zero senhas hardcoded), fingerprinting com ML, integração **NVD/CVE**, movimento lateral automatizado, análise de firmware e payloads de Cross-Site Printing.

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

## Ataques Destrutivos / Irreversíveis

> **AVISO — SOMENTE PARA USO EM LABORATÓRIO AUTORIZADO.**  
> Os ataques abaixo causam **danos físicos permanentes e irreversíveis** ao hardware. São implementados exclusivamente para pesquisa de segurança e pentest autorizado. O operador assume plena responsabilidade legal e de segurança física.

O PrinterXPL-Forge inclui um modo **Auditoria de Ataques Destrutivos** que varre qualquer alvo em busca de todos os vetores de ataque irreversíveis conhecidos:

```bash
# Somente avaliação (dry-run — SEGURO, nenhum payload enviado)
python src/main.py 192.168.1.100 --destructive-audit

# Execução live — envia payloads destrutivos (SOMENTE LAB AUTORIZADO)
python src/main.py 192.168.1.100 --destructive-audit --no-dry

# Módulos específicos
python src/main.py 192.168.1.100 --destructive-audit \
  --destructive-modules research-fuser-thermal-attack,research-brother-nvram

# Menu interativo: escolha a opção [D] DESTRUCTIVE AUDIT
python src/main.py
```

### Módulos de Destruição Física Implementados

| Módulo | Ataque | Classe de Dano | Fabricantes |
|--------|--------|---------------|-------------|
| `research-fuser-thermal-attack` | PJL SET FUSETEMP / PS setpagedevice /FuserTemperature → runaway térmico | **FÍSICO — Risco de incêndio** | HP, Kyocera, Ricoh, Xerox |
| `research-motor-jam-attack` | HP PML DMCMD motor commands / duplex-stress → travamento de engrenagens | **FÍSICO — Mecânico** | HP, Ricoh, Generic |
| `research-laser-scanner-attack` | PS setscreen 9999 lpi + páginas 100% preto → queima de diodo/tambor | **FÍSICO — Óptico** | HP, Xerox, Ricoh, Canon |
| `research-pjl-nvram-damage` | PJL DEFAULT COPIES loop → esgotamento de ciclos de escrita NVRAM | **Brick NVRAM** | HP, Brother, Konica, Lexmark |
| `research-brother-nvram` | PJL COLLATE ON/OFF × 200.000 iterações → burnout permanente do chip | **Brick NVRAM** | Brother |
| `research-snmp-factory-reset` | SNMP prtGeneralReset OID = 6 (sem autenticação) → restauração de fábrica | **Wipe de Config** | Multi-vendor |
| `research-xerox-pjl-dlm` | @PJL DLM START → ativação do firmware download manager | **Brick Firmware** | Xerox |
| `edb-45273` (CVE-2017-2741) | PJL FSDOWNLOAD para /etc/profile.d/ + restart SNMP → root persistente | **Root Firmware** | HP PageWide/OfficeJet |

### Detalhes dos Danos Físicos

**Ataque de Runaway Térmico do Fusor** — O fusor opera em 170–210°C. Comandos PJL como `@PJL SET FUSETEMP=270` ou PostScript `<< /FuserTemperature 270 >> setpagedevice` empurram a temperatura além da tolerância do material do rolo. Acima de 270°C, a manga PTFE do fusor derrete; acima de 285°C, resíduos de papel dentro do fusor podem se incendiar.

**Motor Jamming** — A interface PML DMCMD da HP (manual de serviço) permite ativação direta de motores. Enviar comandos simultâneos para motores mecanicamente exclusivos (alimentação principal + captação + saída) sem papel causa travamento de engrenagens, destruindo o trem de acionamento plástico.

**Ataque ao Scanner a Laser** — PostScript `setscreen` com frequência 9999 lpi força o diodo laser a disparar em 100% de ciclo de trabalho continuamente. Isso acelera a degradação do diodo, superaquece o rolamento do motor do espelho polígono e abla o revestimento do tambor fotossensível — danificando permanentemente a qualidade de impressão ou tornando o LSU inoperante.

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

## Módulos de Exploit (136 total)

| Origem | Qtd | Descrição |
|--------|-----|-----------|
| **ExploitDB** | 23 | Exploits do ExploitDB adaptados para Python 3 |
| **Metasploit** | 19 | Módulos Metasploit portados como wrappers Python |
| **Research** | 58 | Módulos originais baseados em pesquisa de segurança |
| **Core/Generic** | 26 | Módulos de protocolo genérico (PJL, IPP, SNMP, PS, PCL) |

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
| HP | 16 | CVE-2025-26506, CVE-2023-6018, CVE-2017-2741, Faxploit, FutureSmart |
| Xerox | 13 | CVE-2024-6333, CVE-2021-27508, DLM injection, firmware root |
| Brother | 10 | CVE-2024-51977/51978, NVRAM, serial password derivation |
| Ricoh | 10 | CVE-2024-34161, CVE-2021-33945, CVE-2022-29943, LDAP pass-back |
| Konica | 8 | CVE-2022-1026, FIRMWARE-KONICA-001, SOAP credential dump |
| Canon | 8 | CVE-2022-24673, CVE-2025-14235, EDB-49140, PostScript |
| Microsoft | 12 | PrintNightmare, GooseEgg, PrintDemon family (CVE-2021-1675+) |
| Lexmark | 7 | CVE-2023-23560, CVE-2023-50739, CVE-2023-50733, CVE-2023-26067 |
| Linux/CUPS | 6 | CVE-2024-47176 chain, CVE-2026-34980/34990 |
| Sharp | 5 | CVE-2022-45796, SMTP/LDAP pass-back |
| Kyocera | 4 | CVE-2022-1026, brute-force, PJL enum |
| Toshiba | 3 | CVE-2024-21911, TopAccess auth bypass |
| Outros | 14 | Epson, OKI, Samsung, Dell, generics (PJL/IPP/SNMP) |

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

80 CVEs documentados cobrindo:
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


