# PrinterReaper — Handoff

---

## v3.15.2 — Clear Queue + Prompt Target + Session State + Semver Fix

**Data:** 2026-03-24
**Status:** COMPLETO

### Semver corrigido
- `3.15.0` = feature release (IPP/PWG Raster/OS print fallback)
- `3.15.1` = patch (sanitização de código, UI alignment, git LF)
- `3.15.2` = patch (este — queue clearing, prompt target, session state)
- Regra: campo1=MAJOR (mudança drástica), campo2=MINOR (novas features), campo3=PATCH (bugfix/ajustes)

### Alterações

| Arquivo | O que mudou |
|---------|-------------|
| `src/version.py` | Versão `3.15.2`, date `2026-03-24` |
| `src/main.py` | `_require_target()` — nova função que solicita target ao user quando ausente, substituindo todos os `sys.exit(1)` por prompt; `_has_action` — lógica para detectar quando não há ação real e ir para menu interativo mesmo com flags sem efeito |
| `src/modules/print_job.py` | `_clear_os_print_queue()` — nova função que limpa fila de impressão via PowerShell (Windows) ou `cancel -a` (Linux/macOS) antes de enviar job via OS; `send_os_print()` com parâmetro `clear_queue=True` |
| `src/ui/interactive.py` | `_session` dict para persistência de target/vendor/serial entre ações do menu; `_target_prompt()` usa `_session['target']` como default; opção `[T]` para trocar target; exibe target ativo no rodapé do menu |

### Comportamento novo

- `python printer-reaper.py --scan` → solicita target ao user em vez de sair com erro
- `python printer-reaper.py --send-job file.pdf` → solicita target
- Menu interativo: target informado em scan fica salvo para brute-force/attack sem re-digitar
- Impressão via OS: limpa fila antes de enviar (resolve "impressora offline/fila travada")
- Fila de impressão: limpa jobs com erro/paused/stuck antes de cada `send_os_print()`

---

## v3.15.1 — Sanitização de Código + Fixes de UI + Git LF

**Data:** 2026-03-24
**Status:** COMPLETO

### Alterações

| Arquivo | O que mudou |
|---------|-------------|
| `src/main.py` | Corrigido "Version Version" no banner (linha 1641); adicionado `args.mode = args.mode or 'auto'` para resolver `KeyError: None` ao chamar com target sem mode; `--version` usa `get_version_string()` sem prefixo duplicado |
| `src/modules/pjl.py` | Removido "v2.3.1" hardcoded no `do_help()`; agora usa `from version import __version__` dinamicamente |
| `src/ui/interactive.py` | `_menu_header()` reescrito com fórmula matemática de padding (`_w - 4 - len(text)`) para garantir alinhamento perfeito do box Unicode em qualquer versão |
| `src/modules/pcl.py` | Removido "v2.4.0" do docstring |
| `src/modules/ps.py` | Removido "v2.4.0" do docstring |
| `src/payloads/__init__.py` | Removido "v2.4.0" do docstring |
| `src/protocols/__init__.py` | Removido "v2.4.0" do docstring |
| `src/utils/exploit_manager.py` | User-Agent atualizado de `PrinterReaper/3.4` para `PrinterReaper/3.15` |
| `src/utils/fuzzer.py` | Removido "v2.3.3" do comentário interno |
| `src/utils/operators.py` | Removidas referências a "v2.4.0" e blocos de comentário de versão legados |
| `.gitattributes` | Criado para forçar `eol=lf` em todos os arquivos Python/config |

### Comandos executados
```
git config core.autocrlf false
git config core.eol lf
```

### PRET — Análise de Módulos

**Repositório clonado:** `dev/IoT/pret/` (github.com/RUB-NDS/PRET)

**Módulos relevantes analisados:**
- `printer.py` — Classe base com loop cmd, conexão TCP (socket raw porta 9100)
- `capabilities.py` — Fingerprint via IPP, HTTP, HTTPS, SNMP; útil para detecção de capacidades
- `helper.py` — Classe `conn` para socket TCP; classe `output` para logging colorido
- `pjl.py` — Comandos PJL: `do_status`, `do_id`, `do_env`, `do_nvram`, `do_lock`/`do_unlock`, `put` (upload via FSDOWNLOAD)

