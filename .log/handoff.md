# PrinterReaper — Handoff

---

## README + Diagramas SVG originais

**Data:** 2026-03-25
**Status:** COMPLETO — README reescrito para v3.7.0; 4 diagramas SVG originais criados e publicados no GitHub

### Diagramas criados (originais, não copiados das slides)

| Arquivo | Conteúdo |
|---------|----------|
| `img/printer_architecture.svg` | Superfície de ataque de uma impressora: canais de protocolo (RAW/IPP/LPD/SMB/HTTP/SNMP/FTP/Telnet), interpretadores internos (PJL/PS/PCL/ESC-P/EWS), categorias de impacto (DoS/ProtBypass/JobManip/InfoDisc/Lateral/CredAttack) |
| `img/printerreaper_workflow.svg` | Fluxo operacional em 6 fases: Discover → Fingerprint → Assess → Exploit → Pivot → Report, com flags CLI e output esperado por fase |
| `img/attack_coverage_matrix.svg` | Matriz de cobertura baseada em Müller et al. BlackHat 2017 + CVEs 2024-2025; eixos: categoria de ataque vs protocolo; indicadores: suportado/parcial/N/A; lista dos 20+ vendors testados |
| `img/credential_wordlist_flow.svg` | Arquitetura da nova engine de credenciais (v3.7.0): fluxo das 4 wordlists → wordlist_loader.py → token expansion → 4 protocolos de BF (HTTP/SNMP/FTP/Telnet) |

### README reescrito — seções principais
- Versão bumped para 3.7.0 no header
- Diagrama de arquitetura com explicação de superfície de ataque
- Tabela de workflow por fase com flags CLI
- Tabela de cobertura BlackHat 2017 (25 linhas de ataques documentados)
- Seção dedicada à arquitetura de wordlist (formato, tokens, flags)
- Exploit library: estrutura xpl/, check/run API
- Tabela de vendors suportados (14 linhas com default creds e exploits conhecidos)
- Version history completo v2.5.x → v3.7.0
- Legal disclaimer

### Commits publicados no GitHub
- `c3466d3` — docs: rewrite README v3.7.0 + 4 original SVG diagrams
- Push: `608740e..c3466d3 master → master`

---


---

## v3.7.0 — Wordlist-driven credentials (sem hardcode) + lab execution

**Data:** 2026-03-25
**Status:** COMPLETO — Credenciais movidas para wordlists externas; sem hardcode no Python; lab executado

### O que foi alterado

**Arquitetura de credenciais completamente refatorada:**
- Removido `_DB` (dict gigante hardcoded) de `default_creds.py`
- `default_creds.py` agora contém apenas: `Cred` dataclass, tokens (`__SERIAL__`, `__MAC6__`, `__MAC12__`), `_ALIASES`
- Criado `src/utils/wordlist_loader.py` — módulo dedicado ao carregamento de wordlists
- `login_bruteforce.py` usa `wordlist_loader` como fonte primária (não hardcode)
- `--bf-wordlist` agora **substitui** a wordlist padrão (antes fazia merge)
- `--bf-cred` ainda funciona como entradas adicionais de maior prioridade

**Novo módulo: `wordlist_loader.py`**
- `load_wordlist(path)` — carrega todos os pares user:pass de um arquivo
- `load_for_vendor(vendor, wordlist_path)` — filtra por seção vendor + appenda generic
- `load_snmp_communities(path)` — lê `snmp_communities.txt`
- `load_ftp_creds(path)` — lê `ftp_creds.txt`
- `wordlist_stats(path)` — retorna stats por seção
- `get_default_wordlist_path()` — localiza `wordlists/printer_default_creds.txt`
- Suporte a tokens `__SERIAL__`, `__MAC6__`, `__MAC12__` no próprio arquivo de wordlist

**Formato de wordlist com seções de vendor:**
```
# ── HP (Hewlett-Packard) ─────────────────────────────────────────────────────
admin:
Admin:Admin
jetdirect:
# ── Epson ─────────────────────────────────────────────────────────────────────
admin:epson
```

