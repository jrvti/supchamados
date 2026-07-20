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

# Remove barra final se houver
SUPABASE_URL = SUPABASE_URL.rstrip('/')

# Cabeçalhos padrão para API REST do Supabase (PostgREST)
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
    """GET via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.get(url, headers=headers, params=params)
    if resp.status_code >= 400:
        print(f"⚠️  GET {table} erro {resp.status_code}: {resp.text}")
    return resp.json() if resp.ok else []


def api_post(table, data):
    """POST (INSERT) via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code >= 400:
        print(f"⚠️  POST {table} erro {resp.status_code}: {resp.text}")
    return resp.json() if resp.ok else []


def api_patch(table, data, filters):
    """PATCH (UPDATE) via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.patch(url, headers=headers, params=filters, json=data)
    if resp.status_code >= 400:
        print(f"⚠️  PATCH {table} erro {resp.status_code}: {resp.text}")
    return resp.ok


def api_delete(table, filters):
    """DELETE via REST API"""
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = api_headers(use_service_role=True)
    resp = requests.delete(url, headers=headers, params=filters)
    if resp.status_code >= 400:
        print(f"⚠️  DELETE {table} erro {resp.status_code}: {resp.text}")
    return resp.ok


def init_db():
    """Cria a tabela chamados via REST API"""
    print("🔄 Inicializando banco de dados via REST API...")
    
    # Verifica se a tabela existe tentando listar
    dados = api_get("chamados", params={"limit": 1})
    
    if isinstance(dados, list):
        print("✅ Tabela 'chamados' já existe e está acessível!")
        return
    
    # Se não existir, precisamos criar via SQL
    # Usamos o endpoint /sql para executar SQL direto
    try:
        url = f"{SUPABASE_URL}/rest/v1/rpc/"
        headers = api_headers(use_service_role=True)
        
        # O Supabase tem um endpoint /sql para queries SQL
        sql_url = f"{SUPABASE_URL}/sql"
        sql_body = """
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
        """
        resp = requests.post(sql_url, headers=headers, json={"query": sql_body})
        if resp.ok:
            print("✅ Tabela 'chamados' criada com sucesso!")
        else:
            print(f"⚠️  Não foi possível criar tabela via SQL API: {resp.status_code}")
            print("   Crie manualmente no SQL Editor do Supabase com o script acima.")
    except Exception as e:
        print(f"⚠️  Erro ao criar tabela: {e}")
        print("   Crie manualmente no SQL Editor do Supabase.")


def supabase_storage_upload(nome_arquivo, conteudo_bytes):
    """Faz upload PDF para o Storage do Supabase via API REST"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return False
    try:
        bucket_url = f"{SUPABASE_URL}/storage/v1/bucket/rats"
        headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        requests.post(bucket_url, headers=headers, json={"name": "rats", "public": True})
    except:
        pass
    
    url = f"{SUPABASE_URL}/storage/v1/object/rats/{nome_arquivo}"
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/pdf"
    }
    resp = requests.post(url, headers=headers, data=conteudo_bytes)
    return resp.ok


