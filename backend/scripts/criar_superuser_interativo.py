# backend/scripts/criar_superuser_interativo.py
import os
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash
from backend.database.models import Usuario, Base

# Caminho do banco
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, '..', '..', 'dados_fc.db')
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
db = Session()

# Verifica se já existe algum superusuário
existe = db.query(Usuario).filter_by(is_superuser=True).first()
if existe:
    print("\n⚠️ Já existe um superusuário cadastrado.")
    exit()

print("\n🛠️ Criando Superusuário (Admin Principal)")
username = input("Usuário: ").strip()
email    = input("E-mail: ").strip()

while True:
    senha1 = getpass.getpass("Senha: ")
    senha2 = getpass.getpass("Confirmar Senha: ")
    if senha1 != senha2:
        print("❌ As senhas não coincidem. Tente novamente.\n")
    elif len(senha1) < 6:
        print("❌ A senha deve conter pelo menos 6 caracteres.\n")
    else:
        break

# Criação do superusuário
novo_admin = Usuario(
    username=username,
    email=email,
    senha=generate_password_hash(senha1),
    is_superuser=True
)

db.add(novo_admin)
db.commit()
print(f"\n✅ Superusuário '{username}' criado com sucesso!")
