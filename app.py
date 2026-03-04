from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from agents.os import agent_os
import os
import json
import re

from agents.data_agent import agent_model,agent_model_conference
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    question: str

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

@app.post("/ask")
async def ask_agent(data: AskRequest):
    tentativas = 0
    result = await agent_model.arun(data.question)
    feedback = await agent_model_conference.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content}""")
    
    print("Feedback do conferencista:", feedback.content)

    feedback_data = parse_feedback(feedback.content)

    while feedback_data.get('passou') == False and tentativas < 3:
        result = await agent_model.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content},
                                      feedback do conferencista: {feedback_data['feedback']}""")

        feedback = await agent_model_conference.arun(f"""Questao do usuario: {data.question},
                                      resposta do assistente: {result.content}""")
        print("Feedback do conferencista:", feedback.content)
        feedback_data = parse_feedback(feedback.content)
        tentativas += 1

    return {"answer": result.content}

@app.get('/health')
async def health():
    return {'status': 'Online'}



# app.mount('/ai', agent_os.get_app())