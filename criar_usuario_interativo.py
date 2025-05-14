# criar_usuario_interativo.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Usuario
from werkzeug.security import generate_password_hash
import os

def criar_usuario():
    engine = create_engine('sqlite:///dados_fc.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    print("👤 Cadastro de novo colaborador\n")

    username = input("Usuário: ").strip()
    email    = input("Email: ").strip()
    senha    = input("Senha: ").strip()
    is_super = input("Este usuário é um superusuário? (s/n): ").strip().lower() == "s"

    if not username or not senha:
        print("❌ Usuário e senha são obrigatórios.")
        return

    if session.query(Usuario).filter_by(username=username).first():
        print("⚠️ Usuário já existente.")
        return

    senha_hash = generate_password_hash(senha)
    novo = Usuario(
        username=username,
        email=email,
        senha=senha_hash,
        is_superuser=is_super
    )
    session.add(novo)
    session.commit()
    print(f"✅ Usuário '{username}' criado com sucesso. Superusuário: {'Sim' if is_super else 'Não'}")

if __name__ == '__main__':
    criar_usuario()