**Conclusão:** PRET é uma ferramenta de pen-testing de impressoras, **não possui envio direto de print jobs**. O `put()` faz upload via PJL FSDOWNLOAD (filesystem da impressora), não submissão de trabalho de impressão. O PrinterReaper já supera o PRET em todas as funcionalidades relevantes, incluindo `print_job.py` com suporte a IPP/LPD/RAW/OS.

### Status final
- `KeyError: None` → **CORRIGIDO** (auto-detecta modo quando não especificado)
- `"Version Version"` → **CORRIGIDO**
- `v2.3.1` no PJL shell → **CORRIGIDO** (dinâmico via `version.py`)
- Alinhamento do box interativo → **CORRIGIDO** (fórmula matemática de padding)
- Versões antigas em módulos → **SANITIZADAS**

---

## v3.15.0 — Fix IPP Encoding + PWG Raster + OS Print Fallback

**Data:** 2026-03-25
**Status:** COMPLETO
**Commit:** `8473231`

### Bugs críticos corrigidos

| Módulo | Bug | Correção |
|---|---|---|
| `print_job.py` | Encoding IPP `struct.pack('>BHH', ...)` inseria 2 bytes extras antes do nome do atributo, corrompendo toda requisição IPP | Corrigido para `bytes([tag]) + struct.pack('>H', name_len)` per RFC 8011 §3.1.5 |
| `print_job.py` | `printer-uri` usava `ipps://` mesmo em conexões TLS — Epson exige `ipp://` no atributo mesmo sobre TLS | Corrigido: sempre `ipp://` no valor do atributo IPP |
| `print_job.py` | Atributo `printer-resolution` no Print-Job causava `0x0400 Bad Request` na Epson L3250 | Removido do bloco de atributos do job |
| `print_job.py` | Fallback LPD tentava abrir PDF com `PIL.Image.open()` causando `UnidentifiedImageError` | Condição `prefer_escp and fmt == 'image'` antes de abrir com PIL |
| `install_printer.py` | Template PowerShell usava `{host}` sem passar `host=host` no `.format()` | Corrigido o call `.format(name=..., host=host, ipp_uri=...)` |
| `install_printer.py` | `Add-PrinterPort -PortNumber 631 -SNMP:$false` inválido no Windows | Simplificado: usa port padrão 9100 + driver detectado automaticamente |

### Descobertas durante debug (Epson L3250)

| Descoberta | Detalhe |
|---|---|
| Formatos IPP aceitos | `image/pwg-raster`, `application/vnd.epson.escpr`, `application/octet-stream` |
| Sync word PWG Raster | `b"RaS\x03"` (0x52615303), NÃO `b"RaS3"` (0x52615333) |
| `document-format-supported` | Confirmado via Get-Printer-Attributes com encoding correto |
| `pwg-raster-document-type-supported` | `sgray_8`, `srgb_8` |
| Driver real instalado | `EPSON L3250 Series` via WSD (auto-discovery pelo Windows) |

### Novos recursos

| Funcionalidade | Detalhes |
|---|---|
| `_image_to_pwg_raster()` | Gera PWG Raster (`RaS\x03`, 1796-byte header correto, srgb_8/sgray_8) para IPP inkjet |
| `send_os_print()` | Imprime via spooler OS: `mspaint /pt` (imagens), `notepad /pt` (texto), `Start-Process -Verb PrintTo` (PDF/outros), `lpr` (Linux/macOS) |
| Mensagens de erro bilíngues | Erros IPP com sugestão de usar `--install-printer` e tentar pelo driver do SO |
| `_prepare_payload(prefer_pwg=True)` | Gera PWG Raster automaticamente quando protocolo é IPP para inkjets Epson |

### Testes realizados

| Teste | Resultado |
|---|---|
| `Get-Printer-Attributes` com encoding corrigido | 0x0000 — lista completa de formatos retornada |
| Print-Job via IPP (printer busy) | 0x0507 Busy — exibido aviso correto |
| PDF via OS (`EPSON L3250 Series` WSD driver) | Job na fila: "Printing, Retained" (imprimindo) |
| Imagem via OS (`mspaint /pt`) | Job na fila: "Normal" (aguardando PDF) |
| `printer-reaper.py --send-job test.pdf --send-proto auto` | IPP falha (busy) → LPD fallback OK (236KB aceito) |

### Próximos passos sugeridos

1. Testar `--send-job imagem.jpg` quando impressora estiver idle (state=3) para validar PWG Raster via IPP
2. Implementar `--os-printer` como flag CLI para usar `send_os_print()` diretamente
3. Validar se `application/vnd.epson.escpr` aceita ESCPR1 via IPP (formato do driver Linux)

