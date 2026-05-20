import os
import smtplib
from email.mime.text import MIMEText
import json
import io
import datetime
import dotenv
import random
from fastapi import (
    FastAPI,
    HTTPException,
    Depends,
    UploadFile,
    File,
    Form,
    status,
    BackgroundTasks,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session
from PIL import Image
from database import SessionLocal, get_db, engine, Base
from models import Morador, Encomenda, StatusEncomenda
from fastapi.middleware.cors import CORSMiddleware

# Configurações e inicializações
dotenv.load_dotenv()

# API_KEY = os.getenv("GEMINI_API_KEY")
# if not API_KEY:
#    print("AVISO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")

#if genai:
#    genai.configure(api_key=API_KEY)
#    modelo_ia = genai.GenerativeModel(
#        "gemini-2.5-flash", generation_config={"response_mime_type": "application/json"}
#    )

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shipment Notifier - Condomínio")

# CORS Middleware para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # URLs do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rota 1: Cadastrar Morador e Solicitar Comprovante
class MoradorCreateSchema(BaseModel):
    nome: str
    email: str
    bloco: str
    apartamento: str


@app.post("/cadastrar-morador", status_code=status.HTTP_201_CREATED)
async def cadastrar_morador(
    dados: MoradorCreateSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Verifica se já existe um morador cadastrado com o mesmo bloco e apartamento
    morador_existente = (
        db.query(Morador)
        .filter(Morador.bloco == dados.bloco, Morador.apartamento == dados.apartamento)
        .first()
    )

    if morador_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Já existe um morador cadastrado neste bloco e apartamento.",
        )

    # Cria o morador.
    novo_morador = Morador(
        nome=dados.nome,
        email=dados.email,
        bloco=dados.bloco,
        apartamento=dados.apartamento,
    )

    db.add(novo_morador)
    db.commit()
    db.refresh(novo_morador)  # Pega o ID gerado pelo banco para retornar

    return {
        "mensagem": "Morador cadastrado com sucesso!",
        "morador_id": novo_morador.id,
        "nome": novo_morador.nome,
        "email": novo_morador.email,
    }

# Rota 2: Registrar Encomenda e Notificar Morador
class EncomendaSchema(BaseModel):
    bloco: str
    apartamento: str


@app.post("/registrar-encomenda", status_code=status.HTTP_201_CREATED)
async def registrar_encomenda(
    dados: EncomendaSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # Só permite registrar se o morador estiver validado pela IA
    morador = (
        db.query(Morador)
        .filter(
            Morador.bloco == dados.bloco,
            Morador.apartamento == dados.apartamento,
        )
        .first()
    )

    if not morador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Morador não encontrado ou comprovante de residência ainda não aprovado.",
        )

    codigo_hash = str(random.randint(100000, 999999))

    nova_encomenda = Encomenda(morador_id=morador.id, codigo_retirada=codigo_hash)

    db.add(nova_encomenda)
    db.commit()
    db.refresh(nova_encomenda)

    encomenda_id = nova_encomenda.id

    # Chama a função do Twilio em segundo plano
    background_tasks.add_task(
        send_email,
        encomenda_id,
        morador.nome,
        morador.email
    )

    return {
        "mensagem": "Encomenda registrada com sucesso",
        "morador": morador.nome,
        "codigo": codigo_hash,
        "notificacao": "Notificação sendo enviada para o email do morador.",
    }


class RetiradaSchema(BaseModel):
    codigo_retirada: str


@app.put("/registrar-retirada", status_code=status.HTTP_200_OK)
async def registrar_retirada(dados: RetiradaSchema, db: Session = Depends(get_db)):
    # 1. Busca a encomenda pelo código de retirada
    encomenda = (
        db.query(Encomenda)
        .filter(Encomenda.codigo_retirada == dados.codigo_retirada)
        .first()
    )

    # 2. Validações de segurança
    if not encomenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código de retirada inválido ou inexistente.",
        )

    if encomenda.status == StatusEncomenda.ENTREGUE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Esta encomenda já foi retirada em {encomenda.data_retirada.strftime('%d/%m/%Y às %H:%M')}.",
        )

    # 3. Atualiza o status e a data de retirada
    encomenda.status = StatusEncomenda.ENTREGUE
    encomenda.data_retirada = datetime.datetime.now()

    db.commit()
    db.refresh(encomenda)

    # 4. Retorna confirmação com os dados do morador
    return {
        "status": "sucesso",
        "mensagem": "Retirada confirmada!",
        "entregue_para": encomenda.morador.nome,
        "apartamento": f"{encomenda.morador.apartamento} - Bloco {encomenda.morador.bloco}",
        "horario_retirada": encomenda.data_retirada.strftime("%H:%M:%S"),
    }

