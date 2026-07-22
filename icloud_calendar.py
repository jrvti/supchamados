"""
Módulo de integração com iCloud Calendar
"""
import os
from datetime import datetime, timedelta

try:
    from pyicloud import PyiCloudService
    ICONECTADO = True
except ImportError:
    ICONECTADO = False

ICLOUD_USER = os.environ.get('ICLOUD_USER', '')
ICLOUD_PASSWORD = os.environ.get('ICLOUD_PASSWORD', '')
CALENDARIO_NOME = os.environ.get('ICLOUD_CALENDAR', 'JRV-TI Chamados')


def iCloud_disponivel():
    """Verifica se a integração com iCloud está configurada"""
    if not ICONECTADO:
        print("⚠️ pyicloud nao instalado. iCloud indisponível.")
        return False
    if not ICLOUD_USER or not ICLOUD_PASSWORD:
        print("⚠️ ICLOUD_USER/PASSWORD nao configurados.")
        return False
    print(f"🔍 iCloud: Configurado para usuário {ICLOUD_USER}")
    print(f"🔍 iCloud: Senha (primeiros 4 chars): {ICLOUD_PASSWORD[:4]}...")
    return True


def criar_evento_icloud(titulo, data_inicio, descricao="", chamado_os="", tecnico="", endereco=""):
    """
    Cria evento no iCloud Calendar
    Retorna True se sucesso, False caso contrário
    """
    if not iCloud_disponivel():
        return False

    try:
        # Login no iCloud
        api = PyiCloudService(ICLOUD_USER, ICLOUD_PASSWORD)
        print(f"✅ Conectado ao iCloud como {ICLOUD_USER}")

        # Verifica se precisa de autenticação 2FA
        if api.requires_2fa:
            print("⚠️ iCloud requer autenticação de dois fatores (2FA)")
            print("   Tentando enviar código de verificação...")
            try:
                api.send_verification_code()
                print("✅ Código de verificação enviado!")
                print("   ⚠️ Nota: Em produção, você precisaria digitar o código")
                print("   Por enquanto, vamos tentar continuar...")
            except Exception as e:
                print(f"❌ Erro ao enviar código 2FA: {e}")
                return False

        # Procura o calendário ou cria um novo
        calendarios = api.calendar.get_calendars()
        calendario_destino = None

        for cal in calendarios:
            if cal.get('title', '').lower() == CALENDARIO_NOME.lower():
                calendario_destino = cal
                break

        # Se não encontrou, pega o calendário padrão
        if not calendario_destino:
            print(f"⚠️ Calendário '{CALENDARIO_NOME}' não encontrado. Usando padrão.")
            calendario_destino = calendarios[0] if calendarios else None

        if not calendario_destino:
            print("❌ Nenhum calendário encontrado no iCloud")
            return False

        # Converte data_inicio para datetime se for string
        if isinstance(data_inicio, str):
            try:
                data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            except:
                try:
                    data_inicio = datetime.strptime(data_inicio, "%d/%m/%Y")
                except:
                    data_inicio = datetime.now()

        # Define horário padrão (09:00) e duração (2 horas)
        data_inicio = data_inicio.replace(hour=9, minute=0, second=0, microsecond=0)
        data_fim = data_inicio + timedelta(hours=2)

        # Monta descrição detalhada
        descricao_final = descricao
        if chamado_os:
            descricao_final += f"\n\n🔗 Chamado: {chamado_os}"
        if tecnico:
            descricao_final += f"\n👨‍🔧 Técnico: {tecnico}"
        if endereco:
            descricao_final += f"\n📍 Endereço: {endereco}"

        # Cria o evento
        evento = api.calendar.create_event(
            calendario_destino,
            title=titulo,
            description=descricao_final,
            start_date=data_inicio,
            end_date=data_fim
        )

        if evento:
            print(f"✅ Evento '{titulo}' criado no iCloud Calendar!")
            return True
        else:
            print("❌ Falha ao criar evento no iCloud")
            return False

    except Exception as e:
        print(f"❌ Erro ao criar evento no iCloud: {e}")
        if "InvalidPassword" in str(e):
            print("   ⚠️ Senha inválida. Use uma senha específica para app da Apple:")
            print("   https://appleid.apple.com/account/manual")
        elif "Authentication" in str(e):
            print("   ⚠️ Problema de autenticação. Verifique suas credenciais.")
        return False


def criar_evento_da_agenda(dados_evento, chamado_info=None):
    """
    Cria evento no iCloud a partir dos dados da agenda do sistema
    """
    print(f"🔍 iCloud: Tentando criar evento - {dados_evento.get('titulo')}")
    if not iCloud_disponivel():
        print("❌ iCloud: Não disponível (credenciais não configuradas)")
        return False

    titulo = dados_evento.get('titulo', 'Tarefa JRV-TI')
    data = dados_evento.get('data_agenda', '')
    descricao = dados_evento.get('descricao', '')
    tecnico = dados_evento.get('tecnico', '')

    chamado_os = ""
    endereco = ""

    if chamado_info:
        chamado_os = chamado_info.get('codigo_os', '')
        endereco = chamado_info.get('endereco', '')

    nomes_tecnicos = {
        'tecnicon1': 'N1 - Maciel',
        'tecnicon2': 'N2 - Adams',
        'tecsenior': 'N3 - Jaime'
    }
    nome_tecnico = nomes_tecnicos.get(tecnico, tecnico)

    return criar_evento_icloud(
        titulo=titulo,
        data_inicio=data,
        descricao=descricao,
        chamado_os=chamado_os,
        tecnico=nome_tecnico,
        endereco=endereco
    )