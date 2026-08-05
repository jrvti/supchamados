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
    repetir BOOLEAN DEFAULT FALSE,
    evento_icloud_uid VARCHAR(500) DEFAULT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agenda_data ON agenda(data_agenda);
CREATE INDEX IF NOT EXISTS idx_agenda_tecnico ON agenda(tecnico);
CREATE INDEX IF NOT EXISTS idx_agenda_chamado ON agenda(chamado_id);

-- Tabela de financeiro
CREATE TABLE IF NOT EXISTS financeiro (
    id SERIAL PRIMARY KEY,
    chamado_id INTEGER NOT NULL REFERENCES chamados(id) ON DELETE CASCADE,
    valor DECIMAL(10,2) DEFAULT 0,
    status_pagamento VARCHAR(50) DEFAULT 'Pendente',
    observacoes TEXT DEFAULT '',
    data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_pagamento TIMESTAMP DEFAULT NULL,
    usuario_criacao VARCHAR(50) DEFAULT 'sistema',
    usuario_pagamento VARCHAR(50) DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_financeiro_chamado ON financeiro(chamado_id);
CREATE INDEX IF NOT EXISTS idx_financeiro_status ON financeiro(status_pagamento);

-- Tabela de usuários do sistema
CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    senha VARCHAR(255) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    nivel VARCHAR(50) DEFAULT 'tecnico',
    ativo BOOLEAN DEFAULT TRUE,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_usuarios_username ON usuarios(username);

-- Inserir usuários iniciais
INSERT INTO usuarios (username, senha, nome, nivel, ativo) VALUES
('tecsenior', 'S@cCham@d##s2005', 'N3 - Jaime', 'admin', TRUE),
('tecnicon2', 'S@cCham@d##s2005', 'N2 - Adams', 'tecnico', TRUE),
('tecnicon1', 'S@cCham@d##s2005', 'N1 - Maciel', 'tecnico', TRUE)
ON CONFLICT (username) DO NOTHING;
