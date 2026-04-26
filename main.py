import os
import json
import io
import datetime
import google.generativeai as genai
import dotenv
import random
from twilio.rest import Client
from twilio.http.async_http_client import AsyncTwilioHttpClient
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
from PIL import Image
from database import get_db, engine, Base
from models import Morador, Encomenda

# Configurações e inicializações
dotenv.load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("AVISO: GEMINI_API_KEY não encontrada nas variáveis de ambiente.")

if genai:
    genai.configure(api_key=API_KEY)
    modelo_ia = genai.GenerativeModel(
        'gemini-2.5-flash',
        generation_config={"response_mime_type": "application/json"}
    )

# Cria as tabelas se não existirem
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Shipment Notifier - Condomínio")


# Rota 1: Cadastrar Morador e Solicitar Comprovante
class MoradorCreateSchema(BaseModel):
    nome: str
    whatsapp: str
    bloco: str
    apartamento: str

@app.post("/cadastrar-morador", status_code=status.HTTP_201_CREATED)
async def cadastrar_morador(
    dados: MoradorCreateSchema, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Verifica se já existe um morador cadastrado com o mesmo bloco e apartamento
    morador_existente = db.query(Morador).filter(
        Morador.bloco == dados.bloco,
        Morador.apartamento == dados.apartamento
    ).first()
    
    if morador_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Já existe um morador cadastrado neste bloco e apartamento."
        )

    # Cria o morador. O status_validacao vai como 'PENDENTE' por padrão (configurado no models.py)
    novo_morador = Morador(
        nome=dados.nome,
        whatsapp=dados.whatsapp,
        bloco=dados.bloco,
        apartamento=dados.apartamento
    )
    
    db.add(novo_morador)
    db.commit()
    db.refresh(novo_morador) # Pega o ID gerado pelo banco para retornar
    
    # Dispara a mensagem de boas-vindas pedindo o comprovante
    background_tasks.add_task(
        solicitar_comprovante_whatsapp,
        novo_morador.nome,
        novo_morador.whatsapp
    )
    
    return {
        "mensagem": "Morador pré-cadastrado com sucesso!",
        "morador_id": novo_morador.id,
        "status": novo_morador.status_validacao,
        "notificacao": "Solicitação de comprovante enviada via WhatsApp."
    }


# Rota 2: Validar Comprovante de Residência com IA
@app.post("/validar-comprovante", status_code=status.HTTP_200_OK)
async def validar_comprovante(
    morador_id: int = Form(...), 
    comprovante: UploadFile = File(...), 
    db: Session = Depends(get_db)
):
    # Verifica se o morador existe
    morador = db.query(Morador).filter(Morador.id == morador_id).first()
    if not morador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Morador não encontrado.")

    # Prepara a imagem e gerencia recursos da memória
    try:
        conteudo_imagem = await comprovante.read()
        imagem_pil = Image.open(io.BytesIO(conteudo_imagem))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Não foi possível ler a imagem. Certifique-se de que é um arquivo válido (JPG/PNG)."
        )
    finally:
        await comprovante.close() # Libera o arquivo enviado da memória do servidor

    # Prompt para a IA
    endereco_oficial = "Rua das Palmeiras, 1500, Araçatuba - SP" 
    
    prompt = f"""
    Você é um auditor de condomínio. Analise o comprovante de residência na imagem.
    O endereço oficial do nosso condomínio é: {endereco_oficial}.
    
    Regras:
    1. Extraia o endereço legível na imagem.
    2. Compare com o endereço oficial (ignore diferenças de CEP ou abreviações como R. ou Rua).
    3. Retorne EXATAMENTE este esquema JSON:
    {{
        "endereco_encontrado": "o endereço que você leu",
        "mesmo_condominio": true (se bater) ou false (se for diferente),
        "motivo": "N/A se true, ou a explicação do porquê foi negado se false"
    }}
    """

    # Chamada Assíncrona
    try:
        if not genai:
            raise Exception("Biblioteca do Google Gemini não instalada.")
            
        resposta_ia = await modelo_ia.generate_content_async([prompt, imagem_pil])
        resultado = json.loads(resposta_ia.text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail=f"Erro na comunicação com a IA: {str(e)}"
        )

    # Processamento do Resultado e Atualização do Banco
    is_valido = resultado.get("mesmo_condominio", False)
    
    if is_valido:
        morador.status_validacao = 'APROVADO'
        msg_sucesso = "Comprovante validado automaticamente pela IA!"
        status_final = "sucesso"
    else:
        morador.status_validacao = 'REJEITADO'
        msg_sucesso = "O endereço não confere com os registros do condomínio."
        status_final = "negado"

    db.commit()
    
    return {
        "status": status_final,
        "mensagem": msg_sucesso,
        "dados_ia": resultado
    }


# Rota 3: Registrar Encomenda e Notificar Morador
class EncomendaSchema(BaseModel):
    bloco: str
    apartamento: str

