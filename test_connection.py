# test_connection_final.py
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

password = os.getenv('SUPABASE_PASS')
print(f"Senha: {password[:3]}...{password[-3:]}")
print(f"Contém @? {'@' in password}")
print(f"Contém !? {'!' in password}")

print("\n" + "="*60)
print("TESTE: Parâmetros individuais (método correto)")
print("="*60)

try:
    conn = psycopg2.connect(
        host="aws-1-sa-east-1.pooler.supabase.com",
        port=5432,
        dbname="postgres",
        user=os.getenv('SUPABASE_USER'),  # ✅ usuário completo
        password=password,  # ✅ senha original (sem encoding)
        connect_timeout=10
    )
    
    print("✅ CONEXÃO BEM-SUCEDIDA!")
    
    cur = conn.cursor()
    
    # Verifica o usuário conectado
    cur.execute("SELECT current_user, current_database();")
    user, db = cur.fetchone()
    print(f"Usuário conectado: {user}")
    print(f"Database: {db}")
    
    # Lista tabelas
    cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema='public' 
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    print(f"\nTabelas públicas encontradas: {len(tables)}")
    for table in tables:
        print(f"  - {table[0]}")
    
    cur.close()
    conn.close()
    print("\n✅ TESTE PASSOU! Use essa configuração!")
    
except psycopg2.OperationalError as e:
    error_msg = str(e)
    
    if "Circuit breaker" in error_msg:
        print("❌ CIRCUIT BREAKER ATIVO!")
        print("⏰ Aguarde 30 minutos antes de tentar novamente")
    elif "password authentication failed" in error_msg:
        print("❌ SENHA INCORRETA!")
        print("\n🔴 AÇÃO NECESSÁRIA:")
        print("1. Vá em: https://app.supabase.com")
        print("2. Settings > Database")
        print("3. Clique em 'Reset database password'")
        print("4. Copie a NOVA senha")
        print("5. Atualize seu .env")
        print("6. Aguarde 30 minutos")
    elif "postgres" in error_msg and os.getenv('SUPABASE_USER').split('.')[-1] not in error_msg:
        print("❌ USUÁRIO INCORRETO!")
        print("O psycopg2 está ignorando o sufixo do usuário")
        print("Isso pode ser um bug na versão do psycopg2")
    else:
        print(f"❌ Erro: {e}")
        
except Exception as e:
    print(f"❌ Erro geral: {e}")