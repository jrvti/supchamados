# 🖥️ JRV-TI — Sistema de Chamados Técnicos

> **Sistema web completo para abertura, gestão e acompanhamento de chamados de suporte técnico em TI, monitoramento e segurança eletrônica.**  
> Ideal para empresas prestadoras de serviços técnicos que precisam organizar ordens de serviço, controlar visitas técnicas e gerar relatórios profissionais em PDF.

---

## 📋 Sobre o Sistema

O **JRV-TI** é um sistema desenvolvido para **substituir planilhas, cadernos e papéis** na gestão de chamados técnicos. Ele permite que clientes abram chamados diretamente pelo site e que os técnicos acompanhem, atualizem e finalizem as ordens de serviço de forma centralizada.

### 🎯 Para quem é esse sistema?

- **Técnicos de informática** autônomos ou de empresas
- **Prestadores de serviço** em CFTV, alarmes e segurança eletrônica
- **Suporte de TI** para condomínios, empresas e clientes corporativos
- **Micro e pequenas empresas** que querem profissionalizar o atendimento

### ✨ Principais Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 📝 **Abertura de Chamado** | Cliente preenche formulário simples e recebe um código de OS |
| 🔐 **Painel Admin** | Técnicos fazem login e gerenciam todos os chamados |
| 🔍 **Busca e Filtros** | Pesquise chamados por código, cliente, empresa ou urgência |
| 🚦 **Controle de Urgência** | Defina prioridades: Baixa, Média, Alta ou Crítica |
| 👥 **Gestão de Técnicos** | Atribua chamados a N1 (Maciel), N2 (Adams) ou N3 (Jaime) |
| 📄 **RAT em PDF** | Preencha o Relatório de Atendimento Técnico com arrastar e soltar campos no PDF |
| 📊 **Dashboard** | Métricas: chamados ativos, finalizados, urgências críticas e ranking de técnicos |
| 📁 **Histórico** | Chamados finalizados ficam arquivados com RAT disponível para download |
| 🌗 **Tema Escuro/Claro** | Alternância em todas as páginas do sistema |
| 💾 **Armazenamento em Nuvem** | Dados no PostgreSQL + PDFs no Storage (via Supabase) |

### 🏗️ Tecnologias Utilizadas

- **Backend:** Python + Flask
- **Banco de Dados:** PostgreSQL (Supabase)
- **Armazenamento de PDFs:** Supabase Storage (1GB grátis)
- **Hospedagem:** Render
- **Frontend:** HTML, CSS, JavaScript (tema claro/escuro nativo)
- **PDF:** pdf-lib.js (preenchimento dinâmico no navegador)

### 🔧 Como Usar

**Para clientes:** Acesse o site e preencha o formulário com seus dados e descrição do problema. Você receberá um código de OS para acompanhamento.

**Para técnicos:** Faça login no painel administrativo para visualizar, atender e gerenciar chamados. Utilize o RAT para gerar relatórios profissionais em PDF ao finalizar cada atendimento.

## 🚀 Deploy com Supabase + Render

### 1. Criar Conta no Supabase (Grátis)

1. Acesse https://supabase.com e clique em "Start your project"
2. Faça login com GitHub
3. Crie uma nova organização (pode ser pessoal)
4. Clique em "New project"
5. Preencha:
   - **Name:** `jrvti-chamados`
   - **Database Password:** Crie uma senha forte e **guarde-a**
   - **Region:** South America (São Paulo) - para menor latência
6. Aguarde a criação do projeto (~2 minutos)

### 2. Configurar o Banco de Dados

1. No painel do Supabase, vá em **SQL Editor** (ícone de documento no menu lateral)
2. Clique em **New Query**
3. Copie e cole o conteúdo do arquivo `init_db.sql`
4. Clique em **Run** para criar a tabela `chamados`

### 3. Obter Credenciais do Supabase

1. Vá em **Project Settings** (⚙️ ícone de engrenagem no menu inferior)
2. Clique em **Database**
3. Anote a **Connection string** (URL do banco):
   ```
   postgresql://postgres:XXXXXXXX@db.XXXXXXXXX.supabase.co:5432/postgres
   ```
4. Substitua `[YOUR-PASSWORD]` pela senha que você criou no passo 1.5

5. Vá em **Project Settings > API**
6. Anote:
   - **Project URL** → será seu `SUPABASE_URL`
   - **anon public key** → será seu `SUPABASE_KEY`

### 4. Fazer Deploy no Render

1. Acesse https://render.com e faça login com GitHub
2. Clique em **New +** > **Web Service**
3. Conecte seu repositório do GitHub (ou faça upload manual)
4. Configure:
   - **Name:** `jrvti-chamados`
   - **Environment:** `Python`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

5. Em **Environment Variables**, adicione:

| Variável | Valor |
|---|---|
| `SUPABASE_URL` | https://XXXXXXXX.supabase.co (seu Project URL) |
| `SUPABASE_KEY` | eyJhbGciOiJIUzI1NiIsInR5cCI6Ik... (sua anon key) |
| `DATABASE_URL` | postgresql://postgres:senha@db.XXXXXXXX.supabase.co:5432/postgres |

6. Escolha o plano **Free** (grátis)
7. Clique em **Create Web Service**

### 5. Acessar o Sistema

- Após o deploy, o Render dará uma URL tipo: `https://jrvti-chamados.onrender.com`
- Acesse para testar!

**Login dos técnicos:**
| Usuário | Senha |
|---|---|
| `tecnicon1` | `S@cCham@d##s2005` |
| `tecnicon2` | `S@cCham@d##s2005` |
| `tecsenior` | `S@cCham@d##s2005` |

### 6. Gerenciar os Dados

Acesse https://supabase.com/dashboard > seu projeto > **Table Editor**

Lá você pode:
- 👁️ Ver todos os chamados
- ✏️ Editar dados diretamente
- 🗑️ Excluir chamados antigos
- 📤 Exportar dados para CSV
- 📦 Gerenciar os PDFs em **Storage** > **rats**

### 7. Limites Grátis

| Recurso | Limite Free |
|---|---|
| PostgreSQL | 500 MB |
| Storage (PDFs) | 1 GB |
| Site no Render | 750h/mês (dorme após 15min inativo) |

## 🔧 Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
set SUPABASE_URL=sua_url
set SUPABASE_KEY=sua_key
set DATABASE_URL=sua_connection_string

# Rodar
python app.py
```

## 📁 Estrutura do Projeto

```
jrvti_chamados/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── init_db.sql            # Script SQL para criar tabelas
├── modelo_rat.pdf         # Modelo de PDF para RAT
└── templates/
    ├── admin.html         # Painel administrativo
    ├── arquivados.html    # Chamados finalizados
    ├── cliente.html       # Formulário de abertura
    ├── dashboard.html     # Dashboard com métricas
    ├── detalhes.html      # Detalhes do chamado
    ├── login.html         # Login dos técnicos
    ├── rat.html           # Preenchimento de RAT
    └── sucesso.html       # Confirmação de abertura
```

## 📸 Funcionalidades

- ✅ Abertura de chamados pelo cliente
- ✅ Painel administrativo com busca
- ✅ Gestão de urgência, status e técnico responsável
- ✅ Geração de RAT em PDF com preenchimento visual
- ✅ Dashboard com métricas e rankings
- ✅ Histórico de chamados finalizados
- ✅ Upload e download de PDFs via Supabase Storage
- ✅ Tema claro/escuro em todas as páginas
- ✅ Banco PostgreSQL gerenciável via Supabase

