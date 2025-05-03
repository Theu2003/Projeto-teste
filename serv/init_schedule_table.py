import sqlite3

def init_schedule_table():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        # Cria a tabela de agendamentos, se não existir
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                address TEXT NOT NULL,
                description TEXT,
                quantity REAL,
                date TEXT NOT NULL,
                time TEXT NOT NULL
            )
        ''')
        conn.commit()
        print("Tabela de agendamentos criada com sucesso.")

if __name__ == '__main__':
    init_schedule_table()