---

## v3.13.0 — Fix ZoomEye/Netlas APIs + Repo Cleanup

**Data:** 2026-03-24
**Status:** COMPLETO

### Bugs corrigidos

| Engine | Problema | Correção |
|---|---|---|
| ZoomEye | 403 — `api.zoomeye.org` restrito por região; auth `JWT` inválido | Migrado para `api.zoomeye.ai`; auth header mudado para `API-KEY` |
| ZoomEye | 402 — créditos insuficientes (plano free) | Handle gracioso: aviso + skip sem crash |
| Netlas | 400 — parâmetro `indices=responses` inválido | Removido; apenas `q` e `size` usados |
| Netlas | Campos errados: `geo.country_code`, `geo.city.name`, `data.response` | Corrigidos para `geo.country`, `geo.city` (confirmados via API real) |
| Netlas | `data.response` não existe para raw TCP | Queries refeitas: usa `http.title` para web + `port:9100` para raw TCP |
| Netlas | Timeout 20s insuficiente para queries com filtro de país | Aumentado para 60s |

### Testes realizados (validados)

| Teste | Resultado |
|---|---|
| `--discover-local` | OK — Epson L3250 (192.168.0.152) detectada localmente |
| `--scan 192.168.0.152 --no-nvd` | OK — 3 CVEs Epson, 3 vendor, 3 genéricos; 10 exploits mapeados |
| `--discover-online --shodan --dork-vendor epson --dork-country BR --dork-limit 2` | OK — 2 impressoras Epson no BR |
| `--discover-online --netlas --dork-country BR --dork-port 9100 --dork-limit 2` | OK — 2 impressoras RAW no BR |
| `--discover-online --dork-engine shodan,netlas --dork-vendor hp --dork-country BR --dork-limit 2` | OK — 6 impressoras HP no BR via 2 engines |
| ZoomEye (créditos insuficientes) | Skip gracioso com aviso |
| Censys (sem key configurada) | Skip gracioso com aviso |

### Limpeza do repositório

| Item removido | Motivo |
|---|---|
| `tests/` | Arquivos de teste auto-gerados, não solicitados |
| `tools/` | Scripts internos de dev (add_author, db_merge, release_notes) |
| `debian/` | Artefato de packaging não necessário |
| `packaging/` | Artefato de packaging não necessário |
| `build/` | Artefato de build |
| `src/printer_reaper.egg-info/` | Artefato de build |
| `.log/_api_probe.py` | Script de debug temporário |
| `.log/discovery_*.json` | Resultados de teste em runtime |

### .gitignore atualizado

Adicionadas entradas para: `tests/`, `tools/`, `debian/`, `packaging/`, `.log/discovery_*.json`.

### Arquivos alterados

| Arquivo | Mudança |
|---|---|
| `src/utils/discovery_online.py` | ZoomEye: URL→`api.zoomeye.ai`, header→`API-KEY`, handle 402; Netlas: remove `indices`, corrige campos geo, queries refeitas |
| `src/version.py` | 3.12.0 → 3.13.0 |
| `.gitignore` | +tests/, tools/, debian/, packaging/, .log/discovery_*.json |
| `.log/handoff.md` | Este arquivo |

---

## v3.12.0 — CSV Multi-Value Dork Filters + City/Country Guard

**Data:** 2026-03-24
**Status:** COMPLETO

### Problema resolvido
Todos os filtros de dork (`--dork-vendor`, `--dork-country`, `--dork-port`, `--dork-city`, `--dork-region`) agora aceitam:
1. **Valor único**: `--dork-country BR`
2. **CSV num único flag**: `--dork-country BR,AR,US`
3. **Flags repetidos**: `--dork-country BR --dork-country AR`
4. **Nomes compostos com aspas**: `--dork-city "São Paulo",'Rio de Janeiro'`

Regra adicional: `--dork-city` é bloqueado quando 0 ou 2+ países são especificados.

### Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/main.py` | +`_expand_csv()` e `_expand_csv_int()` helpers; +imports `csv`, `io`; todos os args de dork agora `action="append"` + processados com expand; `DiscoveryParams` recebe `cities` (list) em vez de `city` (str); validação city/country guard antes de construir params |
| `src/utils/discovery_online.py` | `DiscoveryParams.city` → `cities: List[str]`; todos os `_*_city_part()` atualizados para OR-join múltiplas cidades com sintaxe nativa de cada engine; adicionados `_fofa_city_part()`, `_zoomeye_city_part()`, `_netlas_city_part()`; `_geo_label()` e `describe()` atualizados |
| `src/version.py` | 3.11.0 → 3.12.0 |
| `.log/handoff.md` | Este arquivo |

