## PrinterReaper Packaging Hub

Este diretório centraliza os **4 caminhos de distribuição** do PrinterReaper.

- `01-pypi/` -> build e publicação PyPI (`pip install printer-reaper`)
- `02-deb/` -> pacote `.deb` (Debian/Ubuntu/Kali)
- `03-rpm/` -> pacote `.rpm` (RHEL/Fedora/Rocky/Alma)
- `04-pipx/` -> instalação isolada com `pipx` (implementado por último)
- `man/` -> fonte do man page (`printer-reaper.1`)

### Ordem de execução recomendada

1. Caminho 1 (PyPI/wheel)  
2. Caminho 2 (DEB)  
3. Caminho 3 (RPM)  
4. Caminho 4 (pipx)  

### Pré-requisitos gerais

- Python 3.8+
- `pip`, `venv`
- projeto atualizado em `master`

### Versão do release

A versão oficial deve ser sempre sincronizada com `src/version.py`.

Comando para conferir:

```bash
python -c "import sys; sys.path.insert(0,'src'); import version; print(version.__version__)"
```

### Atalhos rápidos

Linux/macOS:

```bash
./packages/01-pypi/build.sh
./packages/02-deb/prepare.sh && ./packages/02-deb/build.sh
./packages/03-rpm/build.sh
./packages/04-pipx/validate.sh
```

Windows PowerShell:

```powershell
.\packages\01-pypi\build.ps1
.\packages\02-deb\prepare.ps1
.\packages\03-rpm\prepare.ps1
.\packages\04-pipx\validate.ps1
```

### Observação de layout

O caminho DEB exige `debian/` na raiz no momento do build (`dpkg-buildpackage`).
Por isso, o subdiretório `02-deb/` contém um passo `prepare` que sincroniza os
templates para a raiz automaticamente.

