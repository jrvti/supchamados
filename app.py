import os
import random
import string
import io
import requests
import psycopg
from psycopg.rows import dict_row
from flask import Flask, render_template, request, send_file, redirect, url_for, session, jsonify

app = Flask(__name__)
app.secret_key = 'chave_secreta_jrvti_2026'

# === CONFIGURAÇÃO SUPABASE ===
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
DATABASE_URL = os.environ.get('DATABASE_URL')


def get_db_connection():
    """Conecta ao PostgreSQL do Supabase (via psycopg v3)"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL não configurada!")
    
    # A URL do Supabase já vem com sslmode=require no final
    # Ex: postgresql://postgres:senha@db.xxx.supabase.co:5432/postgres?sslmode=require
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ ERRO AO CONECTAR NO BANCO: {e}")
        # Tenta sem sslmode se falhar
        try:
            clean_url = DATABASE_URL.split('?')[0]  # Remove query params
            conn = psycopg.connect(clean_url, sslmode='require')
            return conn
        except Exception as e2:
            print(f"❌ SEGUNDA TENTATIVA TAMBÉM FALHOU: {e2}")
            raise


def init_db():
    """Cria a tabela chamados se não existir (executado na inicialização)"""
    try:
        print("🔄 Inicializando banco de dados...")
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
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
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Tabela 'chamados' verificada/criada com sucesso!")
    except Exception as e:
        print(f"⚠️  Erro ao inicializar banco: {e}")
        print("⚠️  O site pode funcionar, mas a página admin dará erro 500")


def supabase_storage_upload(nome_arquivo, conteudo_bytes):
    """Faz upload PDF para o Storage do Supabase via API REST"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    # Cria o bucket 'rats' se não existir (tentativa silenciosa)
    try:
        bucket_url = f"{SUPABASE_URL}/storage/v1/bucket/rats"
        headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
        requests.post(bucket_url, headers=headers, json={"name": "rats", "public": True})
    except:
        pass
    # Upload do arquivo
    url = f"{SUPABASE_URL}/storage/v1/object/rats/{nome_arquivo}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/pdf"
    }
    resp = requests.post(url, headers=headers, data=conteudo_bytes)
    return resp.ok


def supabase_storage_download(nome_arquivo):
    """Baixa PDF do Storage do Supabase via API REST"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    url = f"{SUPABASE_URL}/storage/v1/object/public/rats/{nome_arquivo}"
    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO chamados (codigo_os, cliente, empresa, whatsapp, descricao, marca, modelo, urgencia)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', (codigo_gerado, cliente, empresa, whatsapp, descricao_final, marca, modelo, 'Média'))
    conn.commit()
    cur.close()
    conn.close()
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
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    if request.method == 'POST':
        cur.execute("UPDATE chamados SET status = %s, tecnico_responsavel = %s, urgencia = %s WHERE id = %s",
                    (request.form.get('status'), request.form.get('tecnico_responsavel'),
                     request.form.get('urgencia'), request.form.get('id')))
        conn.commit()
    busca = request.args.get('busca', '')
    query = "SELECT * FROM chamados WHERE status != 'Finalizado'"
    if busca:
        query += f" AND (codigo_os ILIKE '%{busca}%' OR cliente ILIKE '%{busca}%')"
    cur.execute(query + " ORDER BY id DESC")
    chamados = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('admin.html', chamados=chamados, tecnico_atual=session.get('usuario'), busca=busca)


@app.route('/arquivados')
def arquivados():
    if not session.get('logado'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    busca = request.args.get('busca', '')
    query = "SELECT * FROM chamados WHERE status = 'Finalizado'"
    if busca:
        query += f" AND (codigo_os ILIKE '%{busca}%' OR cliente ILIKE '%{busca}%')"
    cur.execute(query + " ORDER BY id DESC")
    chamados = cur.fetchall()
    cur.close()
    conn.close()
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
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SELECT * FROM chamados WHERE id = %s", (id,))
    chamado = cur.fetchone()
    cur.close()
    conn.close()
    if not chamado:
        return "Chamado não encontrado", 404
    return render_template('detalhes.html', chamado=chamado)


@app.route('/chamado/<int:id>/rat')
def rat_chamado(id):
    if not session.get('logado'):
        return redirect(url_for('login'))
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SELECT * FROM chamados WHERE id = %s", (id,))
    chamado = cur.fetchone()
    cur.close()
    conn.close()
    if not chamado:
        return "Chamado não encontrado", 404
    return render_template('rat.html', chamado=chamado)


@app.route('/chamado/<int:id>/finalizar', methods=['POST'])
def finalizar_chamado_rat(id):
    if not session.get('logado'):
        return jsonify({"erro": "Não autorizado"}), 401

    pdf_salvo = False
    if 'pdf' in request.files and SUPABASE_URL and SUPABASE_KEY:
        arquivo_pdf = request.files['pdf']
        pdf_bytes = arquivo_pdf.read()
        nome_arquivo = f'RAT_OS_{id}.pdf'
        try:
            pdf_salvo = supabase_storage_upload(nome_arquivo, pdf_bytes)
        except Exception as e:
            print(f"Erro ao enviar PDF: {e}")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE chamados SET status = 'Finalizado' WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()

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
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM chamados WHERE id = %s", (id,))
    conn.commit()
    cur.close()
    conn.close()
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
    conn = get_db_connection()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status != 'Finalizado'")
    total_ativos = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status = 'Finalizado'")
    total_fechados = cur.fetchone()['total']
    cur.execute("SELECT COUNT(*) as total FROM chamados WHERE status != 'Finalizado' AND urgencia IN ('Alta', 'Crítica')")
    total_criticos = cur.fetchone()['total']
    cur.execute("SELECT tecnico_responsavel, COUNT(*) as qtd FROM chamados WHERE status = 'Finalizado' GROUP BY tecnico_responsavel ORDER BY qtd DESC")
    ranking_tecnicos = cur.fetchall()
    cur.execute("SELECT empresa, COUNT(*) as qtd FROM chamados GROUP BY empresa ORDER BY qtd DESC LIMIT 3")
    top_clientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', total_ativos=total_ativos, total_fechados=total_fechados,
                           total_criticos=total_criticos, ranking_tecnicos=ranking_tecnicos,
                           top_clientes=top_clientes)


# Inicializa o banco de dados (cria tabela se não existir)
init_db()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

