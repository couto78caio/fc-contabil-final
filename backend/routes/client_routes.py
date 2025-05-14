# backend/routes/client_routes.py
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash, current_app
)
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine # Consider moving engine/session to a central db manager
from sqlalchemy.orm import sessionmaker
from backend.database.models import Cliente, DocumentoEnviado # Assuming DocumentoEnviado model exists or will be created
from backend.utils.encryption import encrypt_file
from backend.utils.checklist import atualizar_checklist # This might need adjustment if DB stores checklist
import os
import datetime
import re # For input validation

client_bp = Blueprint(
    "client",
    __name__,
    template_folder="../../cliente_interface/templates",
    static_folder="../../cliente_interface/static",
    static_url_path="/cliente/static" # Explicitly set static_url_path for client blueprint
)

# --- Database Setup (Consider a centralized approach) ---
# This repetitive DB setup in each route file is not ideal.
# It should be initialized once in main.py or a dedicated db.py and imported.
DATABASE_URL = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'dados_fc.db')}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Allowed Uploads ---
ALLOWED_EXTENSIONS = {"pdf", "xml", "ofx", "jpg", "jpeg", "png"}
ALLOWED_MODALIDADES = ["notas_fiscais", "extrato_bancario", "folha_pagamento", "outros"]

def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Helper to get DB session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Client Login ---
@client_bp.route("/login", methods=["GET", "POST"])
def login_cliente():
    if "cnpj_cliente" in session:
        return redirect(url_for("client.enviar_documento"))

    if request.method == "POST":
        cnpj = request.form.get("cnpj", "").strip()
        razao_social = request.form.get("razao_social", "").strip()

        # Validate CNPJ (basic validation)
        if not cnpj or not re.match(r"^\d{14}$", cnpj):
            flash("CNPJ inválido. Deve conter 14 números.", "danger")
            return redirect(url_for("client.login_cliente"))

        db = next(get_db())
        cliente = db.query(Cliente).filter_by(cnpj=cnpj).first()

        if not cliente:
            if not razao_social:
                # For new clients, Razao Social could be made mandatory on the form
                flash("Razão Social é obrigatória para novo cliente.", "warning")
                # Or provide a default if allowed by business logic
                # razao_social = f"Cliente {cnpj[:4]}"
                return render_template("login_cliente.html")
            
            # Sanitize razao_social (e.g., limit length)
            razao_social_sane = razao_social[:100] 
            cliente = Cliente(cnpj=cnpj, razao_social=razao_social_sane)
            try:
                db.add(cliente)
                db.commit()
                flash(f"Novo cliente {razao_social_sane} cadastrado com CNPJ {cnpj}.", "success")
            except Exception as e:
                db.rollback()
                current_app.logger.error(f"Erro ao cadastrar novo cliente: {e}")
                flash("Erro ao cadastrar novo cliente. Tente novamente.", "danger")
                return render_template("login_cliente.html")
        
        session["cnpj_cliente"] = cliente.cnpj
        session["cliente_id"] = cliente.id # Store client ID for easier linking
        flash(f"Login bem-sucedido para {cliente.razao_social}!", "success")
        return redirect(url_for("client.enviar_documento"))

    return render_template("login_cliente.html")

# --- Client Logout ---
@client_bp.route("/logout")
def logout_cliente():
    session.pop("cnpj_cliente", None)
    session.pop("cliente_id", None)
    flash("Você foi desconectado.", "info")
    return redirect(url_for("client.login_cliente"))