### Exemplos válidos

```bash
# Um vendor, um país
python printer-reaper.py --discover-online --dork-vendor hp --dork-country BR

# Múltiplos vendors e países via CSV
python printer-reaper.py --discover-online --dork-vendor hp,canon,epson --dork-country BR,AR,US

# Múltiplos flags repetidos
python printer-reaper.py --discover-online \
  --dork-vendor hp --dork-vendor canon \
  --dork-country BR --dork-country AR \
  --dork-port 9100 --dork-port 631 \
  --dork-engine shodan,zoomeye

# Cidades (single country obrigatório)
python printer-reaper.py --discover-online \
  --dork-country BR \
  --dork-city "São Paulo",Belém,"Rio de Janeiro"
```

### Erros gerados automaticamente

```
# 0 países com --dork-city → ERRO
--dork-city 'Sao Paulo'  (sem --dork-country)
→ "--dork-city requires exactly one --dork-country"

# 2+ países com --dork-city → ERRO
--dork-country BR --dork-country AR --dork-city 'Sao Paulo'
→ "--dork-city cannot be used with multiple countries (BR, AR)"
```

---

## v3.11.0 — Engine Selection UX Fix, FOFA Key-Only, ZoomEye/Netlas Keys

**Data:** 2026-03-24
**Status:** COMPLETO

### Problema resolvido
Corrigiu UX de seleção de search engines no `--discover-online`:
- Flags individuais (`--shodan`, `--censys`, `--fofa`, `--zoomeye`, `--netlas`) são **mutually exclusive** — apenas uma pode ser usada por vez.
- `--dork-engine A,B,C` é o **único** mecanismo para selecionar múltiplos engines simultaneamente.
- Misturar flag individual com `--dork-engine` gera erro explicativo imediato.
- Dois ou mais flags individuais juntos geram erro com sugestão de uso do `--dork-engine`.
- Sem flag → todos os engines com chave configurada são usados.

FOFA não exige mais email desde dezembro de 2023 — campo `email` removido do JSON e da API call.

### Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/main.py` | Lógica de resolução de engines reescrita; help texts de todos os engine flags reescritos; import de `fofa_key` no lugar de `fofa_credentials`; `fofa_email` removido do construtor `OnlineDiscoveryManager` |
| `src/utils/discovery_online.py` | `FOFASearcher.__init__` aceita apenas `api_key` (email depreciado); `OnlineDiscoveryManager.__init__` assinatura e init FOFA atualizados; import `fofa_key` no lugar de `fofa_credentials` |
| `src/utils/config.py` | Nova função `fofa_key()` adicionada; `fofa_credentials()` mantida por compatibilidade com nota de depreciação |
| `config.json` | FOFA: campo `email` removido; ZoomEye key preenchida (`0F499Cf2-Db9A-60c3A-8758-2372509e30b`); Netlas key preenchida (`LHOXtnRa1ARORAVnmVFUtH6KKbo8Bzm3`) |
| `config.json.example` | FOFA: campo `email` removido do template |
| `src/version.py` | 3.10.0 → 3.11.0 |
| `.log/handoff.md` | Este arquivo |

### Comportamento de seleção de engines (novo)

```bash
# Um engine → flag individual
python printer-reaper.py --discover-online --shodan --dork-vendor hp --dork-country BR

# Múltiplos engines → --dork-engine
python printer-reaper.py --discover-online --dork-engine shodan,censys --dork-vendor epson

# Erro: mistura proibida
python printer-reaper.py --discover-online --shodan --dork-engine fofa  # ← ERRO

# Erro: dois flags individuais
python printer-reaper.py --discover-online --shodan --fofa               # ← ERRO

# Sem flag → todos os engines configurados
python printer-reaper.py --discover-online --dork-vendor hp
```

### Próximos passos
- Atualizar wiki `Online-Discovery-Dorks.md` para refletir o novo comportamento de engine selection.
- Considerar integração de resultados FOFA/ZoomEye/Netlas no relatório consolidado.

---

## v3.10.0 — Custom Port Overrides for Every Protocol

**Data:** 2026-03-25
**Status:** COMPLETO

### Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/utils/ports.py` | NOVO — `PortConfig` singleton com defaults e overrides por protocolo |
| `src/main.py` | +10 flags (`--port-raw`, `--port-ipp`, `--port-lpd`, `--port-snmp`, `--port-ftp`, `--port-http`, `--port-https`, `--port-smb`, `--port-telnet`, `--extra-ports`); `PortConfig.configure_from_args()` aplicado logo após parse; linhas com 9100 hardcoded corrigidas |
| `src/utils/banner_grabber.py` | `scan_ports()` usa `_resolved_printer_ports()` + `extra_ports`; `_grab_pjl`, `_grab_lpd`, `_grab_ipp`, `_grab_http`, `_grab_snmp` usam `PortConfig.resolve()` |
| `src/core/attack_orchestrator.py` | `run_campaign()` usa `PortConfig.resolve('raw')` e `resolve('ipp')` em lugar de 9100/631 literais |
| `src/modules/pjl.py` | DoS flood usa `PortConfig.resolve('raw')` |
| `src/modules/login_bruteforce.py` | Orquestrador `bruteforce()` usa `PortConfig` para HTTP/FTP/SNMP/Telnet ports |
| `src/protocols/firmware.py` | 4 `create_connection((host, 9100))` → `PortConfig.resolve('raw')`; `UdpTransportTarget((host, 161))` → `PortConfig.resolve('snmp')` |
| `src/protocols/network_map.py` | PJL probe e `generate_xsp_payload()` usam `PortConfig.resolve('raw')` |
| `src/protocols/storage.py` | `snmp_dump` e `snmp_write` usam `PortConfig.resolve('snmp')`; FTP functions usam `_ftp_default_port()` |
| `src/core/discovery.py` | `_snmp_get()` usa `PortConfig.resolve('snmp')` no CLI snmpget |
| `src/version.py` | 3.9.0 → 3.10.0 |
| `README.md` | Nova seção "Custom Port Overrides" com tabela e exemplos |
| `.log/handoff.md` | Este arquivo |

### Como funciona

`PortConfig` é um singleton de classe (sem instância necessária). Resolve na ordem:
1. Override do usuário (via `configure()` ou `configure_from_args()`)
2. Default do protocolo: RAW=9100, IPP=631, LPD=515, SNMP=161, FTP=21, HTTP=80, HTTPS=443, SMB=445, Telnet=23
3. Fallback opcional passado como argumento
4. 9100 como último recurso

### Exemplos de uso

```bash
# Impressora com RAW na 3910, SNMP na 1161
python printer-reaper.py 192.168.1.100 --scan --port-raw 3910 --port-snmp 1161

# Portas extras no scan de fingerprint
python printer-reaper.py 192.168.1.100 --scan --extra-ports 9200 --extra-ports 7100

# Brute-force com HTTP na 8080
python printer-reaper.py 192.168.1.100 --bruteforce --port-http 8080

# Campanha completa respeitando porta customizada
python printer-reaper.py 192.168.1.100 --attack-matrix --port-raw 3910
```

### Regra de design
Nenhum módulo usa porta literal para conexão. Todos chamam `PortConfig.resolve('<proto>')`.
Módulos que precisam de porta default em assinatura usam `port: int = 0` e resolvem via `PortConfig` internamente.

---

## v3.9.0 — 5-Engine Dork Discovery (FOFA + ZoomEye + Netlas)

**Data:** 2026-03-25
**Status:** COMPLETO

### Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/utils/discovery_online.py` | +`FOFASearcher`, `ZoomEyeSearcher`, `NetlasSearcher`; `DorkQueryBuilder` com `build_fofa_queries()`, `build_zoomeye_queries()`, `build_netlas_queries()`; `OnlineDiscoveryManager` com suporte a 5 engines e `_run_*()` helpers |
| `src/utils/config.py` | +entradas `fofa_search`, `zoomeye_search`, `netlas_search` em `FEATURE_REQUIREMENTS`; `_DEFAULTS` com fofa/zoomeye/netlas; +`fofa_credentials()`, `zoomeye_key()`, `netlas_key()` |
| `config.json.example` | +seções `fofa`, `zoomeye`, `netlas` com comentários de registro |
| `src/main.py` | +`--dork-engine` flag; handler `--discover-online` carrega credenciais de todos os 5 engines; validação de engines inválidos |
| `src/version.py` | 3.8.0 → 3.9.0 |
| `README.md` | Seção Discovery atualizada com 5 engines, tabela de sintaxe por engine, exemplos com `--dork-engine` |
| `.log/handoff.md` | Este arquivo |

