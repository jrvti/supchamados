# JRV-TI - Sistema de Chamados Técnicos

Sistema web para abertura e gestão de chamados técnicos, com geração de RAT (Relatório de Atendimento Técnico) em PDF.

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