**Tokens reais no wordlist:**
- Adicionadas entradas reais (não comentadas) no `printer_default_creds.txt`:
  `admin:__SERIAL__`, `:__SERIAL__`, `ADMIN:__SERIAL__`, `administrator:__SERIAL__`
  `admin:__MAC6__`, `admin:__MAC12__`, `:__MAC6__`

**main.py — bruteforce:**
- Exibe path da wordlist sendo usada
- Exibe total de entradas e stats
- Remove código antigo de "merge" da wordlist (que carregava as linhas como `extra_creds`)
- Passa `wordlist_path` para `bf_run()`

### Arquivos modificados
- `src/utils/default_creds.py` — removido `_DB`; mantido apenas tipos e aliases
- `src/utils/wordlist_loader.py` — **NOVO** — carregador de wordlists
- `src/modules/login_bruteforce.py` — usa wordlist_loader; `wordlist_path` em todos os métodos
- `src/main.py` — bruteforce block refatorado; exibe path e stats da wordlist
- `src/version.py` — bump 3.6.2 → 3.7.0
- `wordlists/printer_default_creds.txt` — tokens reais adicionados

### Execução no lab

**Epson L3250 real (192.168.0.152):**
- Bruteforce: `admin` / `epson` — encontrado via HTTP Basic Auth
- URL de login detectada: `/PRESENTATION/HTML/TOP/PRTINFO.HTML`
- Wordlist usada: `wordlists/printer_default_creds.txt` (195 entradas)

**Lab emulado (127.0.0.1) — 7 impressoras:**
- HP LaserJet Pro M404n (9080): 48 creds testadas — HTTP simulador sem auth validation
- Epson L3250 (9081): 43 creds testadas
- Ricoh MP C3003 (9082): 49 creds testadas
- Xerox WorkCentre 7855 (9083): 58 creds testadas
- Kyocera ECOSYS P3055dn (9084): 55 creds testadas
- Brother MFC-J5945DW (9085): 46 creds testadas
- Lexmark CS720de (9086): 43 creds testadas

> Simuladores do lab respondem HTTP 200 independente de auth (comportamento esperado dos stubs).
> O teste validou que a wordlist foi corretamente carregada, filtrada por vendor e aplicada a cada alvo.

### Comandos executados
```
python main.py 192.168.0.152 --bruteforce --bf-vendor epson --bf-serial XAABT77481 --bf-no-variations
# → [+] FOUND: HTTP → 'admin' / 'epson'

python lab_manager.py --start all   # lab emulado
python -c "from utils.wordlist_loader import wordlist_stats; ..."  # validação
```

---
 v3.6.2
**Data:** 2026-03-25  
**Versão:** 3.6.2  
**Status:** COMPLETO — Arsenal expandido com pesquisa Tungsten/Printix, bizuns.com, Canon docs, Spiceworks; novos módulos LDAP hash capture + CVE-2024-51978

---

## Sessão v3.6.2 — Credenciais default expandidas + 2 novos módulos

### Objetivo
Estudar e integrar as informações dos links fornecidos (Tungsten Automation/Printix docs, bizuns.com, ij.manual.canon, Spiceworks community, 0xabdi.medium.com) para enriquecer credenciais default e o arsenal de exploits.

### Novas descobertas incorporadas

**Tungsten Automation / Printix partner docs:**
- Fujifilm Business Innovation: `x-admin / 11111` (novo — era apenas `admin/1111`)
- Ricoh SOP Gen 2: Remote Installation Password default = `ricoh`
- Canon Printix Go: `admin / Printix` (para integração Printix)
- Kyocera: alias `blank/admin00` confirmado

**ij.manual.canon:**
- Canon E460/E480/iB4000/MB2000/MB5000/MG2900 etc: username = `ADMIN` (maiúsculo!), password = `canon`
- Todos os outros modelos Canon: senha default = número de série do produto

