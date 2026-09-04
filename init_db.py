import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    cursor.execute('DROP TABLE IF EXISTS businesses')
    cursor.execute('DROP TABLE IF EXISTS services')

    # Adicionando novos campos: short_description, whatsapp, instagram, address
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS businesses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        rating REAL NOT NULL DEFAULT 5.0,
        distance TEXT DEFAULT '',
        image TEXT DEFAULT '',
        featured BOOLEAN NOT NULL DEFAULT 0,
        about_text TEXT DEFAULT '',
        short_description TEXT DEFAULT '',
        whatsapp TEXT DEFAULT '',
        instagram TEXT DEFAULT '',
        address TEXT DEFAULT '',
        views INTEGER DEFAULT 0,
        plan TEXT DEFAULT 'gratuito',
        status TEXT DEFAULT 'active',
        slug TEXT UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS services (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        price TEXT DEFAULT '',
        FOREIGN KEY (business_id) REFERENCES businesses (id)
    )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados pronto e limpo para empresas reais!")

if __name__ == '__main__':
    init_db()
