from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from backend.database.models import Usuario
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import check_password_hash, generate_password_hash
import os, datetime, json
from collections import defaultdict, Counter

staff_bp = Blueprint(
    'staff',
    __name__,
    template_folder='../../painel_funcionario/templates',
    static_folder='../../painel_funcionario/static',
    static_url_path='/painel/static'
)

# Banco de dados
engine = create_engine("sqlite:///dados_fc.db")
Session = sessionmaker(bind=engine)
db = Session()

# Login / Logout
@staff_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = db.query(Usuario).filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.senha, request.form["senha"]):
            login_user(user)
            return redirect(url_for("staff.documentos"))
        flash("Usuário ou senha inválidos.")
    return render_template("login.html")

@staff_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("staff.login"))

# Esqueci a senha
@staff_bp.route("/esqueci_senha", methods=["GET", "POST"])
def esqueci_senha():
    if request.method == "POST":
        username   = request.form["username"]
        nova_senha = request.form["nova_senha"]
        confirma   = request.form["confirma_senha"]
        user = db.query(Usuario).filter_by(username=username).first()
        if not user:
            flash("Usuário não encontrado.")
        elif nova_senha != confirma:
            flash("A nova senha e a confirmação não coincidem.")
        else:
            user.senha = generate_password_hash(nova_senha)
            db.commit()
            flash("Senha redefinida com sucesso! Faça login.")
            return redirect(url_for("staff.login"))
    return render_template("esqueci_senha.html")

# Alterar senha (logado)
@staff_bp.route("/alterar_senha", methods=["GET", "POST"])
@login_required
def alterar_senha():
    if request.method == "POST":
        atual    = request.form["senha_atual"]
        nova     = request.form["nova_senha"]
        confirma = request.form["confirma_senha"]
        if not check_password_hash(current_user.senha, atual):
            flash("Senha atual incorreta.")
        elif nova != confirma:
            flash("A nova senha e a confirmação não coincidem.")
        else:
            current_user.senha = generate_password_hash(nova)
            db.commit()
            flash("Senha alterada com sucesso!")
            return redirect(url_for("staff.documentos"))
    return render_template("alterar_senha.html", usuario=current_user.username)

# Redireciona para documentos
@staff_bp.route("/")
@login_required
def painel():
    return redirect(url_for("staff.documentos"))

# Listagem de documentos + métricas para cards
@staff_bp.route("/documentos")
@login_required
def documentos():
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    documentos = []

    if os.path.exists(uploads_dir):
        for cnpj in os.listdir(uploads_dir):
            cnpj_path = os.path.join(uploads_dir, cnpj)
            if not os.path.isdir(cnpj_path):
                continue
            for mes in os.listdir(cnpj_path):
                mes_path = os.path.join(cnpj_path, mes)
                if not os.path.isdir(mes_path):
                    continue
                for modalidade in os.listdir(mes_path):
                    mod_path = os.path.join(mes_path, modalidade)
                    if not os.path.isdir(mod_path):
                        continue
                    for nome_arquivo in os.listdir(mod_path):
                        arquivo_path = os.path.join(mod_path, nome_arquivo)
                        data_mod = datetime.datetime.fromtimestamp(
                            os.path.getmtime(arquivo_path)
                        ).strftime("%d/%m/%Y %H:%M")
                        documentos.append({
                            "cnpj": cnpj,
                            "mes": mes,
                            "modalidade": modalidade,
                            "arquivo": nome_arquivo,
                            "data_envio": data_mod
                        })

    documentos.sort(key=lambda x: x["data_envio"], reverse=True)

    enviados_por_mes     = defaultdict(int)
    enviados_por_cliente = Counter()
    meses                = set()
    clientes             = set()
    for d in documentos:
        meses.add(d["mes"])
        clientes.add(d["cnpj"])
        enviados_por_mes[d["mes"]] += 1
        enviados_por_cliente[d["cnpj"]] += 1
    pendencias_por_cliente = defaultdict(int)

    return render_template(
        "painel.html",
        usuario=current_user.username,
        documentos=documentos,
        pendencias_por_cliente=pendencias_por_cliente,
        enviados_por_cliente=enviados_por_cliente,
        enviados_por_mes=enviados_por_mes,
        total_envios=len(documentos),
        total_clientes=len(clientes),
        total_pendencias=sum(pendencias_por_cliente.values()),
        total_meses=len(meses)
    )