### Funcionalidade: Multi-Engine Dork Discovery

**Antes (v3.8.0):** apenas Shodan e Censys.
**Agora (v3.9.0):** 5 engines com sintaxes nativas por plataforma:

| Engine | Sintaxe | Auth |
|--------|---------|------|
| Shodan | `"HP LaserJet" country:BR port:9100` | `api_key` |
| Censys | `services.banner="HP LaserJet" AND location.country_code="BR"` | `api_id` + `api_secret` |
| FOFA | `banner="HP LaserJet" && country="BR" && port="9100"` (base64-encoded) | `email` + `api_key` |
| ZoomEye | `banner:"HP LaserJet" +country:"BR" +port:9100` | `api_key` (JWT) |
| Netlas | `data.response:"HP LaserJet" AND geo.country_code:"BR" AND port:9100` | `X-API-Key` |

### Regra de filtro obrigatória

- **Nenhum engine executa sem ao menos um filtro** — `DiscoveryParams.has_filters()` é verificado antes de qualquer API call
- `--dork-engine` inválido causa erro imediato com lista de opções válidas
- Contexto de impressora é sempre implícito (port=9100/515/631 ou banner=@PJL injetados quando sem filtro de porta)

### Configuração necessária

```json
{
  "fofa":    [{ "email": "user@example.com", "api_key": "fofa_key_here" }],
  "zoomeye": [{ "api_key": "zoomeye_key_here" }],
  "netlas":  [{ "api_key": "netlas_key_here" }]
}
```

### Exemplos de uso

```bash
# Epson no Brasil via FOFA e Netlas
python printer-reaper.py --discover-online \
  --dork-vendor epson --dork-country BR --dork-engine fofa,netlas

# Todas as engines, HP em SP
python printer-reaper.py --discover-online \
  --dork-vendor hp --dork-city "Sao Paulo" --dork-port 9100

# ZoomEye somente, impressoras com porta 515 na América Latina
python printer-reaper.py --discover-online \
  --dork-port 515 --dork-region latin_america --dork-engine zoomeye
```

### Status final
- Sintaxes validadas por testes de saída das funções `build_*_queries()`
- Filtro obrigatório validado: `ValueError` levantado para `DiscoveryParams()` vazio
- Sem hardcoded credentials, sem busca aberta
- Todos os engines aceitam credenciais de `config.json` ou parâmetros diretos

### Próximos passos (opcional)
- Adicionar `--dork-engine all` como alias explícito
- Implementar cache de resultados por hash de query (`.log/discovery_cache/`)
- Suporte a paginação automática em ZoomEye para planos pagos

---

## v3.8.0 — Dork Discovery + Auto Exploit

**Data:** 2026-03-25
**Status:** COMPLETO

### Arquivos alterados

| Arquivo | Mudança |
|---------|---------|
| `src/utils/discovery_online.py` | Reescrito com `DorkQueryBuilder`, `DiscoveryParams`, `ShodanSearcher`, `CensysSearcher`, `PrinterHit`, `OnlineDiscoveryManager.targeted_search()` |
| `src/utils/exploit_manager.py` | Adicionados `auto_exploit()`, `_prefill_params()`, `AutoExploitResult`, `print_auto_exploit_summary()` |
| `src/main.py` | Adicionados flags `--dork-*` (9 flags), `--auto-exploit` (4 flags), handler `_run_auto_exploit()`, handler `--discover-online` reescrito |
| `src/version.py` | 3.7.0 → 3.8.0 |
| `README.md` | Seções Discovery e Auto Exploit atualizadas, versão e tabela de dork flags |
| `.log/handoff.md` | Este arquivo |

### Funcionalidade 1: Dork Discovery (`--discover-online`)

**Antes:** buscava com queries fixas hardcoded, sem filtros.
**Agora:**
- Classe `DiscoveryParams` com campos: vendors, model, countries, city, regions, ports, org, cpe, limit
- Classe `DorkQueryBuilder` gera queries Shodan e Censys a partir dos parâmetros
- Mapeamento de 12 regiões geográficas (`latin_america`, `south_america`, `europe`, etc.) para códigos ISO
- Mapeamento de nomes de países em pt-BR e en-US para códigos ISO
- Mapeamento de 20 vendors para termos de busca específicos
- `targeted_search()` executa as queries, deduplicando por IP:port
- Impressão formatada com tabela + estatísticas de distribuição por país
- Export automático para `.log/discovery_<timestamp>.json`
- Validação: se nenhum filtro e nenhum IP for fornecido, erro explicativo com sugestão de flags

