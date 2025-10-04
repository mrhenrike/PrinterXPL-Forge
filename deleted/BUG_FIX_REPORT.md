# Bug Fix Report - PrinterReaper Loop Infinito

## Resumo
Identificado e corrigido bug crítico que causava loop infinito no PrinterReaper quando comandos eram carregados de arquivo usando a opção `-i`.

## Análise do Problema

### Sintoma
Quando o programa era executado com a opção `-i` (load commands from file), após executar todos os comandos do arquivo (incluindo `exit`), o programa entrava em loop infinito imprimindo apenas o prompt `:/> ` repetidamente.

### Causa Raiz
O problema estava na interação entre `__init__` e `cmdloop()`:

1. **Em `src/core/printer.py` (linha 92-95)**:
   ```python
   if args.load:
       self.do_load(args.load)
       # Exit after loading commands from file
       return
   ```
   - O `__init__` executava `do_load()` e então retornava
   - O `do_load()` executava todos os comandos do arquivo, incluindo `exit`
   - Mas o `return` apenas saía do `__init__`, não impedia o `cmdloop()` de ser chamado

2. **Em `src/main.py` (linha 194-196)**:
   ```python
   shell_class = shell_map[args.mode]
   shell = shell_class(args)
   shell.cmdloop()  # <-- SEMPRE era chamado, mesmo após carregar comandos
   ```
   - O `cmdloop()` era SEMPRE chamado, independentemente de os comandos terem sido executados
   - Como não havia comandos pendentes, o `cmdloop()` ficava esperando input infinitamente
   - Isso resultava no loop infinito do prompt

## Solução Implementada

### 1. Adicionado flag de controle em `src/core/printer.py`
```python
# Linha 64
should_exit = False  # Flag to indicate if shell should exit
```

### 2. Modificado `__init__` para definir o flag
```python
# Linhas 93-96
if args.load:
    self.do_load(args.load)
    # Mark that shell should exit after loading commands
    self.should_exit = True
```

### 3. Modificado `main.py` para verificar o flag
```python
# Linhas 193-199
# Instantiate and run the chosen shell.
shell_class = shell_map[args.mode]
shell = shell_class(args)

# Only enter interactive loop if not exiting from loaded commands
if not shell.should_exit:
    shell.cmdloop()
```

## Testes Realizados

### Teste 1: Arquivo Simples (test_simple.txt)
```bash
$ python3 printer-reaper.py test pjl -q -i test_simple.txt
Executing: help
[... output ...]
Executing: exit
SUCCESS: Program exited normally
```
✅ **PASSOU** - Programa sai corretamente após executar comandos

### Teste 2: Arquivo Complexo (test_qa_commands.txt)
```bash
$ python3 printer-reaper.py test pjl -q -i test_qa_commands.txt
[... executa todos os comandos ...]
Executing: exit
```
✅ **PASSOU** - Programa executa todos os 68 comandos e sai normalmente

### Teste 3: Modo Interativo (sem -i)
```bash
$ python3 printer-reaper.py test pjl
test:/> help
[... output ...]
test:/> exit
```
✅ **PASSOU** - Modo interativo continua funcionando normalmente

## Arquivos Modificados
1. `src/core/printer.py` - Adicionado flag `should_exit` e lógica de controle
2. `src/main.py` - Adicionado verificação do flag antes de chamar `cmdloop()`

## Impacto
- ✅ Corrigido loop infinito ao usar `-i` para carregar comandos de arquivo
- ✅ Modo interativo continua funcionando normalmente
- ✅ Todos os comandos são executados corretamente antes de sair
- ✅ Sem introdução de novos bugs ou problemas de lint

## Conclusão
O bug foi causado por uma falha na lógica de fluxo de controle onde o `cmdloop()` era sempre chamado, mesmo quando os comandos já tinham sido executados a partir de um arquivo. A solução implementa um mecanismo de flag simples e eficaz que permite ao shell saber quando deve ou não entrar no loop interativo.

---
**Data**: 2025-10-04
**Versão**: 2.2.14
**Status**: ✅ CORRIGIDO E TESTADO

