from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.os import AgentOS
from agno.tools.postgres import PostgresTools
from agno.models.openai import OpenAIResponses
import os
import psycopg2
from dotenv import load_dotenv
from agno.tools import tool
from agents.regras_negocio import REGRAS_DE_NEGOCIO

load_dotenv()

DB_CONFIG = {
    'host': 'aws-1-sa-east-1.pooler.supabase.com',
    'port': 5432,
    'dbname': 'postgres',
    'user': os.getenv('SUPABASE_USER'),
    'password': os.getenv('SUPABASE_PASS'),
    'connect_timeout': 10
}

db = SqliteDb(db_file="memory.db")

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=DB_CONFIG['host'],
    port=DB_CONFIG['port'],
    db_name=DB_CONFIG['dbname'],
    user=DB_CONFIG['user'],
    password=DB_CONFIG['password']
)


@tool
def list_tables():
    """Lista todas as tabelas públicas do banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema='public'
            ORDER BY table_name
        """)
        
        tables = cur.fetchall()
        cur.close()
        conn.close()
        
        # Retorna lista de nomes de tabelas
        return [t[0] for t in tables]
        
    except Exception as e:
        return f"Erro ao listar tabelas: {str(e)}"

@tool
def get_schema(table_name: str):
    """Retorna o schema (colunas e tipos) de uma tabela específica"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                column_name, 
                data_type, 
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_name = %s 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """, (table_name,))
        
        schema = cur.fetchall()
        cur.close()
        conn.close()
        
        if not schema:
            return f"Tabela '{table_name}' não encontrada"
        
        # Formata o resultado
        result = []
        for col in schema:
            result.append({
                'coluna': col[0],
                'tipo': col[1],
                'permite_null': col[2],
                'default': col[3]
            })
        
        return result
        
    except Exception as e:
        return f"Erro ao buscar schema: {str(e)}"


agent_model = Agent(
    name="Agno Assist",
    db=db,                                              # session storage
    model=OpenAIResponses(id="gpt-5.2"),                     # session storage
    tools=[postgres_tools,list_tables,get_schema],  # Agno docs via MCP
    add_datetime_to_context=True,
    add_history_to_context=True,                         # include past runs
    num_history_runs=3,                                  # last 3 conversations
    markdown=True,
    instructions=["Quando tiver dúvida sobre quais tabelas/colunas usar, chame list_tables e get_schema antes de montar a query.","""Você como especialista em banco de dados e analise de dados,
    deve fazer consultas otimizadas ao banco de dados usando sua tool
    e trazer respostas para o que foi perguntado.""",
    "Pense sempre na melhor maneira de trazer a resposta para o usuario, usando o mínimo de tabelas e colunas possíveis, para evitar respostas confusas e muito extensas.",
    "Nem todas as respostas precisam ser em formato de tabela, as vezes o melhor é trazer uma resposta direta, sem tabelas, usando apenas texto, para facilitar a leitura do usuário final.",
    "Os valores devem vir ja tratados, ou seja, se for um valor, traga com os dados com pontuação de milhares e decimais, para facilitar a leitura do usuário final.",
    "Sempre analise todas as tabelas e seus schemas antes de executar uma query, para evitar erros e trazer a resposta mais otimizada possível.",
    "Sua resposta deve ser apenas o que foi pedido, evite trazer informações adicionais que não foram solicitadas, para evitar respostas confusas e muito extensas.",
    "Regras de negócio:\n" + "\n".join(f"- {r}" for r in REGRAS_DE_NEGOCIO)]
)

agent_model_conference = Agent(
    name="Agno Assist Conference",
    model=OpenAIResponses(id="gpt-5.2"),
    tools=[postgres_tools,list_tables,get_schema],
    add_datetime_to_context=True,
    add_history_to_context=True,
    num_history_runs=3,
    markdown=False,
    instructions=["""Seu papel é conferir o dado passado pelo agente anterior e verificar se ele aplicou corretamente as instruções
                   ,se a query dele está correta e atende ao pedido feito (Se não está deixando de fora nenhuma variavel que vá impactar o resultado), e se seguiu as boas práticas na consulta ao banco de dados.""",
                   "Sua resposta deve ser SEMPRE um JSON puro (SEM markdown, SEM código, SEM texto adicional, APENAS o JSON) respeitando exatamente esse formato: {\"passou\": true, \"feedback\": \"motivo\"} - onde passou é um booleano indicando se o resultado está correto ou não, e feedback é uma string explicando o motivo.",
                   "Regras de negócio:\n" + "\n".join(f"- {r}" for r in REGRAS_DE_NEGOCIO)
                   ]
)
