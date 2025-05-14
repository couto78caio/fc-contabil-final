# criar_superuser.py
from backend.database.models import Usuario, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
import os

# Caminho do banco
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'dados_fc.db')
engine = create_engine(f"sqlite:///{db_path}")
Session = sessionmaker(bind=engine)
db = Session()

# Verifica se já existe algum superusuário
existe = db.query(Usuario).filter_by(is_superuser=True).first()
if existe:
    print("⚠️ Já existe um superusuário cadastrado.")
else:
    # Dados do novo superusuário
    username = "admin"
    senha = "admin123"
    email = "admin@fccontabil.com.br"

    novo_user = Usuario(
        username=username,
        senha=generate_password_hash(senha),
        email=email,
        is_superuser=True
    )
    db.add(novo_user)
    db.commit()
    print(f"✅ Superusuário '{username}' criado com sucesso.")
