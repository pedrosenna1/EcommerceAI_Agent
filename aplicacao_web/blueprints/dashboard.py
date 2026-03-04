from flask import Blueprint,redirect,url_for,render_template,request,session

bp_dashboard = Blueprint('dashboard',__name__)


@bp_dashboard.route('/dashboard')
def dashboard():
    # Verifica se o usuário está logado
    if 'user' not in session:
        return redirect(url_for('login.login'))  # Redireciona para a página de login se não estiver logado
    
    # Se estiver logado, renderiza o dashboard
    return render_template('dashboard.html', user=session['user'])