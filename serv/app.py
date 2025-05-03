from flask import Flask, request, jsonify, redirect, url_for, send_from_directory, session
import sqlite3
from urllib.parse import parse_qs
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, static_folder='c:/Users/mateu/OneDrive/Documentos/GitHub/Projeto-teste', static_url_path='')

# Configuração da chave secreta para sessões
app.secret_key = 'sua_chave_secreta_aqui'

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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                address TEXT NOT NULL,
                description TEXT,
                quantity INTEGER,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            )
        ''')
        conn.commit()

# Configuração para servir arquivos estáticos
@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(os.path.dirname(__file__), filename)

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

    hashed_password = generate_password_hash(password)

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        return redirect('/index.html')  # Redireciona para a página inicial após o cadastro
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
        cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()

    if user and check_password_hash(user[0], password):
        session['user'] = username  # Armazena o usuário na sessão
        return redirect('/index.html')
    else:
        return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)  # Remove o usuário da sessão
    return redirect('/index.html')

@app.route('/schedule', methods=['POST'])
def create_schedule():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized. Please log in to schedule.'}), 401

    data = request.get_json()
    app.logger.info(f"Dados recebidos para agendamento: {data}")

    schedule_type = data.get('type')
    address = data.get('address')
    description = data.get('description')
    quantity = data.get('quantity')
    date = data.get('date')
    time = data.get('time')

    if not all([schedule_type, address, date, time]):
        app.logger.warning("Campos obrigatórios ausentes no agendamento.")
        return jsonify({'error': 'Todos os campos obrigatórios devem ser preenchidos.'}), 400

    try:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO schedules (type, address, description, quantity, date, time)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (schedule_type, address, description, quantity, date, time))
            conn.commit()
        app.logger.info("Agendamento armazenado com sucesso no banco de dados.")
        return jsonify({'message': 'Agendamento criado com sucesso!'}), 201
    except Exception as e:
        app.logger.error(f"Erro ao armazenar agendamento: {e}")
        return jsonify({'error': 'Erro ao criar agendamento.'}), 500

@app.route('/schedules', methods=['GET'])
def list_schedules():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules')
        schedules = cursor.fetchall()

    return jsonify(schedules), 200

@app.route('/')
def index():
    return redirect('/index.html')  # Redireciona para o arquivo index.html

if __name__ == '__main__':
    init_db()
    app.run(debug=True)