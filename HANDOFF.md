# HANDOFF — PrinterXPL-Forge

## [2026-09-13 16:30] — Bump v6.4.0: CVE expansion + ACL + catalog hygiene

### Estado ao encerrar

- Versao bumped: **6.3.1 -> 6.4.0** em `pyproject.toml` e `src/version.py`
- Todas as alteracoes estao **unstaged** (nenhum commit realizado)
- 19/19 testes passando (`pytest tests/ -q`)

**Fase A - Fundacao:**
- Corrigido bug de merge de metadata em `src/utils/exploit_manager.py`: JSON agora prevalece sobre placeholders `UNKNOWN` em METADATA Python
- `xpl/ipp/` integrada ao loader (IPP-CUPS-TRAVERSAL-001, IPP-INFO-001)
- `tools/generate_xpl_manifest.py` restaurado (estava ausente no tree)
- `xpl/index.json` regenerado: 210 exploits (`exploits[]` key, nao mais `modules[]`)
- `src/data/xpl_manifest.json` regenerado: 210 modulos, `by_era.modern` 109
- `src/data/cve_catalog.json` `_meta.version` alinhado 6.0.0 -> 6.3.1
- `wiki/CVE-Catalog.md` timeline estendida 2025-2026

**Fase B - ACL (PR #3):**
- `src/modules/acl.py` reescrito com bugs corrigidos:
  - `hp_checksum`: `% 1` -> `% 2` (odd byte handling)
  - `do_reset`: `NameError` em `rlen` removido
  - Resposta `b""` nao mais passada para `struct.unpack`
  - Acesso a `_sock` protegido via `_raw_recv()` e `_get_raw_socket()`
  - Ops destrutivas (burnspiflash/burnflash/fixnvram/reset) exigem `_TESTED_MODELS_DESTRUCTIVE` allowlist + confirmacao
  - Limite de tamanho de firmware: `_MAX_FW_SIZE_BYTES = 16 MiB`
- `tests/test_acl.py` adicionado: 17 testes de checksum, parser e constantes

**Fase C - Novos CVEs (16 entradas, 18 modulos):**
- Lexmark ESF/PS 2025: CVE-2025-65077/65078/65080/65081/9269/1127/4044
- HP PostScript 2025: CVE-2025-26507/26508 + metadata.json para CVE-2025-26506
- HP WSD Scan 2026: CVE-2026-4682
- Canon remote mgmt 2026: CVE-2026-1789
- Brother/Fujifilm/Toshiba/Konica spillover: CVE-2024-51979/51981/51982
- CUPS 2025: CVE-2025-58060/58364
- Todos os modulos sao `check`-first com `dry_run=True` por padrao

### Arquivos modificados

```
CHANGELOG.md
pyproject.toml
src/data/cve_catalog.json
src/data/xpl_manifest.json
src/modules/acl.py                          (novo)
src/utils/exploit_manager.py
src/version.py
tests/test_acl.py                           (novo)
tools/generate_xpl_manifest.py             (novo)
wiki/CVE-Catalog.md
xpl/index.json
xpl/ipp/ipp_cups_document_uri_traversal.py
xpl/ipp/ipp_get_printer_attrs_info_leak.py
xpl/research/research-brother-stack-bof-51979/  (novo)
xpl/research/research-brother-wsd-dos-51981/    (novo)
xpl/research/research-brother-wsd-info-51982/   (novo)
xpl/research/research-canon-remote-mgmt-2026-1789/  (novo)
xpl/research/research-cups-2025-58060/     (novo)
xpl/research/research-cups-2025-58364/     (novo)
xpl/research/research-hp-ps-bof-2025-26507/    (novo)
xpl/research/research-hp-ps-bof-2025-26508/    (novo)
xpl/research/research-hp-wsd-scan-rce-2026-4682/   (novo)
xpl/research/research-hp-xps-bof/metadata.json (novo)
xpl/research/research-lexmark-driver-xxe-2025-4044/    (novo)
xpl/research/research-lexmark-esf-path-traversal-2025-65077/   (novo)
xpl/research/research-lexmark-esf-search-path-2025-65078/  (novo)
xpl/research/research-lexmark-ews-path-traversal-2025-1127/    (novo)
xpl/research/research-lexmark-ps-oob-read-2025-65081/  (novo)
xpl/research/research-lexmark-ps-type-confusion-2025-65080/    (novo)
xpl/research/research-lexmark-ssrf-ews-2025-9269/  (novo)
```

### Commits realizados

- `8ca0795` — Expand CVE catalog to 136 entries, add 18 check-first modules, fix ACL protocol module
- Tag: `v6.4.0` publicada em `origin`
- Push: `682e398..8ca0795  master -> master` (GitHub)

### Proximo passo imediato

Antes de commitar/pushar:
1. **OBRIGATORIO - Regra Magna**: Remover `publish-pypi.yml` do rastreamento Git e adicionar ao `.gitignore` do submódulo:
   ```bash
   cd D:\Projetos-SafeLabs\submodules\Uniao-Geek\PrinterXPL-Forge
   git rm --cached .github/workflows/publish-pypi.yml
   echo ".github/workflows/" >> .gitignore
   ```
2. Revisar se `packages/` precisa de tratamento similar (os READMEs podem ficar, mas `prepare.sh`, `prepare.ps1` sao packaging scripts)
3. Confirmar identidade: `git config user.name` / `git config user.email`
4. Commitar com mensagem limpa (sem mencao a ferramentas/AI):
   ```bash
   git add -A
   git commit -m "Expand CVE catalog to 136 entries, add 18 check-first modules, fix ACL protocol module"
   git push origin master
   ```
5. Criar tag: `git tag -a v6.4.0 -m "Release 6.4.0"`

### Pendencias conhecidas

- [ ] Remover `.github/workflows/publish-pypi.yml` do VCS (regra magna de repos publicos)
- [ ] CVE-2025-4045/4046 (Lexmark Print Mgmt Client): nao modelados (escopo de cliente local, fora do escopo de rede)
- [ ] Validar modulos ACL novos em hardware HP P2035n autorizado antes de push
- [ ] `cve_catalog.json` tem 4 entradas com `attack_type: "?"` (CUPS 2025 - detalhe nao publico ainda)
- [ ] Falta reescrever `ipp_cups_document_uri_traversal.py` para usar `dry_run` de forma mais granular
- [ ] Investigar `CVE-2025-26506`: advisory HP diz PostScript, modulo envia XPS - provavelmente ambos sao vetores validos mas merece confirmacao em lab

### Ambiente necessario

- Python 3.8+ (testado em 3.13.5 local)
- `pytest` para testes: `pip install pytest`
- Sem venv obrigatorio para comandos de validacao (usa Python do sistema)
- `PXF_PROFILE=all` para carregar todos os modulos sem filtro de perfil

### Paths importantes

- Windows: `D:\Projetos-SafeLabs\submodules\Uniao-Geek\PrinterXPL-Forge`
- Linux: `/mnt/predator/Projetos-SafeLabs/submodules/Uniao-Geek/PrinterXPL-Forge`
- Catalogo CVE: `src/data/cve_catalog.json` (136 entradas)
- Indice de exploits: `xpl/index.json` (210 exploits)
- Manifest de perfis: `src/data/xpl_manifest.json` (210 modulos)
- Gerador de manifest: `tools/generate_xpl_manifest.py`
- Modulo ACL corrigido: `src/modules/acl.py`
- Testes ACL: `tests/test_acl.py`

## [2026-09-14] TupaXPL-Forge - Sugestao de evolucao upstream

### Origem
TupaXPL-Forge inclui Print Spooler como vetor de propagacao (referencia Stuxnet).
EmbedXPL bridge ja cobre modulos de impressora via EmbedXPL-Forge.

### Pendencias para PR
- [ ] Print Spooler LPE como modulo PrinterXPL nativo
- [ ] Abrir issue: "feat: add Print Spooler privilege escalation module"

## [2026-09-14 17:50] -- New exploit modules: Epson BOF, PrintNightmare, LPD injection

### Estado ao encerrar
- Adicionados 3 novos modulos de exploit
- epson_l14150_raw_bof_cve_2026_39047.py: BOF via RAW protocol porta 9100
- print_nightmare_cve_2021_1675_34527.py: PrintNightmare RCE+LPE via impacket/Mimispool
- lpd_shell_injection_rfc1179.py: LPD job name single-quote breakout RCE

### Proximo passo imediato
- Adicionar PaperCut RCE module
- Adicionar HP JetDirect path traversal

### Pendencias
- [ ] papercut/papercut_rce.py
- [ ] hp/hp_jetdirect_path_traversal.py

## [2026-09-14 19:05] -- Pendencias adicionais resolvidas

### Concluido nesta sub-sessao
- PaperCut CVE-2023-27350 RCE module adicionado: xpl/exploits/papercut/
- HP JetDirect path traversal adicionado: xpl/exploits/hp/hp_jetdirect_path_traversal.py
- publish-pypi.yml ja estava no .gitignore (regra magna ja estava respeitada)
- Commit: c6768e3

### Pendencias remanescentes (low priority)
- [ ] CVE-2025-4045/4046 (Lexmark Print Mgmt Client): fora do escopo de rede
- [ ] Validar modulos ACL em hardware HP P2035n
- [ ] Print Spooler LPE (CVE-2021-34527 Mimispool ja foi adicionado na sessao anterior)
