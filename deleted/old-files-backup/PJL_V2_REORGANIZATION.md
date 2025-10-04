# PrinterReaper v2.0 - Reorganização Completa PJL

## 🎯 Overview

Reorganização completa do PrinterReaper para focar exclusivamente no PJL, com comandos reorganizados por categorias funcionais e melhorias significativas na usabilidade.

## 🔧 Estrutura Reorganizada

### **📁 Sistema de Arquivos (12 comandos)**
- **`ls`** - Listar arquivos e diretórios
- **`mkdir`** - Criar diretórios
- **`find`** - Buscar arquivos recursivamente
- **`upload`** - Upload de arquivos para impressora
- **`download`** - Download de arquivos da impressora
- **`delete`** - Deletar arquivos
- **`copy`** - Copiar arquivos
- **`move`** - Mover arquivos
- **`touch`** - Criar/atualizar arquivos
- **`chmod`** - Alterar permissões de arquivo
- **`permissions`** - Testar permissões de arquivo
- **`mirror`** - Backup completo do sistema de arquivos

### **ℹ️ Informações do Sistema (8 comandos)**
- **`id`** - Identificação da impressora
- **`version`** - Versão do firmware/serial
- **`info`** - Informações detalhadas por categoria
- **`product`** - Informações do produto (modelo, serial, firmware)
- **`network`** - Informações de rede
- **`wifi`** - Informações WiFi
- **`variables`** - Variáveis de ambiente
- **`printenv`** - Variável específica

### **⚙️ Controle e Configuração (8 comandos)**
- **`set`** - Definir variáveis de ambiente
- **`display`** - Mostrar mensagens no display
- **`offline`** - Colocar impressora offline
- **`restart`** - Reiniciar impressora
- **`reset`** - Resetar para padrões de fábrica
- **`selftest`** - Testes de autodiagnóstico
- **`backup`** - Backup de configurações
- **`restore`** - Restaurar configurações

### **🔒 Segurança e Acesso (4 comandos)**
- **`lock`** - Bloquear impressora com PIN
- **`unlock`** - Desbloquear impressora
- **`disable`** - Desabilitar funcionalidades
- **`nvram`** - Acessar/manipular NVRAM

### **💥 Ataques e Testes (4 comandos)**
- **`destroy`** - Ataque de negação de serviço
- **`flood`** - Flood de comandos
- **`hold`** - Manter jobs em espera
- **`format`** - Formatar sistema de arquivos

### **🌐 Rede e Conectividade (3 comandos)**
- **`direct`** - Configurações de impressão direta
- **`execute`** - Executar comandos PJL arbitrários
- **`load`** - Carregar comandos de arquivo

### **📊 Monitoramento (2 comandos)**
- **`pagecount`** - Manipular contador de páginas
- **`status`** - Toggle de mensagens de status

## 🚀 Melhorias Implementadas

### **1. Novos Comandos Essenciais**
- **`upload`** - Upload de arquivos para impressora
- **`download`** - Download de arquivos da impressora
- **`delete`** - Deletar arquivos
- **`copy`** - Copiar arquivos
- **`move`** - Mover arquivos
- **`chmod`** - Alterar permissões
- **`backup`** - Backup de configurações
- **`restore`** - Restaurar configurações

### **2. Nomes de Comandos Melhorados**
- **`df`** → **`diskspace`** (mais claro)
- **`free`** → **`memory`** (mais claro)
- **`env`** → **`variables`** (mais claro)
- **`site`** → **`execute`** (mais claro)

### **3. Sistema de Help Organizado**
- **Help por categoria**: `help filesystem`, `help system`, etc.
- **Help específico**: `help <command>`
- **Categorias lógicas**: Comandos agrupados por função

### **4. Funcionalidades Aprimoradas**
- **Upload/Download**: Transferência completa de arquivos
- **Manipulação de arquivos**: Copy, move, delete, chmod
- **Backup/Restore**: Gerenciamento de configurações
- **Controle de permissões**: Teste e alteração de permissões

## 📊 Comparação v1.x vs v2.0

### **v1.x (35 comandos)**
- Comandos misturados sem categorização
- Nomes confusos (df, free, env, site)
- Funcionalidades limitadas
- Help básico

### **v2.0 (41 comandos)**
- Comandos organizados por categoria
- Nomes claros e intuitivos
- Funcionalidades completas
- Help organizado por categoria

## 🎯 Benefícios da Reorganização

### **1. Usabilidade**
- **Comandos intuitivos**: Nomes claros e descritivos
- **Categorias lógicas**: Comandos agrupados por função
- **Help organizado**: Fácil navegação e descoberta

### **2. Funcionalidade**
- **Cobertura completa**: Todos os aspectos do PJL cobertos
- **Comandos essenciais**: Upload, download, backup, restore
- **Manipulação completa**: Arquivos, permissões, configurações

### **3. Manutenibilidade**
- **Código organizado**: Estrutura clara e lógica
- **Categorias bem definidas**: Fácil expansão e manutenção
- **Documentação integrada**: Help system completo

## 🔧 Estrutura de Arquivos

### **Arquivos Movidos para Backup**
- `src/modules/postscript.py` → `old-files-backup/`
- `src/modules/pcl.py` → `old-files-backup/`
- `src/modules/cve.py` → `old-files-backup/`
- `src/core/cve_*.py` → `old-files-backup/`
- `src/core/language_detector.py` → `old-files-backup/`
- `src/core/http_connector.py` → `old-files-backup/`
- `src/core/connection_manager.py` → `old-files-backup/`
- `src/core/logger.py` → `old-files-backup/`
- `src/core/error_handler.py` → `old-files-backup/`
- `src/core/retry_manager.py` → `old-files-backup/`
- `src/core/printer_detector.py` → `old-files-backup/`
- `src/osint/` → `old-files-backup/`
- `src/core/db/pcl.dat` → `old-files-backup/`
- `src/core/db/ps.dat` → `old-files-backup/`

### **Arquivos Mantidos**
- `src/modules/pjl.py` (original)
- `src/modules/pjl_v2.py` (nova versão)
- `src/core/db/pjl.dat` (base de dados PJL)
- `src/core/printer.py` (classe base)
- `src/utils/` (utilitários)
- `src/version.py` (atualizado para v2.0.0)

## 🎯 Próximos Passos

### **1. Testes**
- Testar todos os comandos PJL v2.0
- Verificar funcionalidades de upload/download
- Validar sistema de help

### **2. Integração**
- Integrar PJL v2.0 no main.py
- Atualizar sistema de detecção
- Configurar fallback para PJL original

### **3. Documentação**
- Atualizar README.md
- Criar guia de usuário
- Documentar comandos por categoria

## 📈 Métricas de Melhoria

### **Comandos**
- **v1.x**: 35 comandos
- **v2.0**: 41 comandos (+17% aumento)

### **Categorias**
- **v1.x**: Comandos misturados
- **v2.0**: 7 categorias organizadas

### **Funcionalidades**
- **v1.x**: Funcionalidades básicas
- **v2.0**: Cobertura completa do PJL

### **Usabilidade**
- **v1.x**: Help básico
- **v2.0**: Sistema de help organizado

---

**PrinterReaper v2.0** - Foco exclusivo em PJL com comandos reorganizados e funcionalidades completas.

*Para mais informações, visit: https://github.com/mrhenrike/PrinterReaper*
