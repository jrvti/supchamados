
"""
Módulo de integração com iCloud Calendar via CalDAV
"""
import os
from datetime import datetime, timedelta

try:
    import caldav
    from caldav.elements import dav, cdav
    CALDAV_DISPONIVEL = True
except ImportError:
    CALDAV_DISPONIVEL = False

ICLOUD_USER = os.environ.get('ICLOUD_USER', '')
ICLOUD_PASSWORD = os.environ.get('ICLOUD_PASSWORD', '')
ICLOUD_CALENDAR = os.environ.get('ICLOUD_CALENDAR', 'JRV-TI Chamados')
CALDAV_URL = os.environ.get('CALDAV_URL', 'https://caldav.icloud.com')

# Mapeamento de técnicos para calendários
CALENDARIOS_POR_TECNICO = {
    'tecnicon1': 'Auxiliares JRV',      # Maciel
    'tecnicon2': 'Técnico Adams',       # Adams
    'tecsenior': 'Técnico Adams',       # Jaime (mesmo calendário do Adams)
}


def caldav_disponivel():
    """Verifica se a integração com CalDAV está configurada"""
    if not CALDAV_DISPONIVEL:
        print("⚠️ caldav nao instalado. CalDAV indisponível.")
        return False
    if not ICLOUD_USER or not ICLOUD_PASSWORD:
        print("⚠️ ICLOUD_USER/PASSWORD nao configurados.")
        return False
    return True


def criar_evento_caldav(titulo, data_inicio, descricao="", chamado_os="", tecnico="", endereco="", nome_calendario=None, repetir=False):
    """
    Cria evento no iCloud Calendar via CalDAV
    Retorna True se sucesso, False caso contrário
    """
    if not caldav_disponivel():
        return False

    try:
        print(f"🔍 CalDAV: Conectando ao iCloud como {ICLOUD_USER}...")
        
        # Conecta ao CalDAV do iCloud
        client = caldav.DAVClient(
            url=CALDAV_URL,
            username=ICLOUD_USER,
            password=ICLOUD_PASSWORD
        )
        
        # Busca o calendário
        principal = client.principal()
        calendars = principal.calendars()
        
        # Se não especificou calendário, usa o padrão
        if not nome_calendario:
            nome_calendario = ICLOUD_CALENDAR
        
        calendario_destino = None
        for cal in calendars:
            if nome_calendario.lower() in cal.name.lower():
                calendario_destino = cal
                break
        
        # Se não encontrou, usa o primeiro calendário
        if not calendario_destino and calendars:
            print(f"⚠️ Calendário '{nome_calendario}' não encontrado. Usando: {calendars[0].name}")
            calendario_destino = calendars[0]
        
        if not calendario_destino:
            print("❌ Nenhum calendário encontrado")
            return False
        
        print(f"✅ Calendário encontrado: {calendario_destino.name}")
        
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
        
        # Cria o evento (com ou sem recorrência)
        if nome_calendario and 'repetir' in locals() and repetir:
            # Evento recorrente (todo dia)
            evento = calendario_destino.add_event(
                summary=titulo,
                description=descricao_final,
                dtstart=data_inicio,
                dtend=data_fim,
                rrule={'freq': 'daily'}
            )
            print(f"✅ Evento recorrente criado (repetição diária)")
        else:
            # Evento único
            evento = calendario_destino.add_event(
                summary=titulo,
                description=descricao_final,
                dtstart=data_inicio,
                dtend=data_fim
            )
        
        if evento:
            print(f"✅ Evento '{titulo}' criado no iCloud Calendar!")
            return True
        else:
            print("❌ Falha ao criar evento")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao criar evento no CalDAV: {e}")
        return False


def criar_evento_da_agenda(dados_evento, chamado_info=None):
    """
    Cria evento no iCloud a partir dos dados da agenda do sistema
    """
    print(f"🔍 CalDAV: Tentando criar evento - {dados_evento.get('titulo')}")
    
    if not caldav_disponivel():
        print("❌ CalDAV: Não disponível (credenciais não configuradas)")
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
    
    # Busca o calendário correto para este técnico
    nome_calendario = CALENDARIOS_POR_TECNICO.get(tecnico, ICLOUD_CALENDAR)
    
    # Verifica se deve repetir
    repetir = dados_evento.get('repetir', False)
    
    return criar_evento_caldav(
        titulo=titulo,
        data_inicio=data,
        descricao=descricao,
        chamado_os=chamado_os,
        tecnico=nome_tecnico,
        endereco=endereco,
        nome_calendario=nome_calendario,
        repetir=repetir
    )