**Spiceworks community:**
- Ricoh backdoor não-documentado: `supervisor` com senha em branco — permite resetar senha admin
- Brother label sticker: senha impressa na etiqueta (last 6 MAC)

**bizuns.com (default passwords list):**
- Xerox DocuCentre 425: `admin / 22222`
- Xerox Multi-Function: `admin / 2222`
- Xerox 240a: `admin / x-admin` + `11111 / x-admin`
- Ricoh DSc338/NRG: blank user + `password`
- Axis Print Server: `root / pass` (universal — todos os Axis)
- IBM Infoprint 6700: `root / (blank)`
- Minolta QMS Magicolor 3100: `operator / (blank)`, `admin / (blank)`
- Kyocera EcoLink: `n/a / PASSWORD`

**CVE-2024-51978 (Spiceworks related topics):**
- Brother printers exposing WBM admin password via SNMP OID em cleartext

**0xabdi.medium.com (LDAP/AD hash capture):**
- Ataque completo: default creds → EWS → redirect LDAP server → captura NTLM hash → Pass-The-Hash / Domain Admin

### Arquivos modificados

**`src/utils/default_creds.py`:**
- Fujifilm: adicionado `x-admin/11111` como entrada principal
- Ricoh: adicionado `ricoh` como senha, `guest/guest` para FTP (EDB-51755), `sysadmin/password` explícito, `:password` (NRG/DSc338)
- Canon: corrigido username para `ADMIN` (maiúsculo) para modelos com senha `canon`; adicionado `Printix` como senha
- Xerox: adicionado `22222`, `2222`, `x-admin` (admin), `11111/x-admin`
- Novos vendors: `zebra`, `axis`, `dell`, `minolta`, `ibm`, `develop`/`ineo`
- _ALIASES expandido com: `fujifilm business innovation`, `brother industries`, `zebra technologies`, `nrg`, `nashuatec`, `lanier`, `savin`, `gestetner`, `infotec`, `qms`, `docucentre`, `apeosport`

**`wordlists/printer_default_creds.txt`:**
- Canon: adicionado `ADMIN:canon`, `ADMIN:` (blank), `admin:Printix`
- Ricoh: adicionado `sysadmin:password`, `:password` (blank user), `guest:guest`
- Xerox: adicionado `admin:22222`, `admin:2222`, `11111:x-admin`, `admin:x-admin`
- Fujifilm: nova seção com `x-admin:11111`, `11111:x-admin`, `admin:1111`
- Axis Print Server: nova seção com `root:pass`
- IBM Infoprint: nova seção com `root:` e `USERID:PASSW0RD`
- Minolta QMS: nova seção com `operator:`, `:0`
- Kyocera: nova seção com `:PASSWORD`, `:3500`, `:2800`, `:4000`, `:2500`

### Novos módulos de exploit

**`xpl/research/research-ldap-hash-capture/`:**
- Ataque: Printer LDAP/AD Integration — NTLM Hash Capture via Rogue Server
- Detecta vendor, localiza página de config LDAP, extrai configuração
- Com `rogue_ip` + `dry_run=False`: redireciona LDAP server e força hash transmission
- Tags: `lateral-movement`, `domain-escalation`, `ntlm`, `ldap`, `hash-capture`
- Referência: 0xabdi.medium.com, Metasploit `auxiliary/server/capture/smb`

**`xpl/edb-cve-2024-51978/`:**
- CVE-2024-51978 (CVSS 7.5): Brother printers expõem senha WBM admin via SNMP OID
- OID: `1.3.6.1.4.1.2435.2.3.9.4.2.1.5.5.2.0` — lê senha em cleartext
- Testa credenciais default (initpass, access) via HTTP
- Modelos afetados: MFC-L8900CDW, MFC-L5700DN, DCP-L3550CDW, HL-L8360CDW e centenas de outros

