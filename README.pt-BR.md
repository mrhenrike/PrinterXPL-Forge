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

PrinterXPL-Forge é um framework modular completo para **avaliação de segurança** de impressoras em rede. Cobre todas as principais linguagens de impressora (PJL, PostScript, PCL, ESC/P), todos os protocolos comuns (RAW, IPP, LPD, SMB, HTTP, SNMP, FTP, Telnet), **185 módulos de exploit**, motor de credenciais via **wordlists externas** (zero senhas hardcoded), fingerprinting com ML, integração **NVD/CVE**, movimento lateral automatizado, análise de firmware e payloads de Cross-Site Printing. Orquestração multi-linguagem (Python, C/C++ via WSL gcc, Ruby/Metasploit, Go, Rust) é gerenciada pelo motor `poly_runner` integrado. Catálogo NVD/CVE com 120 entradas.

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

## Módulos de Exploit (185 total)

| Origem | Qtd | Descrição |
|--------|-----|-----------|
| **ExploitDB** | 25 | Exploits do ExploitDB adaptados para Python 3 |
| **Metasploit** | 19 | Módulos Metasploit portados como wrappers Python |
| **Research** | 80 | Módulos originais baseados em pesquisa de segurança |
| **Core/Generic** | 26 | Módulos de protocolo genérico (PJL, IPP, SNMP, PS, PCL) |

### Novos Módulos HIGH/CRITICAL (v6.1.0)

| Módulo | CVE(s) | CVSS | Fabricante | Tipo |
|---|---|---|---|---|
| `research-hp-printing-shellz` | CVE-2021-39238 | 9.8 | HP | RCE wormable (FutureSmart BOF) |
| `research-hp-bof-series-2022` | CVE-2022-28721/2023-1329/2024-0794 | 9.8 | HP | Série de BOF em rede |
| `edb-cve-2021-3441` | CVE-2021-3441 | 7.4 | HP | XSS persistente via PUT sem autenticação |
| `research-ssport-lpe` | CVE-2021-3438 | 7.8 | HP/Samsung/Xerox | LPE kernel Windows (SSPORT.SYS) |
| `research-canon-xps-bof-2025b` | CVE-2025-14234/CVE-2025-14237 | 9.8 | Canon | XPS BOF (advisory CP2026-001) |
| `research-lexmark-ps-bof-50734` | CVE-2023-50734 | 9.0 | Lexmark | BOF no interpretador PostScript |
| `research-lexmark-ps-bof-50736` | CVE-2023-50736 | 9.0 | Lexmark | Corrupção de memória PS |
| `research-lexmark-fw-downgrade` | CVE-2023-50738 | 8.8 | Lexmark | Downgrade de firmware → RCE |
| `research-lexmark-heap-bof` | CVE-2024-11345 | 7.3 | Lexmark | Heap BOF via upload multipart |
| `research-lexmark-pwn2own-2026` | CVE-2025-65079/65080/65081 | 8.8 | Lexmark | Cadeia Pwn2Own 2026 |
| `research-ricoh-http-bof` | CVE-2024-47939 | 7.7 | Ricoh/Konica Minolta | Stack BOF Web Image Monitor |
| `research-xerox-ipp-bof` | CVE-2019-13165/CVE-2019-13168 | 8.1 | Xerox | BOF IPP sem autenticação |
| `research-xerox-http-bof` | CVE-2019-13169/CVE-2019-13172 | 8.1 | Xerox | BOF HTTP header/cookie |
| `edb-cve-2016-11061` | CVE-2016-11061 | 9.8 | Xerox | RCE sem autenticação (configrui.php) |
| `research-brother-wsd-ssrf` | CVE-2024-51980/CVE-2024-51981 | 7.5 | Brother | WSD TCP forçado / SSRF |
| `research-brother-wsd-dos` | CVE-2024-51983 | 7.5 | Brother | WSD DoS — queda do dispositivo |
| `research-brother-passback` | CVE-2024-51984 | 7.1 | Brother | Pass-back LDAP/SMTP |
| `edb-cve-2023-3710` | CVE-2023-3710 | 8.8 | Honeywell | Injeção de comando PM43 (EDB-51885) |
| `research-tftp-loop-dos` | CVE-2024-2169 | 7.5 | Brother/Genérico | Loop infinito TFTP — DoS |

### Motor poly_runner — Melhorias v6.1.0

- **`available_langs()`** — Retorna dicionário de compiladores/runtimes detectados no sistema
- **`run_from_dir(module_dir, ...)`** — Auto-detecta arquivos fonte (`source.c`, `exploit.rb`, `exploit.go`) e despacha para o runner correto
- **Cache de compilação** — Ignora recompilação quando o binário é mais novo que o fonte
- **Fallback WSL** — No Windows, usa automaticamente `wsl gcc` quando gcc nativo não está disponível

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
| HP | 22 | CVE-2025-26506, CVE-2021-39238, CVE-2022-28721, CVE-2023-1329, CVE-2024-0794, CVE-2021-3438, Faxploit |
| Xerox | 16 | CVE-2024-6333, CVE-2016-11061, CVE-2019-13165/13168/13169/13172, CVE-2021-27508 |
| Brother | 13 | CVE-2024-51977/51978/51980/51981/51983/51984, NVRAM, serial password derivation |
| Ricoh | 11 | CVE-2024-47939, CVE-2024-34161, CVE-2021-33945, CVE-2022-29943, LDAP pass-back |
| Lexmark | 12 | CVE-2023-50734/50736/50738, CVE-2024-11345, CVE-2025-65079, CVE-2023-23560 |
| Canon | 10 | CVE-2025-14232/14234/14235/14237, CVE-2022-24673, EDB-49140 |
| Microsoft | 12 | PrintNightmare, GooseEgg, PrintDemon family (CVE-2021-1675+) |
| Konica Minolta | 9 | CVE-2022-1026, CVE-2024-47939, FIRMWARE-KONICA-001, SOAP credential dump |
| Linux/CUPS | 6 | CVE-2024-47176 chain, CVE-2026-34980/34990 |
| Sharp | 5 | CVE-2022-45796, SMTP/LDAP pass-back |
| Kyocera | 4 | CVE-2022-1026, brute-force, PJL enum |
| Honeywell | 1 | CVE-2023-3710 (PM43 command injection) |
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

