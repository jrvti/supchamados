import os
import random
import string
import io
import requests
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

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


# ==================== ROTAS ====================

@app.route('/')
def index():
    return render_template('cliente.html')


@app.route('/enviar_chamado', methods=['POST'])
def enviar_chamado():
    cliente = request.form.get('cliente')
    empresa = request.form.get('empresa')
    whatsapp = request.form.get('whatsapp')
    marca = request.form.get('marca', 'Não informado')
    modelo = request.form.get('modelo', 'Não informado')
    descricao = request.form.get('descricao')
    descricao_final = f"Equipamento: {marca} / {modelo} | Problema: {descricao}"
    codigo_gerado = gerar_codigo_os()

    dados_chamado = {
        "codigo_os": codigo_gerado,
        "cliente": cliente,
        "empresa": empresa,
        "whatsapp": whatsapp,
        "descricao": descricao_final,
        "marca": marca,
        "modelo": modelo,
        "urgencia": "Média",
        "status": "Aberto",
        "tecnico_responsavel": "Nenhum"
    }

    api_post("chamados", dados_chamado)

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

    busca = request.args.get('busca', '')
    params = {"status": "neq.Finalizado", "order": "id.desc"}
    if busca:
        params["or"] = f"(codigo_os.ilike.*{busca}*,cliente.ilike.*{busca}*,empresa.ilike.*{busca}*,descricao.ilike.*{busca}*)"

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


# Inicializa
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