### Status final
- Total de módulos: **39** (eram 37)
- Novas credenciais: **15+ entradas** em `default_creds.py` e `printer_default_creds.txt`
- Novos vendors suportados: Zebra, Axis, IBM, Minolta QMS, Dell, Develop/Ineo
- Aliases novos: 14 aliases de marca OEM adicionados

---

---

## Sessão Atual — Expansão Arsenal Exploit (xpl/)

### Objetivo
Integrar todos os módulos Metasploit e ExploitDB verificados para impressoras diretamente no PrinterReaper, evitando que o operador precise sair da ferramenta.

### Resultado
**30 exploits** carregados (era 8). Breakdow por fonte:
- `[EDB]` **14** módulos ExploitDB (6 existentes + 8 novos)
- `[MSF]` **9** módulos Metasploit portados para Python nativo
- `[RES]` **6** módulos research original (Epson + genéricos + NCC/SentinelOne)
- `[USR]` **1** template custom

### Novos arquivos criados
- `xpl/msf/msf-printer-env-vars/` — PJL NVRAM dump (MSF printer_env_vars)
- `xpl/msf/msf-printer-dir-list/` — PJL filesystem listing (MSF printer_list_dir)
- `xpl/msf/msf-printer-file-download/` — PJL FSUPLOAD download (MSF printer_download_file)
- `xpl/msf/msf-printer-file-upload/` — PJL FSDOWNLOAD upload (MSF printer_upload_file)
- `xpl/msf/msf-printer-info/` — PJL INFO query (MSF printer_info)
- `xpl/msf/msf-ricoh-loginout-dos/` — Ricoh SNMP DoS (MSF ricoh_loginout)
- `xpl/msf/msf-hp-web-jetadmin-rce/` — HP WebJetAdmin RCE CVE-2011-4065
- `xpl/msf/msf-snmp-printer-enum/` — SNMP MIB dump printer-específico
- `xpl/msf/msf-ipp-printer-check/` — IPP AirPrint anon enumeration
- `xpl/edb-36608/` — Ricoh MP auth bypass (CVE-2014-9321)
- `xpl/edb-40909/` — Samsung SCX command injection (CVE-2016-6556)
- `xpl/edb-36913/` — Lexmark arbitrary file read (CVE-2014-8738)
- `xpl/edb-41920/` — HP LaserJet hardcoded credentials (CVE-2017-2740)
- `xpl/edb-43178/` — Konica Minolta session fixation (CVE-2017-6321)
- `xpl/edb-45205/` — HP PageWide SSRF (CVE-2017-2750)
- `xpl/edb-23147/` — Kyocera ECOSYS info disclosure
- `xpl/edb-37956/` — Brother HL/MFC default credentials
- `xpl/research/research-epson-noauth-disclosure/` — CVE-2022-3426 + CWE-603
- `xpl/research/research-epson-lpd-unauth/` — CVE-2023-27516
- `xpl/research/research-epson-connect-cloud/` — Cloud email SNMP exposure
- `xpl/research/research-generic-pjl-nvram/` — PJL NVRAM read/write

### Mudanças no engine
- `src/utils/exploit_manager.py`: suporte a subpastas `msf/` e `research/`
- `src/utils/exploit_manager.py`: `--xpl-source` filter (metasploit|exploit-db|research|custom)
- `src/utils/exploit_manager.py`: badge `[MSF]`, `[EDB]`, `[RES]`, `[USR]` na listagem
- `src/utils/exploit_manager.py`: `index.json` v2.0 com campos source, protocol, cvss, url
- `src/main.py`: argumento `--xpl-source SOURCE` adicionado

### Comandos disponíveis
```
python src/main.py --xpl-list                        # todos os 30 exploits
python src/main.py --xpl-list --xpl-source metasploit
python src/main.py --xpl-list --xpl-source exploit-db
python src/main.py --xpl-list --xpl-source research
python src/main.py 192.168.0.152 --xpl-check MSF-PRINTER-ENV-VARS
python src/main.py 192.168.0.152 --xpl-run MSF-PRINTER-ENV-VARS
python src/main.py 192.168.0.152 --xpl-run RESEARCH-EPSON-NOAUTH-DISCLOSURE
```

