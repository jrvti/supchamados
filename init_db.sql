-- Script para criar a tabela no Supabase
-- Cole isso no SQL Editor do Supabase (https://supabase.com/dashboard)

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
    data_abertura TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_chamados_status ON chamados(status);
CREATE INDEX IF NOT EXISTS idx_chamados_codigo_os ON chamados(codigo_os);
CREATE INDEX IF NOT EXISTS idx_chamados_data ON chamados(data_abertura DESC);

