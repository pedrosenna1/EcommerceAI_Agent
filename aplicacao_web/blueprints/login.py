from flask import Blueprint,redirect,url_for,render_template,request,session,make_response
from core.database import SessionLocal
from models.user import User
from sqlalchemy import select
from pwdlib import PasswordHash
from datetime import datetime, timezone, timedelta
import os
import jwt

bp_login = Blueprint('login',__name__)

@bp_login.route('/')
def redirect_login():
    return redirect(url_for('login.login'))

@bp_login.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        username = request.form.get('usuario')
        password = request.form.get('senha')
    
        if username is None or password is None:
            return render_template('login.html', error='Por favor, preencha todos os campos')

        if len(username) == 0 or len(password) == 0:
            return render_template('login.html', error='Por favor, preencha todos os campos')  # Exibe mensagem de erro

  # Exibe mensagem de erro
        pwd_context = PasswordHash.recommended()

        db = SessionLocal()
        try:
            result = db.execute(select(User).where(User.email == username.strip().lower()))
            result = result.scalar_one_or_none()
        except Exception as e:
            result = None
            db.rollback()
            
        finally:
            db.close()
        if not result:
            return render_template('login.html', error='Credenciais inválidas')  # Exibe mensagem de erro
        try:
            pwd_context.verify(password, result.password)
            session['user'] = username.strip().lower()
            payload = {
                'sub': session['user'],
                'exp': datetime.now(timezone.utc) + timedelta(hours=1)
            }
            jwt_token = jwt.encode(payload,os.getenv('JWT_KEY'),algorithm="HS256")


            cookie = make_response(redirect(url_for('dashboard.dashboard')))
        except:
            return render_template('login.html', error='Credenciais inválidas')  # Exibe mensagem de erro
        cookie.set_cookie(
            key='access_token',
            value=f'Bearer {jwt_token}',
            max_age=(3600),
            secure=False,  # Defina como True se estiver em Produção e usando HTTPS
            httponly=True
        ) # Redireciona para o dashboard após login bem-sucedido
        return cookie