@app.post("/registrar-encomenda", status_code=status.HTTP_201_CREATED)
async def registrar_encomenda(
    dados: EncomendaSchema, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Só permite registrar se o morador estiver validado pela IA
    morador = db.query(Morador).filter(
        Morador.bloco == dados.bloco,
        Morador.apartamento == dados.apartamento,
        Morador.status_validacao == 'APROVADO'
    ).first()
    
    if not morador:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Morador não encontrado ou comprovante de residência ainda não aprovado."
        )
    
    codigo_hash = str(random.randint(100000, 999999))
    
    nova_encomenda = Encomenda(
        morador_id=morador.id, 
        codigo_retirada=codigo_hash
    )
    
    db.add(nova_encomenda)
    db.commit()
    
    # Chama a função do Twilio em segundo plano
    background_tasks.add_task(
        notificar_morador_whatsapp,
        morador.nome,
        morador.whatsapp,
        codigo_hash
    )
    
    return {
        "mensagem": "Encomenda registrada com sucesso", 
        "morador": morador.nome, 
        "codigo": codigo_hash,
        "notificacao": "Sendo enviada no WhatsApp em segundo plano..."
    }

class RetiradaSchema(BaseModel):
    codigo_retirada: str

@app.put("/registrar-retirada", status_code=status.HTTP_200_OK)
async def registrar_retirada(dados: RetiradaSchema, db: Session = Depends(get_db)):
    # 1. Busca a encomenda pelo código de retirada
    encomenda = db.query(Encomenda).filter(
        Encomenda.codigo_retirada == dados.codigo_retirada
    ).first()

    # 2. Validações de segurança
    if not encomenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Código de retirada inválido ou inexistente."
        )

    if encomenda.status == 'ENTREGUE':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Esta encomenda já foi retirada em {encomenda.data_retirada.strftime('%d/%m/%Y às %H:%M')}."
        )

    # 3. Atualiza o status e a data de retirada
    encomenda.status = 'ENTREGUE'
    encomenda.data_retirada = datetime.datetime.now()

    db.commit()
    db.refresh(encomenda)

    # 4. Retorna confirmação com os dados do morador
    return {
        "status": "sucesso",
        "mensagem": "Retirada confirmada!",
        "entregue_para": encomenda.morador.nome,
        "apartamento": f"{encomenda.morador.apartamento} - Bloco {encomenda.morador.bloco}",
        "horario_retirada": encomenda.data_retirada.strftime("%H:%M:%S")
    }


async def notificar_morador_whatsapp(nome: str, telefone: str, codigo: str):
    """
    Função que usa a API do Twilio para enviar o WhatsApp em segundo plano.
    """
    if not telefone:
        print(f"🟡 [AVISO] Morador {nome} não possui telefone cadastrado.")
        return

    # Formatação do telefone
    telefone_formatado = telefone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if not telefone_formatado.startswith("55"):
        telefone_formatado = f"55{telefone_formatado}"

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    if not account_sid or not auth_token:
        print("🔴 [ERRO] Credenciais do Twilio não encontradas no .env")
        return

    mensagem = (
        f"Olá, *{nome}*! 📦\n\n"
        f"Você tem uma nova encomenda aguardando na portaria.\n"
        f"Apresente este código para retirar: *{codigo}*"
    )

    try:
        motor_assincrono = AsyncTwilioHttpClient()
        client = Client(account_sid, auth_token, http_client=motor_assincrono)
            
        # Dispara a mensagem de forma assíncrona
        message = await client.messages.create_async(
            from_="whatsapp:+14155238886", # Verficar número do Twilio para WhatsApp
            body=mensagem,
            to=f"whatsapp:+{telefone_formatado}"
        )
        print(f"🟢 [TWILIO ENVIADO] Mensagem processada! SID: {message.sid}")
        
    except Exception as e:
        print(f"🔴 [ERRO TWILIO] Falha ao enviar a mensagem: {str(e)}")


async def solicitar_comprovante_whatsapp(nome: str, telefone: str):
    """
    Função em segundo plano para dar boas-vindas e pedir o comprovante.
    """
    if not telefone:
        return

    # Formatação do telefone
    telefone_formatado = telefone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
    if not telefone_formatado.startswith("55"):
        telefone_formatado = f"55{telefone_formatado}"

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")

    mensagem = (
        f"Olá, *{nome}*! Bem-vindo(a) ao sistema de Encomendas do Condomínio. 🏢\n\n"
        f"Seu pré-cadastro foi realizado na portaria.\n"
        f"Para liberarmos o recebimento de suas encomendas e notificações por aqui, "
        f"por favor, envie uma foto nítida do seu *comprovante de residência*."
    )

    try:
        motor_assincrono = AsyncTwilioHttpClient()
        client = Client(account_sid, auth_token, http_client=motor_assincrono)
            
        message = await client.messages.create_async(
            from_="whatsapp:+14155238886", # Verficar número do Twilio para WhatsApp
            body=mensagem,
            to=f"whatsapp:+{telefone_formatado}"
        )
        print(f"🟢 [TWILIO BOAS-VINDAS] Enviado para {nome}! SID: {message.sid}")
        
    except Exception as e:
        print(f"🔴 [ERRO TWILIO] Falha ao solicitar comprovante: {str(e)}")