from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from flask_login import UserMixin
import datetime

Base = declarative_base()

class Cliente(Base):
    __tablename__ = 'clientes'
    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(14), unique=True, nullable=False, index=True)
    razao_social = Column(String(100), nullable=False)

    documentos = relationship("DocumentoEnviado", back_populates="cliente")

class DocumentoEnviado(Base):
    __tablename__ = 'documentos_enviados'
    id = Column(Integer, primary_key=True, index=True)
    cliente_id = Column(Integer, ForeignKey('clientes.id'), nullable=False)
    mes_referencia = Column(String(7), nullable=False) # Formato YYYY-MM
    modalidade = Column(String(50), nullable=False)
    nome_arquivo = Column(String(255), nullable=False)
    caminho_arquivo = Column(String(512), nullable=False)
    protocolo = Column(String(100), unique=True, nullable=False)
    data_envio = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    cliente = relationship("Cliente", back_populates="documentos")

class Usuario(UserMixin, Base):
    __tablename__ = 'usuarios'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    senha = Column(String(255), nullable=False) # Hash da senha
    email = Column(String(100), unique=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

# O modelo 'Documento' original parecia ser uma tentativa inicial para 'DocumentoEnviado'.
# Se não estiver sendo usado em nenhum outro lugar e 'DocumentoEnviado' o substitui,
# ele pode ser removido ou comentado para evitar confusão.
# class Documento(Base):
#     __tablename__ = 'documentos'
#     id = Column(Integer, primary_key=True)
#     cnpj = Column(String, nullable=False)
#     mes_referencia = Column(String, nullable=False)
#     modalidade = Column(String, nullable=False)
#     nome_arquivo = Column(String, nullable=False)
#     caminho = Column(String, nullable=False)

