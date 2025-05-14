# backend/routes/super_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from backend.database.models import Usuario, Cliente
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
import subprocess
import os

super_bp = Blueprint('super', __name__, template_folder='../../painel_funcionario/templates', static_folder='../../painel_funcionario/static', static_url_path='/painel/static')

engine = create_engine("sqlite:///dados_fc.db")
Session = sessionmaker(bind=engine)
db = Session()

def superuser_required(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_superuser:
            return abort(403)
        return f(*args, **kwargs)
    return wrapped

@super_bp.route('/admin')
@login_required
@superuser_required
def admin_dashboard():
    usuarios = db.query(Usuario).all()
    clientes = db.query(Cliente).all()
    return render_template('superuser.html', usuario=current_user.username, usuarios=usuarios, clientes=clientes)

# ——— Usuários ———

@super_bp.route('/admin/usuario/novo', methods=['GET','POST'])
@login_required
@superuser_required
def admin_criar_usuario():
    if request.method == 'POST':
        uname = request.form['username']
        email = request.form['email']
        pwd   = request.form['senha']
        is_su = bool(request.form.get('is_super', False))
        if db.query(Usuario).filter_by(username=uname).first():
            flash('Usuário já existe.', 'error')
        else:
            novo = Usuario(username=uname, email=email, senha=generate_password_hash(pwd), is_superuser=is_su)
            db.add(novo); db.commit()
            flash('Usuário criado com sucesso.', 'success')
            return redirect(url_for('super.admin_dashboard'))
    return render_template('superuser_form.html', usuario=current_user.username)

@super_bp.route('/admin/usuario/excluir/<int:uid>')
@login_required
@superuser_required
def admin_excluir_usuario(uid):
    u = db.query(Usuario).get(uid)
    if u:
        db.delete(u); db.commit()
        flash('Usuário excluído.', 'success')
    return redirect(url_for('super.admin_dashboard'))

# ——— Clientes ———

@super_bp.route('/admin/cliente/novo', methods=['GET','POST'])
@login_required
@superuser_required
def admin_criar_cliente():
    if request.method == 'POST':
        cnpj = request.form['cnpj']
        razao = request.form['razao_social']
        if db.query(Cliente).filter_by(cnpj=cnpj).first():
            flash('CNPJ já cadastrado.', 'error')
        else:
            novo = Cliente(cnpj=cnpj, razao_social=razao)
            db.add(novo); db.commit()
            flash('Cliente criado com sucesso.', 'success')
            return redirect(url_for('super.admin_dashboard'))
    return render_template('cliente_form.html', usuario=current_user.username)

@super_bp.route('/admin/cliente/excluir/<int:cid>')
@login_required
@superuser_required
def admin_excluir_cliente(cid):
    c = db.query(Cliente).get(cid)
    if c:
        db.delete(c); db.commit()
        flash('Cliente excluído.', 'success')
    return redirect(url_for('super.admin_dashboard'))

# ——— Executar script de criação de superusuário ———

@super_bp.route("/executar-script-superuser")
@login_required
@superuser_required
def executar_script_superuser():
    script_path = os.path.join(os.getcwd(), "criar_superuser_interativo.py")
    if not os.path.exists(script_path):
        flash("Script não encontrado.", "error")
        return redirect(url_for('super.admin_dashboard'))

    try:
        subprocess.run(["python", script_path], check=True)
        flash("Script executado com sucesso.", "success")
    except subprocess.CalledProcessError:
        flash("Erro ao executar o script.", "error")

    return redirect(url_for('super.admin_dashboard'))
