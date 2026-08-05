import os
import random
import string
import io

import requests
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify
from whatsapp import (
    notificar_novo_chamado_em_aberto,
    notificar_chamado_atribuido,
    notificar_nova_tarefa_agenda,
    notificar_chamado_finalizado,
    obter_nome_tecnico
)
from caldav_calendar import criar_evento_da_agenda

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

# === CONFIGURAÇÃO SUPABASE ===
SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', '')
SUPABASE_URL = SUPABASE_URL.rstrip('/')


def api_headers(use_service_role=False):
    key = SUPABASE_SERVICE_KEY if use_service_role else SUPABASE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation"
    }


def api_get(table, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code >= 400:
        print(f"⚠️  GET {table} erro {resp.status_code}: {resp.text[:200]}")
    return resp.json() if resp.ok else []


def api_post(table, data):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code >= 400:
        print(f"⚠️  POST {table} erro {resp.status_code}: {resp.text[:200]}")
    return resp.json() if resp.ok else []


def api_patch(table, data, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.patch(url, headers=headers, params=filters, json=data)
    if resp.status_code >= 400:
        print(f"⚠️  PATCH {table} erro {resp.status_code}: {resp.text[:200]}")
    return resp.ok


def api_delete(table, filters):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.delete(url, headers=headers, params=filters)
    if resp.status_code >= 400:
        print(f"⚠️  DELETE {table} erro {resp.status_code}: {resp.text[:200]}")
    return resp.ok


def registrar_log(acao, detalhes="", chamado_id=None):
    """Registra log de auditoria"""
    try:
        dados = {
            "acao": acao,
            "detalhes": detalhes,
            "chamado_id": chamado_id,
            "usuario": session.get('usuario', 'sistema'),
            "ip": request.remote_addr or ''
        }
        api_post("logs", dados)
    except:
        pass


def init_db():
    """Verifica se as tabelas existem"""
    try:
        dados = api_get("chamados", params={"limit": 1})
        if isinstance(dados, list):
            print("✅ Tabela 'chamados' acessível!")
    except:
        pass
    try:
        dados_log = api_get("logs", params={"limit": 1})
        if isinstance(dados_log, list):
            print("✅ Tabela 'logs' acessível!")
    except:
        pass


def supabase_storage_upload(nome_arquivo, conteudo_bytes, pasta="rats"):
    """Faz upload para o Storage do Supabase"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    try:
        headers_auth = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        resp_buckets = requests.get(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers_auth)
        buckets = resp_buckets.json() if resp_buckets.ok else []
        if not any(b.get('name') == pasta for b in buckets):
            requests.post(f"{SUPABASE_URL}/storage/v1/bucket", headers=headers_auth,
                         json={"name": pasta, "public": True})
    except:
        pass
    # Tenta upload com multipart/form-data primeiro
    url = f"{SUPABASE_URL}/storage/v1/object/{pasta}/{nome_arquivo}"
    headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    files = {'file': (nome_arquivo, conteudo_bytes, 'application/pdf')}
    resp = requests.post(url, headers=headers, files=files)
    if resp.ok:
        print(f"✅ Upload {nome_arquivo} para {pasta} OK")
        return True
    # Fallback: upload como octet-stream
    headers["Content-Type"] = "application/octet-stream"
    resp2 = requests.post(url, headers=headers, data=conteudo_bytes)
    if resp2.ok:
        print(f"✅ Upload (fallback) {nome_arquivo} para {pasta} OK")
    else:
        print(f"⚠️ Upload {nome_arquivo} falhou: {resp2.status_code} {resp2.text[:100]}")
    return resp2.ok


def supabase_storage_download(nome_arquivo, pasta="rats"):
    """Baixa arquivo do Storage - tenta autenticado primeiro, depois público"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("⚠️ SUPABASE_URL/SERVICE_KEY nao configurados para download")
        return None
    headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    
    # Tenta com URL autenticada (mais confiável com RLS)
    url_auth = f"{SUPABASE_URL}/storage/v1/object/{pasta}/{nome_arquivo}"
    resp_auth = requests.get(url_auth, headers=headers)
    if resp_auth.ok:
        return resp_auth.content
    
    # Fallback: tenta URL pública
    url_public = f"{SUPABASE_URL}/storage/v1/object/public/{pasta}/{nome_arquivo}"
    resp_public = requests.get(url_public, headers=headers)
    if resp_public.ok:
        return resp_public.content
    
    print(f"⚠️ Download {nome_arquivo} de {pasta} falhou. Auth:{resp_auth.status_code} Public:{resp_public.status_code}")
    # Log do erro para diagnóstico
    if resp_auth.status_code == 404 or resp_public.status_code == 404:
        print(f"   → Arquivo '${nome_arquivo}' nao encontrado no bucket '${pasta}'")
    elif resp_auth.status_code == 403 or resp_public.status_code == 403:
        print(f"   → Permissao negada. Verifique as politicas RLS do bucket '${pasta}' no Supabase")
    elif resp_auth.status_code == 400 or resp_public.status_code == 400:
        print(f"   → Erro 400. Pode ser nome de arquivo invalido ou bucket nao existe")
    return None


def supabase_storage_list(pasta="rats"):
    """Lista arquivos no Storage do Supabase"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        print("⚠️ SUPABASE_URL/SERVICE_KEY nao configurados")
        return []
    try:
        url = f"{SUPABASE_URL}/storage/v1/object/list/{pasta}"
        headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}", "Content-Type": "application/json"}
        body = {"limit": 100, "offset": 0, "prefix": "", "sortBy": {"column": "name", "order": "asc"}}
        resp = requests.post(url, headers=headers, json=body)
        if resp.ok:
            return resp.json()
        else:
            print(f"⚠️ STORAGE LIST {pasta} erro {resp.status_code}: {resp.text[:200]}")
            return []
    except Exception as e:
        print(f"⚠️ STORAGE LIST {pasta} exception: {e}")
        return []


def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    return f"OS-{''.join(random.choice(caracteres) for _ in range(6))}"


# Dicionário de telefones dos técnicos (formato internacional sem +)
TELEFONES_TECNICOS = {
    'tecnicon1': '5511961473785',  # N1 - Maciel
    'tecnicon2': '5511997799379',  # N2 - Adams
    'tecsenior': '5511993447737'   # N3 - Jaime
}


def obter_telefone_tecnico(usuario_tecnico):
    """Retorna o telefone do técnico baseado no username"""
    return TELEFONES_TECNICOS.get(usuario_tecnico, '')


# ==================== ROTAS ====================

@app.route('/')
def index():
    return render_template('cliente.html')


@app.route('/chamado_tecnico')
def chamado_tecnico():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('chamado_tecnico.html')


@app.route('/enviar_chamado', methods=['POST'])
def enviar_chamado():
    cliente = request.form.get('cliente')
    empresa = request.form.get('empresa')
    whatsapp = request.form.get('whatsapp')
    endereco = request.form.get('endereco', '')
    marca = request.form.get('marca', 'Não informado')
    modelo = request.form.get('modelo', 'Não informado')
    categoria = request.form.get('categoria', 'Outros')
    descricao = request.form.get('descricao')
    descricao_final = f"Equipamento: {marca} / {modelo} | Problema: {descricao}"
    codigo_gerado = gerar_codigo_os()

    dados_chamado = {
        "codigo_os": codigo_gerado,
        "cliente": cliente,
        "empresa": empresa,
        "whatsapp": whatsapp,
        "endereco": endereco,
        "descricao": descricao_final,
        "marca": marca,
        "modelo": modelo,
        "categoria": categoria,
        "urgencia": "Média",
        "status": "Aberto",
        "tecnico_responsavel": "Nenhum"
    }

    try:
        resultado = api_post("chamados", dados_chamado)
        print(f"✅ Chamado criado: {codigo_gerado} - Resultado: {resultado}")
    except Exception as e:
        print(f"❌ Erro ao criar chamado: {e}")
        return f"Erro ao criar chamado: {e}", 500

    # Upload fotos se houver
    if 'fotos' in request.files:
        fotos = request.files.getlist('fotos')
        for i, foto in enumerate(fotos):
            if foto.filename:
                ext = foto.filename.rsplit('.', 1)[-1].lower() if '.' in foto.filename else 'jpg'
                nome_foto = f"chamado_{codigo_gerado}_{i}.{ext}"
                try:
                    supabase_storage_upload(nome_foto, foto.read(), "chamados_fotos")
                except Exception as e:
                    print(f"Erro upload foto: {e}")

    # Notifica Maciel sobre TODO chamado novo
    notificar_novo_chamado_em_aberto(
        codigo_gerado, cliente, empresa, descricao_final, categoria
    )

    # Notifica técnico específico se o chamado já foi atribuído (raro, mas possível)
    if dados_chamado.get('tecnico_responsavel') and dados_chamado['tecnico_responsavel'] != 'Nenhum':
        telefone_tecnico = obter_telefone_tecnico(dados_chamado['tecnico_responsavel'])
        if telefone_tecnico:
            notificar_chamado_atribuido(
                codigo_gerado, cliente, empresa, descricao_final, categoria,
                dados_chamado['tecnico_responsavel'], telefone_tecnico, "Média"
            )

    # Se for técnico logado, redireciona para admin. Se for cliente público, mostra página de sucesso
    if session.get('logado'):
        return redirect(url_for('admin'))
    else:
        return render_template('sucesso.html', codigo_os=codigo_gerado)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        senha = request.form.get('senha')
        if usuario in ['tecsenior', 'tecnicon2', 'tecnicon1'] and senha == 'S@cCham@d##s2005':
            session['logado'] = True
            session['usuario'] = usuario
            registrar_log("login", f"Usuário {usuario} logou")
            return redirect(url_for('admin'))
        return render_template('login.html', erro="Credenciais incorretas.")
    return render_template('login.html', erro=None)


@app.route('/logout')
def logout():
    registrar_log("logout", f"Usuário {session.get('usuario')} saiu")
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        chamado_id = request.form.get('id')
        novo_status = request.form.get('status')
        novo_tecnico = request.form.get('tecnico_responsavel')
        nova_urgencia = request.form.get('urgencia')

        dados_atuais = api_get("chamados", {"id": f"eq.{chamado_id}", "limit": "1"})
        if dados_atuais:
            chamado_atual = dados_atuais[0]
            mudancas = []
            if novo_status and novo_status != chamado_atual.get('status'):
                mudancas.append(f"status {chamado_atual.get('status')}→{novo_status}")
            if novo_tecnico and novo_tecnico != chamado_atual.get('tecnico_responsavel'):
                mudancas.append(f"técnico {chamado_atual.get('tecnico_responsavel')}→{novo_tecnico}")
            if nova_urgencia and nova_urgencia != chamado_atual.get('urgencia'):
                mudancas.append(f"urgência {chamado_atual.get('urgencia')}→{nova_urgencia}")
            if mudancas:
                registrar_log("alteracao", f"OS {chamado_atual.get('codigo_os')}: {', '.join(mudancas)}", chamado_id)

        api_patch("chamados", {
            "status": novo_status,
            "tecnico_responsavel": novo_tecnico,
            "urgencia": nova_urgencia
        }, {"id": f"eq.{chamado_id}"})
        
        # Notifica técnico se foi atribuído a um chamado
        if novo_tecnico and novo_tecnico != 'Nenhum' and novo_tecnico != chamado_atual.get('tecnico_responsavel'):
            telefone_tecnico = obter_telefone_tecnico(novo_tecnico)
            if telefone_tecnico:
                notificar_chamado_atribuido(
                    chamado_atual.get('codigo_os', ''),
                    chamado_atual.get('cliente', ''),
                    chamado_atual.get('empresa', ''),
                    chamado_atual.get('descricao', ''),
                    chamado_atual.get('categoria', 'Outros'),
                    novo_tecnico,
                    telefone_tecnico,
                    chamado_atual.get('urgencia', 'Média')
                )

    busca = request.args.get('busca', '')
    params = {"status": "neq.Finalizado", "order": "id.desc"}
    if busca:
        params["or"] = f"(codigo_os.ilike.*{busca}*,cliente.ilike.*{busca}*,empresa.ilike.*{busca}*,categoria.ilike.*{busca}*,descricao.ilike.*{busca}*)"

    chamados = api_get("chamados", params)
    return render_template('admin.html', chamados=chamados, tecnico_atual=session.get('usuario'), busca=busca)


@app.route('/arquivados')
def arquivados():
    if not session.get('logado'):
        return redirect(url_for('login'))

    busca = request.args.get('busca', '')
    params = {"status": "eq.Finalizado", "order": "id.desc"}
    if busca:
        params["or"] = f"(codigo_os.ilike.*{busca}*,cliente.ilike.*{busca}*,empresa.ilike.*{busca}*)"

    chamados = api_get("chamados", params)
    return render_template('arquivados.html', chamados=chamados)


@app.route('/rat_avulsa')
def rat_avulsa():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('rat.html', chamado={"id": 0, "codigo_os": gerar_codigo_os()})


@app.route('/chamado/<int:id>')
def detalhes_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))

    dados = api_get("chamados", {"id": f"eq.{id}", "limit": "1"})
    if not dados:
        return "Chamado não encontrado", 404

    chamado = dados[0]

    # Busca logs deste chamado
    logs = api_get("logs", {"chamado_id": f"eq.{id}", "order": "id.desc", "limit": "20"})

    # Busca fotos do chamado
    codigo_os = chamado.get('codigo_os', '')
    todas_fotos = supabase_storage_list("chamados_fotos") if SUPABASE_SERVICE_KEY else []
    fotos_chamado = [f for f in todas_fotos if isinstance(f, dict) and f.get('name', '').startswith(f'chamado_{codigo_os}')]

    return render_template('detalhes.html', chamado=chamado, logs=logs, fotos=fotos_chamado)


@app.route('/chamado/<int:id>/rat')
def rat_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))

    dados = api_get("chamados", {"id": f"eq.{id}", "limit": "1"})
    if not dados:
        return "Chamado não encontrado", 404
    return render_template('rat.html', chamado=dados[0])


@app.route('/chamado/<int:id>/finalizar', methods=['POST'])
def finalizar_chamado_rat(id):
    if not session.get('logado'):
        return jsonify({"erro": "Não autorizado"}), 401

    pdf_salvo = False
    if 'pdf' in request.files and SUPABASE_URL and SUPABASE_SERVICE_KEY:
        arquivo_pdf = request.files['pdf']
        pdf_bytes = arquivo_pdf.read()
        nome_arquivo = f'RAT_OS_{id}.pdf'
        try:
            pdf_salvo = supabase_storage_upload(nome_arquivo, pdf_bytes, "rats")
        except Exception as e:
            print(f"Erro ao enviar PDF: {e}")

    api_patch("chamados", {"status": "Finalizado"}, {"id": f"eq.{id}"})

    dados_chamado = api_get("chamados", {"id": f"eq.{id}", "limit": "1"})
    codigo = dados_chamado[0].get('codigo_os', '') if dados_chamado else ''
    registrar_log("finalizacao", f"OS {codigo} finalizada", id)

    msg = "Chamado arquivado com sucesso!"
    if pdf_salvo:
        msg += " RAT salva no storage."
    else:
        msg += " (PDF nao foi salvo - verifique config)"

    return jsonify({"sucesso": True, "mensagem": msg}), 200


@app.route('/baixar_rat/<int:id>')
def baixar_rat(id):
    if not session.get('logado'):
        return redirect(url_for('login'))

    nome_arquivo = f'RAT_OS_{id}.pdf'
    pdf_data = supabase_storage_download(nome_arquivo, "rats")

    if pdf_data:
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )
    return "Arquivo PDF nao encontrado no storage", 404


@app.route('/chamado/<int:id>/excluir', methods=['POST'])
def excluir_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))

    dados_chamado = api_get("chamados", {"id": f"eq.{id}", "limit": "1"})
    codigo = dados_chamado[0].get('codigo_os', '') if dados_chamado else ''
    api_delete("chamados", {"id": f"eq.{id}"})
    registrar_log("exclusao", f"OS {codigo} excluída", id)
    return redirect(url_for('admin'))


@app.route('/modelo_base_pdf')
def modelo_rat():
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelo_rat.pdf')
    if os.path.exists(caminho_arquivo):
        return send_file(caminho_arquivo, mimetype='application/pdf')
    return "Arquivo nao encontrado", 404


@app.route('/foto_chamado/<path:nome_arquivo>')
def foto_chamado(nome_arquivo):
    """Serve fotos do chamado"""
    dados = supabase_storage_download(nome_arquivo, "chamados_fotos")
    if dados:
        ext = nome_arquivo.rsplit('.', 1)[-1].lower() if '.' in nome_arquivo else 'jpeg'
        mimetype = f'image/{ext}' if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] else 'image/jpeg'
        return send_file(io.BytesIO(dados), mimetype=mimetype)
    return "Foto nao encontrada", 404


@app.route('/logs')
def visualizar_logs():
    """Página de logs de auditoria - acesso via /logs"""
    if not session.get('logado'):
        return redirect(url_for('login'))

    pagina = request.args.get('pagina', 1, type=int)
    if pagina < 1:
        pagina = 1
    offset = (pagina - 1) * 100
    logs = api_get("logs", {"order": "id.desc", "limit": "100", "offset": str(offset)})
    return render_template('logs.html', logs=logs, pagina=pagina)


@app.route('/dashboard')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))

    total_ativos = len(api_get("chamados", {"status": "neq.Finalizado", "select": "id"}))
    total_fechados = len(api_get("chamados", {"status": "eq.Finalizado", "select": "id"}))

    criticos = api_get("chamados", {
        "status": "neq.Finalizado",
        "urgencia": "in.(Alta,Crítica)",
        "select": "id"
    })
    total_criticos = len(criticos)

    # Carrega dados para ranking (agregação server-side)
    chamados_fechados = api_get("chamados", {"status": "eq.Finalizado", "select": "tecnico_responsavel"})
    from collections import Counter
    contagem_tecnicos = Counter(c.get('tecnico_responsavel', 'Nenhum') for c in chamados_fechados if c.get('tecnico_responsavel'))
    ranking_tecnicos = [{"tecnico_responsavel": k, "qtd": v} for k, v in contagem_tecnicos.most_common()]

    chamados_todos = api_get("chamados", {"select": "empresa"})
    contagem_empresas = Counter(c.get('empresa', 'N/A') for c in chamados_todos if c.get('empresa'))
    top_clientes = [{"empresa": k, "qtd": v} for k, v in contagem_empresas.most_common(3)]

    return render_template('dashboard.html',
                          total_ativos=total_ativos,
                          total_fechados=total_fechados,
                          total_criticos=total_criticos,
                          ranking_tecnicos=ranking_tecnicos,
                          top_clientes=top_clientes)


@app.route('/admin/bulk_excluir', methods=['POST'])
def bulk_excluir():
    """Excluir múltiplos chamados finalizados"""
    if not session.get('logado') or session.get('usuario') != 'tecsenior':
        return jsonify({"erro": "Apenas tecnico senior"}), 403

    data = request.get_json()
    ids = data.get('ids', [])
    if not ids:
        return jsonify({"erro": "Nenhum ID"}), 400

    for chamado_id in ids:
        dados = api_get("chamados", {"id": f"eq.{chamado_id}", "limit": "1"})
        codigo = dados[0].get('codigo_os', '') if dados else ''
        api_delete("chamados", {"id": f"eq.{chamado_id}"})
        registrar_log("exclusao_bulk", f"OS {codigo} excluída em lote", chamado_id)

    return jsonify({"sucesso": True, "mensagem": f"{len(ids)} chamado(s) excluído(s)"}), 200


# ==================== ROTAS DE CLIENTES (PERFIS) ====================

@app.route('/clientes')
def listar_clientes():
    """Lista todos os clientes cadastrados"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    busca = request.args.get('busca', '')
    params = {"order": "nome_empresa.asc"}
    if busca:
        params["nome_empresa"] = f"ilike.*{busca}*"
    
    clientes = api_get("clientes", params)
    return render_template('clientes.html', clientes=clientes, busca=busca)


@app.route('/clientes/api_lista')
def api_lista_clientes():
    """Retorna JSON com lista de clientes para preenchimento automático"""
    # Inclui endereco para o preenchimento completo na página de técnicos e RAT
    clientes = api_get("clientes", {"order": "nome_empresa.asc", "select": "id,nome_empresa,nome_gestor,whatsapp,endereco,cnpj_cpf"})
    return jsonify(clientes)


@app.route('/clientes/novo', methods=['GET', 'POST'])
def novo_cliente():
    """Cadastra novo cliente"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        dados = {
            "nome_empresa": request.form.get('nome_empresa', '').strip(),
            "nome_gestor": request.form.get('nome_gestor', '').strip(),
            "whatsapp": request.form.get('whatsapp', '').strip(),
            "endereco": request.form.get('endereco', '').strip(),
            "cnpj_cpf": request.form.get('cnpj_cpf', '').strip(),
            "observacoes": request.form.get('observacoes', '').strip()
        }
        
        if not dados["nome_empresa"]:
            return render_template('cliente_form.html', cliente=dados, erro="Nome da empresa é obrigatório")
        
        try:
            api_post("clientes", dados)
            registrar_log("cliente_cadastro", f"Cliente '{dados['nome_empresa']}' cadastrado")
            return redirect(url_for('listar_clientes'))
        except Exception as e:
            return render_template('cliente_form.html', cliente=dados, erro=f"Erro ao cadastrar: {e}")
    
    return render_template('cliente_form.html', cliente={}, erro=None)


@app.route('/clientes/<int:id>/editar', methods=['GET', 'POST'])
def editar_cliente(id):
    """Edita cliente existente"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    dados = api_get("clientes", {"id": f"eq.{id}", "limit": "1"})
    if not dados:
        return "Cliente não encontrado", 404
    
    cliente = dados[0]
    
    if request.method == 'POST':
        dados_update = {
            "nome_empresa": request.form.get('nome_empresa', '').strip(),
            "nome_gestor": request.form.get('nome_gestor', '').strip(),
            "whatsapp": request.form.get('whatsapp', '').strip(),
            "endereco": request.form.get('endereco', '').strip(),
            "cnpj_cpf": request.form.get('cnpj_cpf', '').strip(),
            "observacoes": request.form.get('observacoes', '').strip()
        }
        
        if not dados_update["nome_empresa"]:
            return render_template('cliente_form.html', cliente={**cliente, **dados_update}, erro="Nome da empresa é obrigatório")
        
        api_patch("clientes", dados_update, {"id": f"eq.{id}"})
        registrar_log("cliente_edicao", f"Cliente '{dados_update['nome_empresa']}' editado")
        return redirect(url_for('listar_clientes'))
    
    return render_template('cliente_form.html', cliente=cliente, erro=None)


@app.route('/clientes/<int:id>/excluir', methods=['POST'])
def excluir_cliente(id):
    """Exclui cliente"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    dados = api_get("clientes", {"id": f"eq.{id}", "limit": "1"})
    nome = dados[0].get('nome_empresa', '') if dados else ''
    api_delete("clientes", {"id": f"eq.{id}"})
    registrar_log("cliente_exclusao", f"Cliente '{nome}' excluído")
    return redirect(url_for('listar_clientes'))


@app.route('/api/cliente/<int:id>')
def api_cliente_dados(id):
    """API pública para auto-preenchimento do formulário de chamado"""
    dados = api_get("clientes", {"id": f"eq.{id}", "limit": "1"})
    if dados:
        return jsonify(dados[0])
    return jsonify({}), 404


# ==================== ROTAS DA AGENDA ====================

@app.route('/agenda')
def pagina_agenda():
    """Página da agenda/calendário"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Carrega chamados ativos para vincular
    chamados = api_get("chamados", {"status": "neq.Finalizado", "order": "codigo_os.asc", "select": "id,codigo_os,cliente,empresa"})
    
    # Mês e ano atuais ou da query
    from datetime import datetime
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    return render_template('agenda.html', chamados=chamados, ano=ano, mes=mes)


@app.route('/agenda/api_eventos')
def api_eventos_agenda():
    """API que retorna eventos de um mês"""
    if not session.get('logado'):
        return jsonify([])
    
    from datetime import datetime
    ano = request.args.get('ano', datetime.now().year, type=int)
    mes = request.args.get('mes', datetime.now().month, type=int)
    
    # Filtra por mês
    mes_str = f"{ano:04d}-{mes:02d}"
    eventos = api_get("agenda", {
        "data_agenda": f"gte.{mes_str}-01",
        "and": f"(data_agenda.lte.{mes_str}-31)",
        "order": "data_agenda.asc,id.asc"
    })
    
    # Busca informações dos chamados vinculados
    for ev in eventos:
        if ev.get('chamado_id'):
            chamado = api_get("chamados", {"id": f"eq.{ev['chamado_id']}", "limit": "1", "select": "codigo_os,cliente"})
            if chamado:
                ev['codigo_os'] = chamado[0].get('codigo_os', '')
                ev['cliente_nome'] = chamado[0].get('cliente', '')
    
    return jsonify(eventos)


@app.route('/agenda/salvar', methods=['POST'])
def salvar_evento():
    """Cria ou atualiza evento na agenda"""
    if not session.get('logado'):
        return jsonify({"erro": "Não autorizado"}), 401
    
    data = request.get_json()
    evento_id = data.get('id')
    
    dados_evento = {
        "data_agenda": data.get('data_agenda'),
        "chamado_id": data.get('chamado_id') if data.get('chamado_id') else None,
        "titulo": data.get('titulo', '').strip(),
        "descricao": data.get('descricao', '').strip(),
        "tecnico": data.get('tecnico', '').strip(),
        "cor": data.get('cor', '#3b82f6'),
        "repetir": data.get('repetir', False)
    }
    
    print(f"📝 Salvando evento: {dados_evento}")
    
    if not dados_evento['data_agenda']:
        return jsonify({"erro": "Data é obrigatória"}), 400
    
    if evento_id:
        api_patch("agenda", dados_evento, {"id": f"eq.{evento_id}"})
        registrar_log("agenda_editar", f"Evento '{dados_evento['titulo']}' editado em {dados_evento['data_agenda']}")
    else:
        resultado = api_post("agenda", dados_evento)
        print(f"✅ Evento salvo no banco: {resultado}")
        registrar_log("agenda_criar", f"Evento '{dados_evento['titulo']}' criado em {dados_evento['data_agenda']}")
        
        # Notifica técnico sobre nova tarefa na agenda
        print(f"🔔 Verificando notificação para técnico: {dados_evento.get('tecnico')}")
        if dados_evento.get('tecnico'):
            telefone_tecnico = obter_telefone_tecnico(dados_evento['tecnico'])
            print(f"📱 Telefone do técnico: {telefone_tecnico}")
            if telefone_tecnico:
                codigo_chamado = None
                chamado_cliente = None
                chamado_endereco = None
                if dados_evento.get('chamado_id'):
                    chamado_info = api_get("chamados", {"id": f"eq.{dados_evento['chamado_id']}", "limit": "1", "select": "codigo_os,cliente,endereco"})
                    if chamado_info:
                        codigo_chamado = chamado_info[0].get('codigo_os')
                        chamado_cliente = chamado_info[0].get('cliente', '')
                        chamado_endereco = chamado_info[0].get('endereco', '')
                print(f"📤 Enviando notificação WhatsApp...")
                resultado = notificar_nova_tarefa_agenda(
                    dados_evento['data_agenda'],
                    dados_evento['titulo'],
                    telefone_tecnico,
                    codigo_chamado,
                    chamado_cliente,
                    dados_evento.get('tecnico'),
                    dados_evento.get('descricao', '')
                )
                print(f"✅ Notificação enviada: {resultado}")
            else:
                print("❌ Telefone não encontrado para o técnico")
        
        # Cria evento no iCloud Calendar
        chamado_info_icloud = None
        if dados_evento.get('chamado_id'):
            chamado_info_icloud = api_get("chamados", {"id": f"eq.{dados_evento['chamado_id']}", "limit": "1", "select": "codigo_os,cliente,endereco,descricao"})
            if chamado_info_icloud:
                chamado_info_icloud = chamado_info_icloud[0]
        
        criar_evento_da_agenda(dados_evento, chamado_info_icloud)
    
    return jsonify({"sucesso": True}), 200


@app.route('/agenda/<int:id>/excluir', methods=['POST'])
def excluir_evento(id):
    """Exclui evento da agenda"""
    if not session.get('logado'):
        return jsonify({"erro": "Não autorizado"}), 401
    
    dados = api_get("agenda", {"id": f"eq.{id}", "limit": "1"})
    titulo = dados[0].get('titulo', '') if dados else ''
    api_delete("agenda", {"id": f"eq.{id}"})
    registrar_log("agenda_excluir", f"Evento '{titulo}' excluído")
    
    return jsonify({"sucesso": True}), 200


# ==================== ROTAS DE FINANCEIRO ====================

@app.route('/financeiro')
def pagina_financeiro():
    """Página de financeiro"""
    print(f"🔍 Acessando /financeiro - Usuário: {session.get('usuario')}")
    if not session.get('logado'):
        print("❌ Não logado")
        return redirect(url_for('login'))
    print("✅ Acesso permitido")
    return render_template('financeiro.html')


@app.route('/financeiro/api_lista')
def api_lista_financeiro():
    """API que retorna lista de financeiro"""
    if not session.get('logado'):
        return jsonify([])
    
    status = request.args.get('status', '')
    busca = request.args.get('busca', '')
    
    # JOIN com chamados para pegar dados do cliente
    query = """
        SELECT f.*, c.codigo_os, c.cliente, c.empresa 
        FROM financeiro f 
        JOIN chamados c ON f.chamado_id = c.id 
        WHERE 1=1
    """
    params = {}
    
    if status:
        query += " AND f.status_pagamento = :status"
        params['status'] = status
    
    if busca:
        query += " AND (c.codigo_os ILIKE :busca OR c.cliente ILIKE :busca OR c.empresa ILIKE :busca)"
        params['busca'] = f"%{busca}%"
    
    query += " ORDER BY f.data_criacao DESC"
    
    # Usa a API do Supabase
    financeiro = api_get("financeiro", {"order": "data_criacao.desc"})
    
    # Busca dados dos chamados
    for item in financeiro:
        chamado = api_get("chamados", {"id": f"eq.{item['chamado_id']}", "limit": "1", "select": "codigo_os,cliente,empresa"})
        if chamado:
            item['codigo_os'] = chamado[0].get('codigo_os', '')
            item['cliente'] = chamado[0].get('cliente', '')
            item['empresa'] = chamado[0].get('empresa', '')
    
    return jsonify(financeiro)


@app.route('/financeiro/salvar', methods=['POST'])
def salvar_financeiro():
    """Salva dados financeiros"""
    if not session.get('logado'):
        return jsonify({"erro": "Não autorizado"}), 401
    
    data = request.get_json()
    
    dados = {
        "chamado_id": int(data.get('chamado_id')),
        "valor": float(data.get('valor', 0)),
        "status_pagamento": data.get('status_pagamento', 'Pendente'),
        "observacoes": data.get('observacoes', ''),
        "usuario_criacao": session.get('usuario', 'sistema')
    }
    
    # Se status for Pago, adiciona data de pagamento
    if dados['status_pagamento'] == 'Pago':
        dados['data_pagamento'] = datetime.now().isoformat()
        dados['usuario_pagamento'] = session.get('usuario', 'sistema')
    
    financeiro_id = data.get('id')
    
    if financeiro_id:
        # Atualiza
        api_patch("financeiro", dados, {"id": f"eq.{financeiro_id}"})
        registrar_log("financeiro_editar", f"Financeiro ID {financeiro_id} atualizado - Status: {dados['status_pagamento']}")
    else:
        # Cria novo
        api_post("financeiro", dados)
        registrar_log("financeiro_criar", f"Financeiro criado para chamado {dados['chamado_id']}")
    
    return jsonify({"sucesso": True}), 200


# ==================== ROTAS DE USUÁRIOS ====================

@app.route('/usuarios')
def pagina_usuarios():
    """Página de gerenciamento de usuários"""
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Apenas admin pode acessar
    if session.get('usuario') != 'tecsenior':
        return redirect(url_for('admin'))
    
    usuarios = api_get("usuarios", {"order": "nome.asc"})
    return render_template('usuarios.html', usuarios=usuarios)


@app.route('/usuarios/api_lista')
def api_lista_usuarios():
    """API que retorna lista de usuários"""
    if not session.get('logado'):
        return jsonify([])
    
    usuarios = api_get("usuarios", {"order": "nome.asc"})
    return jsonify(usuarios)


@app.route('/usuarios/salvar', methods=['POST'])
def salvar_usuario():
    """Salva usuário (criar/editar)"""
    if not session.get('logado') or session.get('usuario') != 'tecsenior':
        return jsonify({"erro": "Apenas admin"}), 403
    
    data = request.get_json()
    
    dados = {
        "username": data.get('username', '').strip(),
        "nome": data.get('nome', '').strip(),
        "nivel": data.get('nivel', 'tecnico'),
        "ativo": data.get('ativo', True)
    }
    
    # Se tem senha, atualiza ela
    if data.get('senha'):
        dados['senha'] = data.get('senha')  # Em produção, use hash!
    
    usuario_id = data.get('id')
    
    if usuario_id:
        api_patch("usuarios", dados, {"id": f"eq.{usuario_id}"})
        registrar_log("usuario_editar", f"Usuário {dados['username']} editado")
    else:
        if not dados['senha']:
            return jsonify({"erro": "Senha obrigatória"}), 400
        api_post("usuarios", dados)
        registrar_log("usuario_criar", f"Usuário {dados['username']} criado")
    
    return jsonify({"sucesso": True}), 200


@app.route('/usuarios/<int:id>/excluir', methods=['POST'])
def excluir_usuario(id):
    """Exclui usuário"""
    if not session.get('logado') or session.get('usuario') != 'tecsenior':
        return jsonify({"erro": "Apenas admin"}), 403
    
    api_delete("usuarios", {"id": f"eq.{id}"})
    registrar_log("usuario_excluir", f"Usuário ID {id} excluído")
    
    return jsonify({"sucesso": True}), 200


# Inicializa
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