# Rota 4: Consultar Moradores e Encomendas
@app.get("/consultar-morador/{bloco}/{apartamento}", status_code=status.HTTP_200_OK)
async def consultar_morador(
    bloco: str, apartamento: str, db: Session = Depends(get_db)
):
    # 1. Busca o morador usando bloco e apartamento
    morador = (
        db.query(Morador)
        .filter(Morador.bloco == bloco, Morador.apartamento == apartamento)
        .first()
    )

    if not morador:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Morador não encontrado para este bloco e apartamento.",
        )

    # 2. Busca encomendas pendentes
    encomendas_pendentes = (
        db.query(Encomenda)
        .filter(Encomenda.morador_id == morador.id, Encomenda.status != "ENTREGUE")
        .all()
    )

    # 3. Formata a resposta
    return {
        "morador": {
            "id": morador.id,
            "nome": morador.nome,
            "whatsapp": morador.whatsapp,
        },
        "total_encomendas_pendentes": len(encomendas_pendentes),
        "encomendas": [
            {"codigo_retirada": enc.codigo_retirada, "status": enc.status}
            for enc in encomendas_pendentes
        ],
    }


# Rota 5: Listar Encomendas Pendentes
@app.get("/encomendas-pendentes", status_code=status.HTTP_200_OK)
async def listar_encomendas_pendentes(db: Session = Depends(get_db)):
    # Faz um JOIN entre Encomenda e Morador para pegar os dados de ambos
    # Filtra apenas as encomendas que não foram entregues
    resultados = (
        db.query(Encomenda, Morador)
        .join(Morador, Encomenda.morador_id == Morador.id)
        .filter(Encomenda.status != "ENTREGUE")
        .all()
    )

    # Se não houver nada pendente
    if not resultados:
        return {
            "mensagem": "A portaria está limpa! Nenhuma encomenda pendente.",
            "total_pendentes": 0,
            "encomendas": [],
        }

    # Monta a lista formatada
    lista_pendentes = []
    for encomenda, morador in resultados:
        lista_pendentes.append(
            {
                "id" : encomenda.id,
                "codigo_retirada": encomenda.codigo_retirada,
                "status": encomenda.status,
                "morador": {
                    "nome": morador.nome,
                    "bloco": morador.bloco,
                    "apartamento": morador.apartamento,
                },
            }
        )

    return {
        "total_pendentes": len(lista_pendentes),
        "encomendas": lista_pendentes
    }

# Rota 6: Listar Moradores (geral)
@app.get("/listar-moradores", status_code=status.HTTP_200_OK)
async def listar_moradores(db: Session = Depends(get_db)):
    moradores = db.query(Morador).all()
    return {
        "total_moradores": len(moradores),
        "moradores": [
            {
                "id": morador.id,
                "nome": morador.nome,
                "email": morador.email,
                "bloco": morador.bloco,
                "apartamento": morador.apartamento,
            }
            for morador in moradores
        ],
    }

def send_email(encomenda_id: int, morador_nome: str, to_email: str):
    if not to_email or not morador_nome or not encomenda_id:
        print("Dados insuficientes para enviar email. Verifique os parâmetros.")
        return

    print(f"Enviando email para {to_email}.")

    db = SessionLocal()  # Cria uma nova sessão para o banco de dados

    try:
        encomenda = db.query(Encomenda).filter(
            Encomenda.id == encomenda_id,
            Encomenda.status != StatusEncomenda.ENTREGUE
        ).first()

        msg = MIMEText(f"Olá {morador_nome},\n\nSua encomenda chegou na portaria! Use o código de retirada para pegar sua encomenda: {encomenda.codigo_retirada}\n\nObrigado!")
        msg["Subject"] = f"{morador_nome}, sua encomenda chegou!"
        msg["From"] = "andresreis.2018@gmail.com"
        msg["To"] = to_email

        # senha de acesso à conta do google
        senha = os.getenv("APP_PASSWORD")

        # envia o email através do servidor SMTP do Gmail
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login("andresreis.2018@gmail.com", senha)
            server.send_message(msg)
    except Exception as e:
        print(f"Erro ao enviar email: {str(e)}")

    db.close()
