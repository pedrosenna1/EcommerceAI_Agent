from core.database import SessionLocal
from pwdlib import PasswordHash 
from models.user import User

def create_user(name: str, email: str, password: str):
    db = SessionLocal()

    pwd_context = PasswordHash.recommended()

    hashed_password = pwd_context.hash(password)

    try:
        pwd_context.verify(password, hashed_password)
        print('Usuário verificado com sucesso')
    except Exception as e:
        print(f"Erro ao verificar senha: {e}")
        return None
    
    new_user = User(name=name.lower(), email=email.lower(), password=hashed_password)
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        db.close()
        print(f"Erro ao criar usuário: {e}")
        return None
    finally:
        db.close()
    return new_user


create_user(name="Pedro", email="pedrotjb7@hotmail.com", password="pedro0206")