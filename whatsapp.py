"""
Módulo de integração com WhatsApp via Evolution API
"""
import requests
import os

EVOLUTION_API_URL = os.environ.get('EVOLUTION_API_URL', 'https://attention-shininess-radiated.ngrok-free.dev')
EVOLUTION_API_KEY = os.environ.get('EVOLUTION_API_KEY', 'F6696D693168-4A2A-B814-F0570E881714')
EVOLUTION_INSTANCE = os.environ.get('EVOLUTION_INSTANCE', 'Baileys')


def enviar_whatsapp(numero_telefone, mensagem):
    """
    Envia mensagem WhatsApp via Evolution API
    numero_telefone: formato internacional sem + (ex: 5511999999999)
    """
    if not EVOLUTION_API_URL or not EVOLUTION_API_KEY:
        print(f"⚠️ WhatsApp não configurado. Mensagem para {numero_telefone}: {mensagem}")
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
        if resp.ok:
            print(f"✅ WhatsApp enviado para {numero_telefone}")
            return True
        else:
            print(f"⚠️ Erro ao enviar WhatsApp: {resp.status_code} - {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Erro ao enviar WhatsApp: {e}")
        return False


def notificar_novo_chamado_tecnico(codigo_os, cliente, empresa, categoria, tecnico_telefone):
    """Notifica técnico sobre novo chamado atribuído"""
    if not tecnico_telefone:
        return False
    
    mensagem = f"""🔔 *NOVO CHAMADO ATRIBUÍDO*

📋 O.S.: {codigo_os}
👤 Cliente: {cliente}
🏢 Empresa: {empresa}
📂 Categoria: {categoria}

Acesse o sistema para mais detalhes."""

    return enviar_whatsapp(tecnico_telefone, mensagem)


def notificar_nova_tarefa_agenda(data, titulo, tecnico_telefone, chamado_codigo=None):
    """Notifica técnico sobre nova tarefa na agenda"""
    if not tecnico_telefone:
        return False
    
    mensagem = f"""📅 *NOVA TAREFA NA AGENDA*

📅 Data: {data}
📌 Tarefa: {titulo}"""
    
    if chamado_codigo:
        mensagem += f"\n🔗 Chamado: {chamado_codigo}"
    
    mensagem += "\n\nAcesse o sistema para mais detalhes."""

    return enviar_whatsapp(tecnico_telefone, mensagem)


def notificar_chamado_finalizado(codigo_os, cliente, telefone_cliente):
    """Notifica cliente que o chamado foi finalizado"""
    if not telefone_cliente:
        return False
    
    mensagem = f"""✅ *CHAMADO FINALIZADO*

📋 O.S.: {codigo_os}
👤 Cliente: {cliente}

Seu chamado foi finalizado. Acesse o sistema para baixar o RAT."""

    return enviar_whatsapp(telefone_cliente, mensagem)