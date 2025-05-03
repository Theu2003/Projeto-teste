import sqlite3

def clear_users():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        # Certifica-se de que a tabela 'users' existe antes de tentar apagar os dados
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('DELETE FROM users')
        conn.commit()
        print("Todos os dados da tabela 'users' foram apagados com sucesso.")

if __name__ == '__main__':
    clear_users()