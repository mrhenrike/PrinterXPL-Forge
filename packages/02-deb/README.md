## Caminho 2 - Debian Package (.deb)

Empacotamento para Debian/Ubuntu/Kali com `dpkg-buildpackage`.

### Estrutura

- `debian/` -> templates oficiais do pacote Debian
- `prepare.sh` / `prepare.ps1` -> sincroniza `debian/` para a raiz do projeto
- `build.sh` -> executa `dpkg-buildpackage`

### Fluxo

```bash
./packages/02-deb/prepare.sh
./packages/02-deb/build.sh
```

Saída esperada:

- `../printer-reaper_<versao>-1_all.deb`

### Instalação

```bash
sudo dpkg -i ../printer-reaper_*_all.deb
sudo apt-get install -f
printer-reaper --version
```

