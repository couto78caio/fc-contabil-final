from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Usuario
from werkzeug.security import generate_password_hash

def criar_usuario():
    engine = create_engine('sqlite:///dados_fc.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    print("🧾 Cadastro de novo colaborador")
    username = input("Usuário: ").strip()
    senha = input("Senha: ").strip()

    if not username or not senha:
        print("❌ Usuário e senha não podem estar vazios.")
        return

    existente = session.query(Usuario).filter_by(username=username).first()
    if existente:
        print("⚠️ Este usuário já existe.")
        return

    senha_hash = generate_password_hash(senha)
    usuario = Usuario(username=username, senha=senha_hash)
    session.add(usuario)
    session.commit()
    print(f"✅ Usuário '{username}' criado com sucesso!")

if __name__ == '__main__':
    criar_usuario()