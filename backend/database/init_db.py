import os
import sys

# Adiciona a pasta raiz do projeto ao path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../'))
sys.path.insert(0, project_root)

from sqlalchemy import create_engine
from backend.database.models import Base

def init_db():
    engine = create_engine('sqlite:///dados_fc.db')
    Base.metadata.create_all(engine)
    print('✅ Banco de dados criado com sucesso: dados_fc.db')

if __name__ == '__main__':
    init_db()
