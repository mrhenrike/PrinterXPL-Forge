# Deleted Files Archive

Esta pasta contém arquivos que foram "deletados" do projeto principal, mas que são mantidos para referência futura.

## Política de Arquivos

- **Nunca deletar arquivos permanentemente** - sempre mover para esta pasta
- **Esta pasta NÃO é publicada no GitHub** (está no .gitignore)
- **Arquivos podem ser restaurados** se necessário
- **Organização por data** quando possível

## Estrutura

- `deleted/` - Pasta principal para arquivos removidos
- `deleted/YYYY-MM-DD/` - Organização por data (quando aplicável)
- `deleted/backup/` - Backups de arquivos importantes

## Uso

Para "deletar" um arquivo:
```bash
# Em vez de: rm arquivo.txt
# Use: move arquivo.txt deleted/
```

Para restaurar um arquivo:
```bash
# Mover de volta para o local original
move deleted/arquivo.txt ./
```

## Notas

- Esta pasta é local e não sincronizada com Git
- Arquivos podem ser organizados por data ou categoria
- Sempre documentar o motivo da remoção quando possível