**Flags adicionadas:**
```
--dork-vendor  (repeatable)
--dork-model
--dork-country (repeatable)
--dork-city
--dork-region  (repeatable)
--dork-port    (repeatable)
--dork-org
--dork-cpe
--dork-limit
```

### Funcionalidade 2: Auto Exploit (`--auto-exploit`)

**Fluxo:**
1. `grab_all()` → fingerprint do alvo
2. `match_exploits()` → candidatos por make/model/firmware/ports/CVEs
3. Sort por CVSS desc
4. `check()` nos top N (não-destrutivo)
5. `_prefill_params()` → preenche host, port, serial, mac, vendor automaticamente
6. `run()` nos top M confirmados (dry-run por padrão)
7. `print_auto_exploit_summary()` → tabela de resultados

**Flags adicionadas:**
```
--auto-exploit
--auto-exploit-limit N   (default: 8)
--auto-exploit-run N     (default: 1)
--auto-exploit-file FILE (custom exploit .py, parâmetros auto-preenchidos)
```

### Documentação

- Wiki: `Online-Discovery-Dorks.md` (novo) + `Auto-Exploit.md` (novo)
- Wiki: `Home.md` atualizado com links para as novas páginas
- README: seção Discovery reescrita com dorks, seção Auto Exploit adicionada
- Versão: 3.7.0 → 3.8.0

---

## Entry Point + GitHub Wiki — v3.7.0

**Data:** 2026-03-25
**Status:** COMPLETO

### Entry point atualizado

- `printer-reaper.py` reescrito como entry point limpo e definitivo para v3.7.0
- Usa `os.path.abspath(__file__)` para localizar `src/` independente do CWD
- Trata `KeyboardInterrupt` e `ImportError` com mensagens claras
- Docstring com exemplos de uso direto no arquivo
- Verificado: `python printer-reaper.py --version` → `printerreaper Version 3.7.0 (2026-03-25)`

### GitHub Wiki criada e publicada

Repositório: `https://github.com/mrhenrike/PrinterReaper/wiki`

| Página | Conteúdo |
|--------|----------|
| Home | Índice da wiki, quick reference |
| Installation | Requisitos, venv, Windows/Linux/macOS/Termux |
| Quick Start | 5 passos para o primeiro scan |
| Discovery | `--discover-local`, Shodan/Censys, WSD |
| Reconnaissance | `--scan`, `--scan-ml`, `--no-nvd`, auto-exploit matching |
| Interactive Shell | PJL (60+ comandos), PS (20+ comandos), PCL, batch mode |
| Brute Force | Todas as flags `--bf-*`, wordlists, tokens, variações, protocolos |
| Exploit Library | `--xpl-*`, catálogo completo, como escrever módulo custom |
| Attack Matrix | `--attack-matrix`, todas as categorias BlackHat 2017 + CVEs 2024-2025 |
| Lateral Movement | SSRF pivot, `--network-map`, LDAP hash capture, SMB hash capture |
| Storage & Firmware | `--storage`, `--firmware`, `--firmware-reset`, `--implant` |
| Cross-Site Printing | XSP tipos (info/capture/dos/nvram/exfil), CORS spoofing, deployment |
| Send Job | `--send-job`, protocolos, formatos, copias, queue LPD |
| Wordlists | Formato, seções de vendor, tokens dinâmicos, wordlists customizadas |
| Configuration | `config.json`, todas as keys, field reference |
| Supported Vendors | 15 vendors com creds padrão, protocolos, CVEs, exploits |

**Push realizado:** `afc36d7..fb02d5c master -> master` (wiki repo)

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

---

## v3.7.0 — Limpeza, PNGs, draw.io, logo, wiki — 2026-03-25