# Checklist por cliente
@staff_bp.route("/checklist/<cnpj>")
@login_required
def checklist_cliente(cnpj):
    OBRIG = ["notas_fiscais", "extrato_bancario", "folha_pagamento", "outros"]
    path  = os.path.join("uploads", cnpj, "checklist.json")
    resultado = {}
    if os.path.exists(path):
        with open(path, "r") as f:
            chk = json.load(f)
        for mes, lista in chk.items():
            resultado[mes] = [
                {"modalidade": d, "status": "Enviado" if d in lista else "Pendente"}
                for d in OBRIG
            ]
    return render_template(
        "painel.html",
        usuario=current_user.username,
        checklist=resultado,
        cnpj=cnpj
    )

# Dashboard com gráficos
@staff_bp.route("/dashboard")
@login_required
def dashboard():
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    enviados_por_mes     = defaultdict(int)
    enviados_por_cliente = Counter()
    pendencias_por_cliente = defaultdict(int)
    OBRIG = {"notas_fiscais", "extrato_bancario", "folha_pagamento", "outros"}

    if os.path.exists(uploads_dir):
        for cnpj in os.listdir(uploads_dir):
            cnpj_path = os.path.join(uploads_dir, cnpj)
            if not os.path.isdir(cnpj_path):
                continue
            chk_path = os.path.join(cnpj_path, "checklist.json")
            if not os.path.exists(chk_path):
                continue
            with open(chk_path, "r") as f:
                chk = json.load(f)
            for mes, lista in chk.items():
                enviados_por_mes[mes] += len(lista)
                enviados_por_cliente[cnpj] += len(lista)
                pendencias_por_cliente[cnpj] += len(OBRIG - set(lista))

    return render_template(
        "dashboard.html",
        usuario=current_user.username,
        enviados_por_mes=enviados_por_mes,
        enviados_por_cliente=enviados_por_cliente,
        pendencias_por_cliente=pendencias_por_cliente
    )

# Download de arquivos da pasta uploads
@staff_bp.route('/download/<cnpj>/<mes>/<path:filename>')
@login_required
def download_file(cnpj, mes, filename):
    uploads_dir = os.path.join(os.getcwd(), 'uploads', cnpj, mes)
    return send_from_directory(uploads_dir, filename, as_attachment=True)

# Listagem de pastas e arquivos por cliente
@staff_bp.route("/arquivos")
@login_required
def arquivos_clientes():
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    clientes = []

    if os.path.exists(uploads_dir):
        for cnpj in os.listdir(uploads_dir):
            cnpj_path = os.path.join(uploads_dir, cnpj)
            if not os.path.isdir(cnpj_path):
                continue

            nome = cnpj
            chk_path = os.path.join(cnpj_path, "checklist.json")
            if os.path.exists(chk_path):
                try:
                    with open(chk_path, "r") as f:
                        chk = json.load(f)
                    nome = chk.get("nome_cliente", cnpj)
                except:
                    pass

            meses = []
            for mes in sorted(os.listdir(cnpj_path)):
                mes_path = os.path.join(cnpj_path, mes)
                if not os.path.isdir(mes_path):
                    continue

                arquivos = []
                for modalidade in sorted(os.listdir(mes_path)):
                    mod_path = os.path.join(mes_path, modalidade)
                    if not os.path.isdir(mod_path):
                        continue
                    for arq in sorted(os.listdir(mod_path)):
                        arquivos.append(f"{modalidade}/{arq}")

                meses.append({"mes": mes, "arquivos": arquivos})

            clientes.append({"cnpj": cnpj, "nome": nome, "meses": meses})

    return render_template(
        "arquivos.html",
        usuario=current_user.username,
        clientes=clientes
    )