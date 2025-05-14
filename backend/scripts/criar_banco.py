# criar_banco.py
from backend.database.models import Base
from sqlalchemy import create_engine
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, 'dados_fc.db')
engine = create_engine(f"sqlite:///{db_path}")

# Criação das tabelas
Base.metadata.create_all(engine)
print("✅ Banco de dados criado com sucesso.")