### Alterações
- **SVGs deletados**: img/printer_architecture.svg, img/printerreaper_workflow.svg, img/attack_coverage_matrix.svg, img/credential_wordlist_flow.svg
- **PNGs gerados** via Pillow (dark-theme, 960px+): printer_architecture.png, printerreaper_workflow.png, attack_coverage_matrix.png, credential_wordlist_flow.png
- **draw.io criados**: diagrams/printerreaper_workflow.drawio, diagrams/credential_flow.drawio, diagrams/attack_matrix.drawio (editáveis em app.diagrams.net)
- **Limpeza**: diagrams/CHANGELOG.md, scripts/help_selftest.py, scripts/selftest_help_run.py removidos
- **README.md**: logo União Geek restaurado no topo e footer, diagrams referenciados como PNG, tabela benchmark PrinterReaper vs PRET adicionada
- **printer-reaper.py**: entry point limpo com versão 3.7.0, KeyboardInterrupt e ImportError tratados
- **Wiki GitHub**: inicializada e publicada em https://github.com/mrhenrike/PrinterReaper/wiki — 7 páginas: Home, Installation, Quick-Start, Discovery, Reconnaissance, Interactive-Shell, Brute-Force

### Status
- Repository: https://github.com/mrhenrike/PrinterReaper — push confirmado (4c03781..9696c24)
- Wiki: https://github.com/mrhenrike/PrinterReaper/wiki — push confirmado (afc36d7)

---

## v3.14.0 — 2026-03-24

### Contexto
Sessão de troubleshooting de impressão real na Epson L3250 (192.168.0.152), com correções de bugs detectados em produção e novos recursos de instalação de impressora no host.

### Arquivos removidos
- `_test_text.txt` — artefato de teste temporário
- `_test_image.jpg` — artefato de teste temporário
- `_create_test_files.py` — script de teste temporário
- `config.yaml` — duplicado (API key real exposta; config.json é canônico)
- `config.yaml.example` — redundante com config.json.example

### Arquivos alterados
- `src/modules/print_job.py` — reescrito completamente:
  - `probe_printer()`: sonda IPP/LPD/RAW + SNMP status antes de enviar
  - `_probe_ipp()`: detecta se precisa de TLS (426 ou connection-reset)
  - `send_ipp()`: auto-upgrade TLS ao detectar ConnectionResetError (comportamento Epson)
  - `send_lpd()`: usa `l` (passthrough) no control file para ESC/P chegar ao motor
  - `_prepare_payload()`: prefer_escp=True para LPD → Epson inkjets (evita JPEG via LPD travado)
  - `_text_to_escp()`: geração de ESC/P nativo (idioma Epson, zero dependências)
  - `_image_to_escp_bitmap()`: conversão de imagem para ESC/P 24-pin via Pillow
  - `_classify_ipp_error()`: mensagens claras de restrição por código IPP
  - `PrinterCapabilities`: dataclass com resultado de probe + best_protocol
  - `PrintJobResult`: adicionado campo `hint` para orientação ao operador
  - Fallback IPP → LPD automático quando formato rejeitado e LPD disponível
- `src/modules/install_printer.py` — **novo módulo**:
  - Windows: PowerShell Add-Printer (RAW TCP/IP ou IPP Class Driver)
  - Linux/macOS: CUPS lpadmin (IPP Everywhere ou RAW socket)
  - Drivers: auto, generic, epson, hp, cups-ipp
- `src/main.py`:
  - `_run_send_job()`: redesign UX — probe antes de enviar, status SNMP, warnings de busy, hints de erro
  - `_run_install_printer()`: novo handler para --install-printer
  - `--send-proto`: default changed raw → auto (smart probe)
  - `--install-printer`, `--install-driver`, `--install-name`: novos flags
- `src/version.py`: bumped 3.13.0 → 3.14.0
- `README.md`: logo e versão União Geek removidos do header e footer

### Bugs corrigidos
- **Job JPEG via LPD travava a impressora**: JPEG raw não é formato nativo da Epson inkjet; corrigido para ESC/P via `prefer_escp=True` em LPD
- **IPP falha com WinError 10054**: Epson reseta conexões sem TLS; corrigido com retry automático via TLS ao detectar ConnectionResetError
- **Mensagens de erro genéricas**: substituídas por classificação por código IPP com hints acionáveis
- **send-proto padrão raw**: mudado para auto (probe automático)

### Testes executados
- `probe_printer(192.168.0.152)`: IPP=True (TLS required), LPD=True, RAW=False
- `python printer-reaper.py 192.168.0.152 --scan-ml --no-nvd`: executado (ver resultados abaixo)
- Import validation: `from modules.print_job import probe_printer, send_print_job` ✓
- `--help`: --install-printer, --install-driver, --install-name exibidos ✓

### Próximos passos
- Testar `--send-job` com `--send-proto auto` (requer printer idle)
- Testar `--install-printer 192.168.0.152` no host Windows
- Avaliar geração PWG Raster para envio via IPPS

