-- Script para criar as tabelas no Supabase
-- Cole isso no SQL Editor do Supabase (https://supabase.com/dashboard)

-- Tabela de chamados
CREATE TABLE IF NOT EXISTS chamados (
    id SERIAL PRIMARY KEY,
    codigo_os VARCHAR(20) UNIQUE NOT NULL,
    cliente VARCHAR(200) NOT NULL,
    empresa VARCHAR(200) NOT NULL,
    whatsapp VARCHAR(50) NOT NULL,
    descricao TEXT NOT NULL,
    marca VARCHAR(100) DEFAULT 'Não informado',
    modelo VARCHAR(100) DEFAULT 'Não informado',
    urgencia VARCHAR(20) DEFAULT 'Média',
    status VARCHAR(50) DEFAULT 'Aberto',
    tecnico_responsavel VARCHAR(50) DEFAULT 'Nenhum',
    categoria VARCHAR(50) DEFAULT 'Outros',
    endereco VARCHAR(300) DEFAULT '',
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status);
CREATE INDEX IF NOT EXISTS idx_chamados_codigo_os ON chamados(codigo_os);
CREATE INDEX IF NOT EXISTS idx_chamados_data ON chamados(data_abertura DESC);

-- Tabela de logs
CREATE TABLE IF NOT EXISTS logs (
    id SERIAL PRIMARY KEY,
    acao VARCHAR(50) NOT NULL,
    detalhes TEXT DEFAULT '',
    chamado_id INTEGER DEFAULT NULL,
    usuario VARCHAR(50) DEFAULT 'sistema',
    ip VARCHAR(50) DEFAULT '',
    data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome_empresa VARCHAR(200) NOT NULL UNIQUE,
    nome_gestor VARCHAR(200) NOT NULL DEFAULT '',
    whatsapp VARCHAR(50) NOT NULL DEFAULT '',
    endereco VARCHAR(300) NOT NULL DEFAULT '',
    cnpj_cpf VARCHAR(50) NOT NULL DEFAULT '',
    observacoes TEXT DEFAULT '',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_clientes_empresa ON clientes(nome_empresa);

-- Tabela de agenda (tarefas/compromissos)
CREATE TABLE IF NOT EXISTS agenda (
    id SERIAL PRIMARY KEY,
    data_agenda DATE NOT NULL,
    chamado_id INTEGER DEFAULT NULL REFERENCES chamados(id) ON DELETE SET NULL,
    titulo VARCHAR(200) NOT NULL DEFAULT '',
    descricao TEXT DEFAULT '',
    tecnico VARCHAR(50) NOT NULL DEFAULT '',
    cor VARCHAR(20) DEFAULT '#3b82f6',
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_agenda);
CREATE INDEX IF NOT EXISTS idx_agenda_tecnico ON agenda(tecnico);
CREATE INDEX IF NOT EXISTS idx_agenda_chamado ON agenda(chamado_id);