---

---

## Sessão Atual — Assessment Completo Epson L3250

### Objetivo
Assessment de segurança completo na impressora de laboratório Epson EcoTank L3250 (192.168.0.152) com credenciais default (admin / XAABT77481 = serial number).

### Resultados Gerais
- **Autenticado** com sucesso via serial number na 1ª tentativa
- **21 endpoints web** acessíveis SEM autenticação (incluindo ADMIN, FWUPDATE, RESTORE)
- **4 portas abertas**: TCP/80, TCP/443, TCP/515 (LPD), TCP/631 (IPP)
- **SNMP dump**: 2000 OIDs coletados sem auth (community `public`)
- **Firmware**: `05.22.XF26P8` — sem CVEs publicados para esta versão exata
- **Attack matrix**: 15 testes, 2 vulneráveis, 1 explorado

---

## Device Profile (Coletado no Assessment)

| Campo | Valor |
|-------|-------|
| Modelo | Epson EcoTank L3250 Series |
| Firmware | **05.22.XF26P8** |
| Hardware | EEPS2 Hard Ver.1.00 Firm Ver.0.22 |
| Serial / Senha Admin | **XAABT77481** |
| MAC | 58:05:D9:3F:9F:9C |
| IP | 192.168.0.152 (DHCP) |
| Gateway | 192.168.0.1 |
| WiFi SSID | **Cyberpass** (WPA2-PSK/AES) |
| Wi-Fi Direct SSID | **DIRECT-D9-EPSON-3F9F9C** |
| Epson Connect Email | **vst2954d586u65@print.epsonconnect.com** |
| Epson Connect | Registered / Connected |
| Root Cert | v02.01 |
| Idiomas de impressão | ESCPL2, BDC, D4, D4PX, ESCPR1, END4, GENEP, PWGRaster |

---

## Vulnerabilidades Identificadas

### Críticas
| ID | Descrição | Prova |
|----|-----------|-------|
| CRIT-1 | PRTINFO.HTML expõe SSID "Cyberpass" sem auth | GET retorna 200 com dados |
| CRIT-2 | CWE-603: Autenticação apenas no lado JS | Todos os 21 endpoints retornam 200 sem cookie |
| CRIT-3 | LPD TCP/515 aceita comandos sem autenticação | ACK=0x00, "no entries" retornado |
| CRIT-4 | Senha default = número de série (documentado pelo fabricante) | Login na 1ª tentativa |

### Altas
| ID | Descrição |
|----|-----------|
| HIGH-1 | Email Epson Connect `vst2954d586u65@print.epsonconnect.com` exposto via SNMP → permite envio de jobs da internet |
| HIGH-2 | SSID Wi-Fi Direct `DIRECT-D9-EPSON-3F9F9C` exposto via SNMP |
| HIGH-3 | SNMP dump completo: 2000 OIDs sem autenticação |
| HIGH-4 | IPP: 30+ atributos expostos sem auth, AirPrint ativo |
| HIGH-5 | Certificado TLS self-signed → MITM possível |

### Médias
- Sem rate limiting no login
- SSID "Cyberpass" exposto → alvo para WPA2 handshake
- Headers de segurança HTTP ausentes (CSP, HSTS, X-Frame-Options)
- eSCL scanner acessível (TCP/631, retorna 500 — endpoint existe)
- WSD SSRF capaz (confirmado no attack matrix)

---

## CVEs Aplicáveis

| CVE | CVSS | Status |
|-----|------|--------|
| CVE-2022-3426 | 5.4 | **CONFIRMADO** — info disclosure sem auth |
| CVE-2023-27516 | 7.5 | **CONFIRMADO** — LPD sem autenticação |
| CVE-2021-26598 | 6.1 | Provável — CSRF (sem token CSRF encontrado) |
| CVE-2019-3949 | 7.5 | Possível — XSS no nome/location |
| CWE-603 | N/A | **CONFIRMADO** — autenticação client-side only |

