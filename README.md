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

