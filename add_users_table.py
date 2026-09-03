import sqlite3

def add_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        business_id INTEGER,
        FOREIGN KEY (business_id) REFERENCES businesses (id)
    )
    ''')

    # Inserir um usuário padrão para testarmos o login
    try:
        cursor.execute('''
        INSERT INTO users (email, password, business_id)
        VALUES ('admin@lentelclara.com', 'senha123', 1)
        ''')
    except sqlite3.IntegrityError:
        pass # Usuario ja existe

    conn.commit()
    conn.close()
    print("Tabela de usuários criada e usuário padrão inserido!")

if __name__ == '__main__':
    add_users()
