## Caminho 4 - pipx (implementado por último)

Este é o caminho recomendado para uso operacional isolado (sem poluir Python do sistema).

### Instalação do pipx

```bash
python -m pip install --user pipx
python -m pipx ensurepath
```

### Instalar PrinterReaper

Publicado no PyPI:

```bash
pipx install printer-reaper
```

A partir do checkout local:

```bash
pipx install --editable .
```

### Extras opcionais

```bash
pipx inject printer-reaper shodan censys scikit-learn
```

### Validar

```bash
printer-reaper --version
printer-reaper --help
```

