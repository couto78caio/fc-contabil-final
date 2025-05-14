import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Cria a instância do Flask – templates e estáticos do cliente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'cliente_interface', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'cliente_interface', 'static')
)

# Habilita CORS
CORS(app)

# Configurações gerais
app.secret_key = os.getenv("SECRET_KEY", "fc_super_segura_123")
app.config['UPLOAD_FOLDER']      = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB

# Garante que a pasta de uploads exista
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ───── Banco de dados ─────
engine = create_engine(f"sqlite:///{os.path.join(BASE_DIR, 'dados_fc.db')}")
Session = sessionmaker(bind=engine)
db_session = Session()

# ───── Flask-Login ─────
login_manager = LoginManager()
login_manager.login_view = 'staff.login'
login_manager.init_app(app)

from backend.database.models import Usuario
@login_manager.user_loader
def load_user(user_id):
    return db_session.query(Usuario).get(int(user_id))

# ───── Blueprints ─────
from backend.routes.client_routes import client_bp
from backend.routes.staff_routes  import staff_bp

app.register_blueprint(client_bp, url_prefix='/cliente')
app.register_blueprint(staff_bp,  url_prefix='/painel')

# ───── Rotas gerais ─────
@app.route('/')
def home():
    # página inicial do cliente
    return render_template('index.html')

if __name__ == "__main__":
    # Mostra todas as rotas (útil para debug de static_url_path)
    print(app.url_map)
    app.run(debug=True)
