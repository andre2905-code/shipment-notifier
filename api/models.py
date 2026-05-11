import enum
from sqlalchemy import Column, Integer, String, Enum, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

# --- ENUMS NATIVOS DO PYTHON ---
# Herdam apenas de (str, enum.Enum) para funcionarem corretamente no Python e no Banco
class StatusValidacao(str, enum.Enum):
    PENDENTE = 'PENDENTE'
    APROVADO = 'APROVADO'
    REJEITADO = 'REJEITADO'

class StatusEncomenda(str, enum.Enum):
    AGUARDANDO = 'AGUARDANDO'
    ENTREGUE = 'ENTREGUE'

# --- MODELOS (TABELAS) ---
class Morador(Base):
    __tablename__ = "moradores"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100))
    whatsapp = Column(String(20))
    bloco = Column(String(10))
    apartamento = Column(String(10))
    
    # Utilizando o Enum do SQLAlchemy passando a classe do Python
    status_validacao = Column(Enum(StatusValidacao), default=StatusValidacao.PENDENTE)
    data_cadastro = Column(DateTime(timezone=True), server_default=func.now())

    # RELACIONAMENTO: Permite acessar lista de encomendas e apaga os pacotes se o morador for deletado
    encomendas = relationship("Encomenda", back_populates="morador", cascade="all, delete-orphan")


class Encomenda(Base):
    __tablename__ = "encomendas"

    id = Column(Integer, primary_key=True, index=True)
    morador_id = Column(Integer, ForeignKey("moradores.id"))
    
    # Utilizando o Enum do SQLAlchemy passando a classe do Python
    status = Column(Enum(StatusEncomenda), default=StatusEncomenda.AGUARDANDO)
    codigo_retirada = Column(String(64), unique=True)
    data_recebimento = Column(DateTime(timezone=True), server_default=func.now())
    data_retirada = Column(DateTime(timezone=True), onupdate=func.now())

    # RELACIONAMENTO: Permite acessar os dados do morador dono da encomenda
    morador = relationship("Morador", back_populates="encomendas")