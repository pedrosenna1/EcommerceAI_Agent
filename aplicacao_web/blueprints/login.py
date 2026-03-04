from flask import Blueprint,redirect,url_for,render_template,request,session
from core.database import SessionLocal
from models.user import User
from sqlalchemy import select
from pwdlib import PasswordHash

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

        pwd_context = PasswordHash.recommended()

        db = SessionLocal()

        result = db.execute(select(User).where(User.email == username.strip().lower()))
        result = result.scalar_one_or_none()
        if not result:
            return render_template('login.html', error='Credenciais inválidas')  # Exibe mensagem de erro
        try:
            pwd_context.verify(password, result.password)
            session['user'] = username.strip().lower()
            return redirect(url_for('dashboard.dashboard'))  # Redireciona para o dashboard após login bem-sucedido
        except Exception as e:
            return render_template('login.html', error='Credenciais inválidas')  # Exibe mensagem de erro

