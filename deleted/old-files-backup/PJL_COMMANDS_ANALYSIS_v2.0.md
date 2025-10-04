# PrinterReaper v2.0 - Análise Completa dos Comandos PJL

## 🎯 Overview

Análise completa dos comandos PJL disponíveis no PrinterReaper, organizados por categorias funcionais para a versão 2.0.

## 📋 Comandos PJL Atuais (35 comandos)

### **🔍 Sistema de Arquivos (8 comandos)**
- **`ls`** - Listar arquivos e diretórios
- **`mkdir`** - Criar diretórios
- **`find`** - Buscar arquivos recursivamente
- **`mirror`** - Fazer backup completo do sistema
- **`df`** - Mostrar espaço em disco (alias para info filesys)
- **`free`** - Mostrar memória livre (alias para info memory)
- **`touch`** - Criar/atualizar arquivos
- **`permissions`** - Testar permissões de arquivo

### **ℹ️ Informações do Sistema (8 comandos)**
- **`id`** - Identificação da impressora
- **`env`** - Variáveis de ambiente (alias para info variables)
- **`version`** - Versão do firmware/serial
- **`info`** - Informações detalhadas por categoria
- **`printenv`** - Mostrar variável específica
- **`product`** - Informações do produto (modelo, serial, firmware)
- **`network`** - Informações de rede
- **`wifi`** - Informações WiFi

### **⚙️ Controle e Configuração (6 comandos)**
- **`set`** - Definir variáveis de ambiente
- **`display`** - Mostrar mensagens no display
- **`offline`** - Colocar impressora offline
- **`restart`** - Reiniciar impressora
- **`reset`** - Resetar para padrões de fábrica
- **`selftest`** - Testes de autodiagnóstico

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
- **`site`** - Executar comandos PJL arbitrários
- **`load`** - Carregar comandos de arquivo

### **📊 Monitoramento (2 comandos)**
- **`pagecount`** - Manipular contador de páginas
- **`status`** - Toggle de mensagens de status

## 🔧 Análise de Melhorias Necessárias

### **1. Nomes de Comandos Confusos**
- **`df`** → **`diskspace`** (mais claro)
- **`free`** → **`memory`** (mais claro)
- **`env`** → **`variables`** (mais claro)
- **`site`** → **`execute`** (mais claro)

### **2. Comandos Faltando**
- **`upload`** - Upload de arquivos
- **`download`** - Download de arquivos
- **`delete`** - Deletar arquivos
- **`copy`** - Copiar arquivos
- **`move`** - Mover arquivos
- **`chmod`** - Alterar permissões
- **`backup`** - Backup de configurações
- **`restore`** - Restaurar configurações

### **3. Categorias Reorganizadas**

#### **📁 Sistema de Arquivos (12 comandos)**
- **`ls`** - Listar arquivos e diretórios
- **`mkdir`** - Criar diretórios
- **`find`** - Buscar arquivos
- **`upload`** - Upload de arquivos
- **`download`** - Download de arquivos
- **`delete`** - Deletar arquivos
- **`copy`** - Copiar arquivos
- **`move`** - Mover arquivos
- **`touch`** - Criar/atualizar arquivos
- **`chmod`** - Alterar permissões
- **`permissions`** - Testar permissões
- **`mirror`** - Backup completo

#### **ℹ️ Informações do Sistema (8 comandos)**
- **`id`** - Identificação da impressora
- **`version`** - Versão do firmware
- **`info`** - Informações detalhadas
- **`product`** - Informações do produto
- **`network`** - Informações de rede
- **`wifi`** - Informações WiFi
- **`variables`** - Variáveis de ambiente
- **`printenv`** - Variável específica

#### **⚙️ Controle e Configuração (8 comandos)**
- **`set`** - Definir variáveis
- **`display`** - Mostrar mensagens
- **`offline`** - Colocar offline
- **`restart`** - Reiniciar
- **`reset`** - Resetar configurações
- **`selftest`** - Testes de diagnóstico
- **`backup`** - Backup de configurações
- **`restore`** - Restaurar configurações

#### **🔒 Segurança e Acesso (4 comandos)**
- **`lock`** - Bloquear impressora
- **`unlock`** - Desbloquear impressora
- **`disable`** - Desabilitar funcionalidades
- **`nvram`** - Acessar NVRAM

#### **💥 Ataques e Testes (4 comandos)**
- **`destroy`** - Ataque de negação de serviço
- **`flood`** - Flood de comandos
- **`hold`** - Manter jobs em espera
- **`format`** - Formatar sistema

#### **🌐 Rede e Conectividade (3 comandos)**
- **`direct`** - Configurações de impressão direta
- **`execute`** - Executar comandos PJL
- **`load`** - Carregar comandos de arquivo

#### **📊 Monitoramento (2 comandos)**
- **`pagecount`** - Manipular contador de páginas
- **`status`** - Toggle de mensagens de status

## 🚀 Proposta para v2.0

### **1. Reorganização por Categorias**
- **Comandos agrupados logicamente**
- **Nomes mais claros e intuitivos**
- **Funcionalidades completas**

### **2. Novos Comandos Essenciais**
- **Upload/Download de arquivos**
- **Manipulação de arquivos (copy, move, delete)**
- **Backup/Restore de configurações**
- **Controle de permissões**

### **3. Interface Melhorada**
- **Help por categoria**
- **Comandos agrupados**
- **Nomes mais intuitivos**
- **Funcionalidades completas**

## 📈 Benefícios da Reorganização

### **1. Usabilidade**
- **Comandos mais intuitivos**
- **Categorias lógicas**
- **Help organizado**

### **2. Funcionalidade**
- **Cobertura completa do PJL**
- **Comandos essenciais adicionados**
- **Funcionalidades organizadas**

### **3. Manutenibilidade**
- **Código organizado**
- **Categorias claras**
- **Fácil expansão**

---

**PrinterReaper v2.0** - Foco exclusivo em PJL com comandos reorganizados e melhorados.

*Para mais informações, visit: https://github.com/mrhenrike/PrinterReaper*
