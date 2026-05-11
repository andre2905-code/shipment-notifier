from database import SessionLocal
from models import Morador

def atualizar_whatsapp(morador_id: int, novo_numero: str):
    # Abre a conexão com o banco
    db = SessionLocal()
    try:
        # Busca o morador pelo ID
        morador = db.query(Morador).filter(Morador.id == morador_id).first()
        
        if not morador:
            print(f"🔴 Erro: Morador com ID {morador_id} não encontrado no banco de dados.")
            return

        # Atualiza o número
        numero_antigo = morador.whatsapp
        morador.whatsapp = novo_numero
        
        # Salva as alterações (commit)
        db.commit()
        
        print(f"✅ SUCESSO!")
        print(f"Morador: {morador.nome} (Apt {morador.apartamento} / Bloco {morador.bloco})")
        print(f"Número antigo: {numero_antigo}")
        print(f"Número novo: {morador.whatsapp}")

    except Exception as e:
        print(f"🔴 Erro inesperado ao acessar o banco: {str(e)}")
        db.rollback() # Desfaz qualquer alteração que deu erro pela metade
    finally:
        db.close() # Fecha a conexão

if __name__ == "__main__":
    # ==========================================
    # ⚠️ EDITE ESTES VALORES ANTES DE RODAR
    # ==========================================
    
    # Se você acabou de criar o banco, seu morador provavelmente tem o ID 1
    ID_DO_MORADOR = 1  
    
    # Coloque o número exato que você usou para mandar o código do Twilio
    NOVO_TELEFONE = "+5511952786261" 
    
    print("Iniciando atualização...")
    atualizar_whatsapp(ID_DO_MORADOR, NOVO_TELEFONE)