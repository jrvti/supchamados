"""
Módulo de integração com WhatsApp via Evolution API
"""
import requests
import os
from datetime import datetime

EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL', 'https://attention-shininess-radiated.ngrok-free.dev')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'F6696D693168-4A2A-B814-F0570E881714')
EVOLUTION_INSTANCE = os.environ.get('EVOLUTION_INSTANCE', 'Baileys')

# Nome do técnico Maciel para notificar de todos os chamados novos
TECNICO_MACIEL_TELEFONE = '5511961473785'


def formatar_data_agora():
    """Retorna data/hora formatada"""
    agora = datetime.now()
    return agora.strftime("%d/%m/%Y às %H:%M")


def obter_nome_tecnico(usuario):
    """Retorna o nome legível do técnico"""
    nomes = {
        'tecnicon1': 'N1 - Maciel',
        'tecnicon2': 'N2 - Adams',
        'tecsenior': 'N3 - Jaime'
    }
    return nomes.get(usuario, usuario)


def enviar_whatsapp(numero_telefone, mensagem):
    """
    Envia mensagem WhatsApp via Evolution API
    numero_telefone: formato internacional sem + (ex: 5511999999999)
    """
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY:
        print(f"⚠️ WhatsApp não configurado. Mensagem para {numero_telefone}: {mensagem[:100]}...")
        return False

    try:
        url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
        headers = {
            "apikey": EVOLUTION_API_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "number": numero_telefone,
            "text": mensagem,
            "delay": 0
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=10)
        if resp.ok or resp.status_code == 201:
            print(f"✅ WhatsApp enviado para {numero_telefone}")
            return True
        else:
            print(f"⚠️ Erro ao enviar WhatsApp: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar WhatsApp: {e}")
        return False


def notificar_novo_chamado_em_aberto(codigo_os, cliente, empresa, descricao, categoria):
    """Notifica Maciel sobre TODO novo chamado criado (independente de técnico)"""
    agora = formatar_data_agora()

    mensagem = f"""🔔 *NOVO CHAMADO RECEBIDO*

📋 *O.S.:* {codigo_os}
👤 *Cliente:* {cliente}
🏢 *Empresa:* {empresa}
📂 *Categoria:* {categoria}
🕐 *Registrado em:* {agora}

📝 *Descrição:*
{descricao[:200]}{'...' if len(descricao) > 200 else ''}

⚡ Aguardando atribuição de técnico."""

    return enviar_whatsapp(TECNICO_MACIEL_TELEFONE, mensagem)


def notificar_chamado_atribuido(codigo_os, cliente, empresa, descricao, categoria,
                                tecnico_usuario, tecnico_telefone, urgencia):
    """Notifica técnico quando um chamado é atribuído a ele"""
    agora = formatar_data_agora()
    nome_tecnico = obter_nome_tecnico(tecnico_usuario)

    mensagem = f"""🔔 *CHAMADO ATRIBUÍDO A VOCÊ*

📋 *O.S.:* {codigo_os}
👤 *Cliente:* {cliente}
🏢 *Empresa:* {empresa}
📂 *Categoria:* {categoria}
🚦 *Urgência:* {urgencia}
🕐 *Atribuído em:* {agora}
👨‍🔧 *Técnico:* {nome_tecnico}

📝 *Descrição do Problema:*
{descricao[:250]}{'...' if len(descricao) > 250 else ''}

✅ Acesse o sistema para mais detalhes e para preencher o RAT."""

    return enviar_whatsapp(tecnico_telefone, mensagem)


def notificar_nova_tarefa_agenda(data_agenda, titulo, tecnico_telefone,
                                  chamado_codigo=None, chamado_cliente=None,
                                  tecnico_usuario=None, descricao=None):
    """Notifica técnico sobre nova tarefa na agenda"""
    agora = formatar_data_agora()
    nome_tecnico = obter_nome_tecnico(tecnico_usuario) if tecnico_usuario else "Técnico"

    mensagem = f"""📅 *NOVA TAREFA NA AGENDA*

📅 *Data:* {data_agenda}
📌 *Tarefa:* {titulo}
👨‍🔧 *Responsável:* {nome_tecnico}
🕐 *Criada em:* {agora}"""

    if chamado_codigo:
        mensagem += f"""
🔗 *Chamado Vinculado:* {chamado_codigo}"""
        if chamado_cliente:
            mensagem += f"""
👤 *Cliente:* {chamado_cliente}"""

    if descricao:
        mensagem += f"""

📝 *Observações:*
{descricao[:200]}{'...' if len(descricao) > 200 else ''}"""

    mensagem += """

✅ Acesse o sistema para gerenciar suas tarefas."""

    return enviar_whatsapp(tecnico_telefone, mensagem)


def notificar_chamado_finalizado(codigo_os, cliente, empresa, tecnico_nome):
    """Notifica Maciel que um chamado foi finalizado"""
    agora = formatar_data_agora()

    mensagem = f"""✅ *CHAMADO FINALIZADO*

📋 *O.S.:* {codigo_os}
👤 *Cliente:* {cliente}
🏢 *Empresa:* {empresa}
👨‍🔧 *Finalizado por:* {tecnico_nome}
🕐 *Finalizado em:* {agora}

📁 Chamado arquivado no sistema."""

    return enviar_whatsapp(TECNICO_MACIEL_TELEFONE, mensagem)