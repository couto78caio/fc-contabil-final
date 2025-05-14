import os
from flask import Flask, render_template
from flask_cors import CORS
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ───── Carrega variáveis de ambiente ─────
load_dotenv()

# ───── Cria a aplicação Flask ─────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'cliente_interface', 'templates'),
    static_folder=os.path.join(BASE_DIR,  'cliente_interface', 'static')
)
app.secret_key = os.getenv("SECRET_KEY", "fc_super_segura_123")

# ───── Habilita CORS ─────
CORS(app)

# ───── Configurações de upload ─────
app.config['UPLOAD_FOLDER']      = os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25 MB
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ───── Banco de dados ─────
engine = create_engine(f"sqlite:///{os.path.join(BASE_DIR, 'dados_fc.db')}")
Session = sessionmaker(bind=engine)
db_session = Session()

# ───── Flask-Login ─────
login_manager = LoginManager()
login_manager.login_view = 'staff.login'
login_manager.init_app(app)
app.login_manager = login_manager  # expõe o manager no app

from backend.database.models import Usuario

@login_manager.user_loader
def load_user(user_id):
    # pode usar Session.get a partir do SQLAlchemy 1.4+
    return db_session.query(Usuario).get(int(user_id))

# ───── Registra Blueprints ─────
from backend.routes.client_routes    import client_bp
from backend.routes.staff_routes     import staff_bp
from backend.routes.superuser_routes import super_bp

app.register_blueprint(client_bp, url_prefix='/cliente')
app.register_blueprint(staff_bp,  url_prefix='/painel')
app.register_blueprint(super_bp,  url_prefix='/painel')  # área de super-user

# ───── Rota principal do site ─────
@app.route('/')
def home():
    return render_template('index.html')

# ───── Debug: mostra todas as rotas e estáticos ─────
print(app.url_map)

# ───── Executa o servidor ─────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
