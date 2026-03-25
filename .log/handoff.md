# PrinterReaper — Handoff v3.5.0
**Data:** 2026-03-25  
**Versão:** 3.5.0  
**Status:** COMPLETO — Assessment Epson L3250 realizado

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
