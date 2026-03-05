from fastapi import FastAPI, Request, HTTPException, status
import jwt
import os


def verify_token(request: Request):
    token = request.cookies.get('access_token')
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Token não encontrado.'
        )
    
    if token.startswith('Bearer '):
        token = token.replace('Bearer ', '').strip()
        
    try:
        jwt.decode(
            jwt=token, 
            key=os.getenv('JWT_KEY'), 
            algorithms=['HS256']
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Token expirado.'
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail='Token inválido.'
        )