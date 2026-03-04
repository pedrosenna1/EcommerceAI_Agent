from flask import Flask,jsonify,redirect,url_for,request,session
from blueprints.login import bp_login
from blueprints.dashboard import bp_dashboard

app = Flask(__name__)

app.secret_key = '123435246546521341233215454'  # Substitua por uma chave secreta real para segurança e coloque no .env
app.permanent_session_lifetime = 3600  # Tempo de expiração da sessão em segundos (1 hora)

app.register_blueprint(blueprint=bp_login)
app.register_blueprint(blueprint=bp_dashboard)


if __name__ == "__main__":
    app.run(debug=True)