# --- Document Submission Form ---
@client_bp.route("/", methods=["GET", "POST"])
@client_bp.route("/envio", methods=["GET", "POST"])
def enviar_documento():
    if "cnpj_cliente" not in session:
        flash("Por favor, faça login para enviar documentos.", "warning")
        return redirect(url_for("client.login_cliente"))

    cnpj_cliente = session["cnpj_cliente"]
    cliente_id = session["cliente_id"]

    if request.method == "POST":
        modalidade = request.form.get("modalidade")
        mes_ref = request.form.get("mes_referencia") # Expected format YYYY-MM
        arquivo_file = request.files.get("arquivo")

        # --- Input Validations ---
        if not all([modalidade, mes_ref, arquivo_file]):
            flash("Todos os campos são obrigatórios.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        if modalidade not in ALLOWED_MODALIDADES:
            flash("Modalidade inválida.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        if not re.match(r"^\d{4}-\d{2}$", mes_ref):
            flash("Formato do mês de referência inválido. Use AAAA-MM.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)
        
        year, month = map(int, mes_ref.split("-"))
        if not (1900 <= year <= datetime.datetime.now().year + 1 and 1 <= month <= 12):
            flash("Mês de referência fora do intervalo válido.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        if arquivo_file.filename == "":
            flash("Nenhum arquivo selecionado.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        if not allowed_file(arquivo_file.filename):
            flash(f"Tipo de arquivo não permitido. Permitidos: {', '.join(ALLOWED_EXTENSIONS)}", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)
        
        # --- Secure Path and Filename ---
        # Validate components used in path construction to prevent traversal
        # CNPJ is from session, assumed safe. mes_ref and modalidade validated above.
        # Basic check for directory components:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", modalidade) or not re.match(r"^\d{4}-\d{2}$", mes_ref):
            flash("Componentes de caminho inválidos.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        filename = secure_filename(arquivo_file.filename)
        # Limit filename length
        filename = filename[:100]

        upload_folder_base = current_app.config.get("UPLOAD_FOLDER", os.path.join(current_app.root_path, "..", "uploads"))
        # Path construction: UPLOAD_FOLDER / CNPJ / MES_REF / MODALIDADE / filename
        # Ensure CNPJ, MES_REF, MODALIDADE are sanitized/validated to prevent path traversal.
        # CNPJ from session is generally safer. mes_ref and modalidade validated above.
        path_parts = [upload_folder_base, cnpj_cliente, mes_ref, modalidade]
        for part in path_parts[1:]: # Skip base folder for this check
            if '..' in part or part.startswith('/'):
                flash("Caminho de upload inválido.", "danger")
                return render_template("index.html", cnpj=cnpj_cliente)
        
        destino_dir = os.path.join(*path_parts)
        
        try:
            os.makedirs(destino_dir, exist_ok=True)
        except OSError as e:
            current_app.logger.error(f"Erro ao criar diretório {destino_dir}: {e}")
            flash("Erro no servidor ao preparar o upload. Tente mais tarde.", "danger")
            return render_template("index.html", cnpj=cnpj_cliente)

        caminho_arquivo = os.path.join(destino_dir, filename)

        # Check for filename collision (optional, depends on requirements)
        if os.path.exists(caminho_arquivo):
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{timestamp}{ext}"
            filename = filename[:100] # Re-check length
            caminho_arquivo = os.path.join(destino_dir, filename)

        try:
            arquivo_file.save(caminho_arquivo)
            encrypt_file(caminho_arquivo) # Assumes encrypt_file handles its own errors
            
            # --- Record in Database ---
            db = next(get_db())
            novo_documento = DocumentoEnviado(
                cliente_id=cliente_id,
                mes_referencia=mes_ref,
                modalidade=modalidade,
                nome_arquivo=filename,
                caminho_arquivo=caminho_arquivo, # Store relative or absolute path as needed
                protocolo="", # Will be generated next
                data_envio=datetime.datetime.utcnow()
            )
            db.add(novo_documento)
            db.flush() # To get novo_documento.id

            protocolo_str = f"PROTO-{cnpj_cliente[:6]}-{mes_ref.replace('-', '')}-{novo_documento.id}-{datetime.datetime.now().strftime('%S%f')[:8]}"
            novo_documento.protocolo = protocolo_str
            db.commit()

            # Atualizar checklist (se ainda for baseado em arquivo)
            # Consider moving checklist logic to be database-driven as well.
            # atualizar_checklist(cnpj_cliente, modalidade, mes_ref, filename) # Pass filename if needed

            flash(f"Documento '{filename}' enviado com sucesso! Protocolo: {protocolo_str}", "success")
            return redirect(url_for("client.enviar_documento")) # Or to history

        except Exception as e:
            current_app.logger.error(f"Erro ao salvar/processar arquivo {filename} para {cnpj_cliente}: {e}")
            flash("Erro ao processar o arquivo. Tente novamente.", "danger")
            # Cleanup partially saved file if necessary
            if os.path.exists(caminho_arquivo):
                 try: os.remove(caminho_arquivo) catch: pass
            if 'db' in locals() and db.is_active: db.rollback()

    return render_template("index.html", cnpj=cnpj_cliente)

# --- Client Document History ---
@client_bp.route("/historico")
def historico_envios(): # Renamed for clarity
    if "cnpj_cliente" not in session:
        flash("Por favor, faça login para ver o histórico.", "warning")
        return redirect(url_for("client.login_cliente"))

    cnpj_cliente = session["cnpj_cliente"]
    cliente_id = session["cliente_id"]
    db = next(get_db())

    # Fetch from database instead of filesystem scanning
    documentos_db = db.query(DocumentoEnviado).filter_by(cliente_id=cliente_id).order_by(DocumentoEnviado.data_envio.desc()).all()
    
    # The old filesystem scanning logic is less reliable and secure.
    # If it must be kept for some reason, it needs significant hardening against path traversal.

    return render_template("historico.html", cnpj=cnpj_cliente, documentos=documentos_db)

# Ensure client_bp is registered in main.py with the correct static_folder and template_folder if not already.
# The Blueprint definition here already sets them relative to this file's location.

