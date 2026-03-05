from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, status, Request, Depends, HTTPException,responses
from fastapi.middleware.cors import CORSMiddleware
from agents.os import agent_os
import os
import json
import re
import time
import jwt

from agents.data_agent import agent_model,agent_model_conference
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5000", "http://localhost:5000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str

# Rate limit: 5 requisições por minuto por IP
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # segundos
_rate_limit_store: dict[str, list[float]] = {}
TRUSTED_PROXIES = {
    ip.strip() for ip in os.getenv("TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if ip.strip()
}


def get_client_ip(request: Request) -> str:
    peer_ip = request.client.host if request.client and request.client.host else "unknown"

    # Só confia em headers quando a conexão veio de um proxy confiável
    if peer_ip in TRUSTED_PROXIES:
        cf_ip = request.headers.get("cf-connecting-ip")
        if cf_ip:
            return cf_ip.strip()

        xff = request.headers.get("x-forwarded-for")
        if xff:
            return xff.split(",")[0].strip()

        x_real_ip = request.headers.get("x-real-ip")
        if x_real_ip:
            return x_real_ip.strip()

    return peer_ip

def rate_limit(request: Request):
    client_ip = get_client_ip(request)
    now = time.time()

    # Inicializa lista de timestamps do IP
    if client_ip not in _rate_limit_store:
        _rate_limit_store[client_ip] = []

    # Remove timestamps fora da janela
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]

    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Limite de requisições excedido. Tente novamente em alguns instantes."
        )

    _rate_limit_store[client_ip].append(now)

def parse_feedback(content: str) -> dict:
    """Extrai o JSON do content, mesmo que venha com markdown ou texto extra."""
    try:
        # Tenta direto
        return json.loads(content)
    except Exception:
        # Tenta extrair JSON de dentro de bloco markdown ```...```
        match = re.search(r'\{.*?\}', content, re.DOTALL)
        if match:
            return json.loads(match.group())
        # Se não conseguir parsear, considera que passou para não travar
        return {'passou': True, 'feedback': content}

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
    
@app.get('/',status_code=status.HTTP_200_OK)
async def root():
    return {
        "message": "Agno Assist API está rodando!",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "ask": "/ask (POST)"
        }
    }

async def process(data: AskRequest):
    yield json.dumps({"status": "processing", "message": "Processando sua solicitação..."}) + "\n"
    tentativas = 0
    result = await agent_model.arun(data.question)

    yield json.dumps({"status": "processing", "message": "Validando resposta..."}) + "\n"
    feedback = await agent_model_conference.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content}""")
    
    # print("Feedback do conferencista:", feedback.content)

    feedback_data = parse_feedback(feedback.content)

    while feedback_data.get('passou') == False and tentativas < 3:
        yield json.dumps({"status": "processing", "message": f"Refinando resposta (tentativa {tentativas + 1})..."}) + "\n"
        result = await agent_model.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content},
                                      feedback do conferencista: {feedback_data['feedback']}""")

        feedback = await agent_model_conference.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content}""")
        # print("Feedback do conferencista:", feedback.content)
        feedback_data = parse_feedback(feedback.content)
        tentativas += 1

    yield json.dumps({"status": "done", "answer": result.content}) + "\n"


@app.post("/ask",dependencies=[Depends(rate_limit),Depends(verify_token)])
async def ask_agent(data: AskRequest):
    return responses.StreamingResponse(process(data), media_type="application/x-ndjson")

@app.get('/health')
async def health():
    return {'status': 'Online'}


# app.mount('/ai', agent_os.get_app())