**Firmware 05.22.XF26P8**: Nenhum CVE publicado no NVD para esta versão específica.

---

## Arquivos Gerados Nesta Sessão

| Arquivo | Descrição |
|---------|-----------|
| `.log/epson_l3250_assessment_report.md` | Relatório completo de assessment |
| `.log/snmp_dump_192_168_0_152.txt` | Dump SNMP (2000 OIDs) |
| `.log/_enum_endpoints.py` | Script de enumeração de endpoints HTTP/HTTPS |
| `.log/_deep_probe.py` | Probe profunda de endpoints críticos |
| `.log/_pswd_analysis.py` | Análise da página de auth e BOIP API |
| `.log/_auth_and_extract.py` | Extração autenticada via session cookie |
| `.log/_final_analysis.py` | Análise final + report consolidado |

---

## Comandos Executados

```bash
# Scan completo
python src/main.py 192.168.0.152 --scan

# Attack matrix (dry-run)
python src/main.py 192.168.0.152 --attack-matrix

# IPP audit
python src/main.py 192.168.0.152 --ipp

# Firmware audit
python src/main.py 192.168.0.152 --firmware

# Storage + SNMP dump
python src/main.py 192.168.0.152 --storage

# Network map
python src/main.py 192.168.0.152 --network-map

# Brute-force com serial
python src/main.py 192.168.0.152 --bruteforce --bf-vendor epson --bf-serial XAABT77481

# Enumerate 40+ endpoints HTTP/HTTPS
python .log/_enum_endpoints.py

# Deep probe crítico (EEPROM, ADMIN, FWUPDATE, RESTORE...)
python .log/_deep_probe.py

# Auth completa + extração de dados
python .log/_auth_and_extract.py
```

---

## Observações Técnicas

### Mecanismo de Auth do EWS Epson L3250
- A impressora usa autenticação **baseada em cookie de sessão**
- Login via POST para `/PRESENTATION/PSWD` com `session=<SERIAL>`
- Retorna cookie: `EPSON_COOKIE_SESSION=session&<UUID>`
- **Falha crítica**: a verificação é feita **apenas no JavaScript** do lado do cliente
- O servidor retorna HTTP 200 para TODOS os endpoints sem verificar cookie de sessão

### Endpoints com Conteúdo Real (não-JS)
- `/PRESENTATION/HTML/TOP/PRTINFO.HTML` (6540b) — dados sem auth
- `/PRESENTATION/HTML/TOP/INDEX.html` (7459b) — menu principal (requer sessão válida)
- `/PRESENTATION/PSWD` (3488b) — formulário de login

### Network Map (Bug Corrigido — Pendente)
- `--network-map` retorna gateway com encoding quebrado (bytes não-ASCII)
- Bug na leitura de OID SNMP para netmask/gateway — tratar como issue pendente

---

## Status Anterior (v3.4.1 → v3.5.0)

Ver handoff anterior para histórico das versões 3.0.0–3.4.1.

### Principais features v3.5.0
- `send-job`: envio de impressão (RAW/IPP/LPD) para qualquer alvo
- Remoção de emojis da UI/CLI
- Wordlists expandidas em `wordlists/`
- `--bf-wordlist` para credenciais personalizadas
- Lab PrinterReaper expandido com 6 novas impressoras (BlackHat 2017)
- QEMU integration scripts para Kali VM

---

## Próximos Passos Sugeridos

1. Corrigir bug de encoding no `--network-map` (gateway/netmask SNMP)
2. Implementar extração automática de dados após autenticação web bem-sucedida
3. Implementar exploit específico para CWE-603 (auth bypass via script sem JS)
4. Testar `--send-job` contra a impressora real com um arquivo de teste
5. Verificar se firmware update está disponível para L3250 (ver https://epson.com/Support/)
6. Implementar teste de CSRF (form sem token) — `/PRESENTATION/PSWD`
7. Testar abuso do Epson Connect email para envio de job remoto
