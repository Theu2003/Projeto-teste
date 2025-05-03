import sqlite3

def list_schedules():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM schedules')
        schedules = cursor.fetchall()
        if schedules:
            print("Agendamentos salvos:")
            for schedule in schedules:
                print(schedule)
        else:
            print("Nenhum agendamento encontrado.")

if __name__ == '__main__':
    list_schedules()