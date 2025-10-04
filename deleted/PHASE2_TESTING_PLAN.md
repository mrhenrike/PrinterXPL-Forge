# Fase 2: Real-World Testing Plan - PrinterReaper v2.3.3
**Impressora Alvo**: 15.204.211.244 (HP LaserJet 4200)  
**Objetivo**: Validar todos os 54 comandos PJL com impressora real  
**Duração Estimada**: 2-3 horas  
**Data**: 2025-10-04

---

## 🎯 ESTRATÉGIA DE TESTES

### Princípios:
1. ✅ **Safety First** - Começar com comandos não-destrutivos
2. ✅ **Progressive** - Do mais seguro ao mais perigoso
3. ✅ **Documented** - Registrar cada resultado
4. ✅ **Reversible** - Sempre com opção de cleanup

### Categorias de Risco:

| Risco | Comandos | Ordem |
|-------|----------|-------|
| 🟢 SAFE | Info gathering, read-only | 1º |
| 🟡 LOW | File operations (non-destructive) | 2º |
| 🟠 MEDIUM | Configuration changes (reversible) | 3º |
| 🔴 HIGH | DoS, manipulation (com backup) | 4º |
| ⚫ EXTREME | Destructive (SKIP ou com aprovação) | 5º |

---

## 📝 TESTE 1: INFORMATION GATHERING (🟢 SAFE)

### Comandos (15):
```bash
# Básico
id
pwd
timeout
status

# Advanced Info
info
info CONFIG
info MEMORY
info FILESYS
scan_volumes
firmware_info
variables
printenv PATH
network
pagecount
```

**Resultado Esperado**: Informações da impressora sem modificações

---

## 📝 TESTE 2: FILESYSTEM READ (🟢 SAFE)

### Comandos (8):
```bash
# Navigation
chvol 0:
chvol 1:
cd /
ls
ls 0:
ls 1:

# Scanning
find
scan_volumes

# Path Traversal (read-only)
traverse
cat /etc/passwd
```

**Resultado Esperado**: Listagens de diretório, sem escrita

---

## 📝 TESTE 3: FILE OPERATIONS (🟡 LOW RISK)

### Comandos (10):
```bash
# Upload test file (safe)
upload LICENSE test_upload.txt

# Read uploaded file
cat test_upload.txt
ls

# Download file
download test_upload.txt downloaded_test.txt

# Append (reversible)
append test_upload.txt "Test line from PrinterReaper"
cat test_upload.txt

# Copy/Move (reversible)
copy test_upload.txt test_copy.txt
move test_copy.txt test_moved.txt
ls

# Cleanup
pjl_delete test_upload.txt
pjl_delete test_moved.txt
ls
```

**Resultado Esperado**: Operações de arquivo funcionando corretamente

---

## 📝 TESTE 4: CONFIGURATION (🟡 LOW - Reversible)

### Comandos (8):
```bash
# Set variables (reversible)
set TESTVAR=testvalue
printenv TESTVAR
variables | grep TEST

# Display (reversible)
display "PrinterReaper Test - OK"

# Backup config first!
backup printer_config_backup.txt

# Page counter (can restore)
pagecount
pagecount 999
pagecount

# Restore if needed
# restore printer_config_backup.txt
```

**Resultado Esperado**: Configurações temporárias, restauráveis

---

## 📝 TESTE 5: JOB MANIPULATION (🟠 MEDIUM)

### Comandos (3):
```bash
# Enable job retention (reversible)
hold

# Capture jobs (read-only)
capture

# If jobs exist
capture download
```

**Resultado Esperado**: Jobs capturados (se existirem)

---

## 📝 TESTE 6: ADVANCED ATTACKS (🔴 HIGH - Com Cautela)

### Comandos Safe para Testar (5):
```bash
# Exfiltration (read-only)
exfiltrate

# Info gathering
info

# Lock/Unlock (cuidado - pode travar!)
# SKIP lock/unlock em produção

# Poison (COM BACKUP PRIMEIRO!)
# backup config_before_poison.txt
# poison
# restore config_before_poison.txt
```

**Resultado Esperado**: Exfiltração de arquivos acessíveis

---

## 📝 TESTE 7: DOS TESTS (🔴 HIGH - SKIP em Produção)

### ⚠️ COMANDOS PERIGOSOS - NÃO EXECUTAR SEM APROVAÇÃO:

```bash
# THESE WILL BE SKIPPED OR TESTED ONLY WITH EXPLICIT APPROVAL:

# dos_display      # Spam display (reversible via power cycle)
# dos_jobs         # Queue flooding (pode afetar outros usuários)
# dos_connections  # Network flooding (DETECTÁVEL)
# hang             # Pode CRASHAR impressora
# destroy          # DANO FÍSICO - NUNCA TESTAR
# format           # PERDA DE DADOS - NUNCA TESTAR
# reset            # Factory reset - CUIDADO
```

**Decisão**: ❌ **SKIP DESTRUTIVOS** - Apenas documentar

---

## 📊 MATRIZ DE TESTES

| # | Comando | Categoria | Risco | Testar? | Prioridade |
|---|---------|-----------|-------|---------|------------|
| 1-15 | Info commands | Info | 🟢 | ✅ SIM | P0 |
| 16-23 | Filesystem read | Filesystem | 🟢 | ✅ SIM | P0 |
| 24-33 | File operations | Filesystem | 🟡 | ✅ SIM | P1 |
| 34-41 | Configuration | Control | 🟡 | ✅ SIM | P1 |
| 42-44 | Job manipulation | Jobs | 🟠 | ✅ SIM | P1 |
| 45-49 | Advanced | Advanced | 🔴 | ⚠️ PARCIAL | P2 |
| 50-54 | DoS/Destructive | Attacks | ⚫ | ❌ SKIP | P3 |

**Total a Testar**: ~45 comandos (safe + low + medium risk)  
**Total a Skip**: ~9 comandos (destructive/dangerous)

---

## ✅ DELIVERABLES

Ao final da Fase 2, teremos:

1. **PJL_COMPATIBILITY_REPORT.md**
   - Cada comando testado
   - Resultado (sucesso/falha/parcial)
   - Comportamento observado
   - Notas específicas da impressora

2. **test_real_world.txt**
   - Script de teste executado
   - Comandos em ordem de segurança

3. **PHASE2_RESULTS.md**
   - Resumo dos testes
   - Taxa de compatibilidade
   - Bugs encontrados (se houver)
   - Recomendações

4. **v2.3.4 Release**
   - Bug fixes (se necessário)
   - Tested & validated
   - Production-ready certification

---

## 🚀 EXECUÇÃO

### Próximos Passos:

1. ⏭️ Criar test_real_world.txt com comandos seguros
2. ⏭️ Executar testes com a impressora
3. ⏭️ Documentar resultados
4. ⏭️ Ajustar código se necessário
5. ⏭️ Release v2.3.4

**Pronto para começar os testes!**