def supabase_storage_download(nome_arquivo):
    """Baixa PDF do Storage do Supabase via API REST"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return None
    url = f"{SUPABASE_URL}/storage/v1/object/public/rats/{nome_arquivo}"
    headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
    resp = requests.get(url, headers=headers)
    if resp.ok:
        return resp.content
    return None


def gerar_codigo_os():
    caracteres = string.ascii_uppercase + string.digits
    return f"OS-{''.join(random.choice(caracteres) for _ in range(6))}"


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
    
    data = {
        "codigo_os": codigo_gerado,
        "cliente": cliente,
        "empresa": empresa,
        "whatsapp": whatsapp,
        "descricao": descricao_final,
        "marca": marca,
        "modelo": modelo,
        "urgencia": "Média"
    }
    
    api_post("chamados", data)
    return render_template('sucesso.html', codigo_os=codigo_gerado)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('usuario') in ['tecsenior', 'tecnicon2', 'tecnicon1'] and request.form.get('senha') == 'S@cCham@d##s2005':
            session['logado'] = True
            session['usuario'] = request.form.get('usuario')
            return redirect(url_for('admin'))
        return render_template('login.html', erro="Credenciais incorretas.")
    return render_template('login.html', erro=None)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        chamado_id = request.form.get('id')
        api_patch("chamados", {
            "status": request.form.get('status'),
            "tecnico_responsavel": request.form.get('tecnico_responsavel'),
            "urgencia": request.form.get('urgencia')
        }, {"id": f"eq.{chamado_id}"})
    
    busca = request.args.get('busca', '')
    params = {"status": "neq.Finalizado", "order": "id.desc"}
    if busca:
        params["or"] = f"(codigo_os.ilike.*{busca}*,cliente.ilike.*{busca}*)"
    
    chamados = api_get("chamados", params)
    
    return render_template('admin.html', chamados=chamados, tecnico_atual=session.get('usuario'), busca=busca)


@app.route('/arquivados')
def arquivados():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    busca = request.args.get('busca', '')
    params = {"status": "eq.Finalizado", "order": "id.desc"}
    if busca:
        params["or"] = f"(codigo_os.ilike.*{busca}*,cliente.ilike.*{busca}*)"
    
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
    return render_template('detalhes.html', chamado=dados[0])


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
            pdf_salvo = supabase_storage_upload(nome_arquivo, pdf_bytes)
        except Exception as e:
            print(f"Erro ao enviar PDF: {e}")

    api_patch("chamados", {"status": "Finalizado"}, {"id": f"eq.{id}"})

    msg = "Chamado arquivado com sucesso!"
    if pdf_salvo:
        msg += " RAT salva no storage."
    else:
        msg += " (PDF não foi salvo - verifique config do Supabase)"

    return jsonify({"sucesso": True, "mensagem": msg}), 200


@app.route('/baixar_rat/<int:id>')
def baixar_rat(id):
    if not session.get('logado'):
        return redirect(url_for('login'))

    nome_arquivo = f'RAT_OS_{id}.pdf'
    pdf_data = supabase_storage_download(nome_arquivo)

    if pdf_data:
        return send_file(
            io.BytesIO(pdf_data),
            as_attachment=True,
            download_name=nome_arquivo,
            mimetype='application/pdf'
        )

    return "Arquivo PDF não encontrado no storage", 404


@app.route('/chamado/<int:id>/excluir', methods=['POST'])
def excluir_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    api_delete("chamados", {"id": f"eq.{id}"})
    return redirect(url_for('admin'))


@app.route('/modelo_base_pdf')
def modelo_rat():
    caminho_arquivo = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modelo_rat.pdf')
    if os.path.exists(caminho_arquivo):
        return send_file(caminho_arquivo, mimetype='application/pdf')
    return "Arquivo não encontrado", 404


@app.route('/dashboard')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    
    # Métricas via REST API
    total_ativos = len(api_get("chamados", {"status": "neq.Finalizado", "select": "id"}))
    
    total_fechados = len(api_get("chamados", {"status": "eq.Finalizado", "select": "id"}))
    
    criticos = api_get("chamados", {
        "status": "neq.Finalizado",
        "urgencia": "in.(Alta,Crítica)",
        "select": "id"
    })
    total_criticos = len(criticos)
    
    ranking_tecnicos = api_get("chamados", {
        "status": "eq.Finalizado",
        "select": "tecnico_responsavel,count",
        "group": "tecnico_responsavel",
        "order": "count.desc"
    })
    
    top_clientes = api_get("chamados", {
        "select": "empresa,count",
        "group": "empresa",
        "order": "count.desc",
        "limit": 3
    })
    
    return render_template('dashboard.html', 
                           total_ativos=total_ativos, 
                           total_fechados=total_fechados,
                           total_criticos=total_criticos, 
                           ranking_tecnicos=ranking_tecnicos,
                           top_clientes=top_clientes)


# Inicializa
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
