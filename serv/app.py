from flask import Flask, request, jsonify, redirect, url_for, send_from_directory
import sqlite3
from urllib.parse import parse_qs
import os
import jwt
import datetime
from functools import wraps
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__, static_folder='../', static_url_path='')
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'

def init_db():
    # Inicializa o banco de dados e cria a tabela de usuários, se não existir
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

# Configuração para servir arquivos estáticos
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

# Função para verificar o token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except:
            return jsonify({'error': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated

def is_valid_email(email):
    # Verifica se o e-mail está no formato correto
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def is_strong_password(password):
    # Verifica se a senha tem pelo menos 8 caracteres, incluindo letras maiúsculas, minúsculas e números
    return len(password) >= 8 and any(c.islower() for c in password) and any(c.isupper() for c in password) and any(c.isdigit() for c in password)

def send_reset_email(email, token):
    sender_email = "seu_email@gmail.com"  # Substitua pelo seu e-mail
    sender_password = "sua_senha"  # Substitua pela sua senha
    subject = "Redefinição de Senha"
    
    # Corpo do e-mail
    body = f"""
    Olá,

    Você solicitou a redefinição de sua senha. Clique no link abaixo para redefini-la:
    http://127.0.0.1:5000/reset_password?token={token}

    Se você não solicitou isso, ignore este e-mail.
    """

    # Configuração do e-mail
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Envia o e-mail
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("E-mail de redefinição enviado com sucesso.")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

@app.route('/register', methods=['POST'])
def register():
    if request.content_type == 'application/x-www-form-urlencoded':
        data = parse_qs(request.get_data(as_text=True))
        username = data.get('username', [None])[0]
        password = data.get('password', [None])[0]
    else:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if not is_valid_email(username):
        return jsonify({'error': 'Invalid email format'}), 400

    if not is_strong_password(password):
        return jsonify({'error': 'Password must be at least 8 characters long and include uppercase, lowercase, and numbers'}), 400

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        return redirect('/index.html')  # Redireciona para o arquivo index.html após o cadastro
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 409

@app.route('/login', methods=['POST'])
def login():
    if request.content_type == 'application/x-www-form-urlencoded':
        data = parse_qs(request.get_data(as_text=True))
        username = data.get('username', [None])[0]
        password = data.get('password', [None])[0]
    else:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
        user = cursor.fetchone()

    if user:
        token = jwt.encode({'user': username, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (email,))
        user = cursor.fetchone()

    if user:
        token = jwt.encode({'user': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'], algorithm='HS256')
        send_reset_email(email, token)
        return jsonify({'message': 'Password reset email sent'}), 200
    else:
        return jsonify({'error': 'Email not found'}), 404

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('new_password')

    if not token or not new_password:
        return jsonify({'error': 'Token and new password are required'}), 400

    try:
        decoded = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        email = decoded['user']
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token has expired'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 400

    if not is_strong_password(new_password):
        return jsonify({'error': 'Password must be at least 8 characters long and include uppercase, lowercase, and numbers'}), 400

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET password = ? WHERE username = ?', (new_password, email))
        conn.commit()

    return jsonify({'message': 'Password has been reset successfully'}), 200

@app.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'This is a protected route accessible only with a valid token.'})

@app.route('/admin/users', methods=['GET'])
@token_required
def list_users():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, username FROM users')
        users = cursor.fetchall()
    return jsonify(users), 200

@app.route('/admin/users/<int:user_id>', methods=['DELETE'])
@token_required
def delete_user(user_id):
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
    return jsonify({'message': 'User deleted successfully'}), 200

@app.route('/')
def index():
    return redirect('/index.html')  # Redireciona para o arquivo index.html

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')