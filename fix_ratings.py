import sqlite3

def fix_ratings():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE businesses 
            SET rating = 0.0 
            WHERE id NOT IN (SELECT DISTINCT business_id FROM reviews)
        ''')
        rows = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"✅ Sucesso! Foram corrigidas as avaliações de {rows} empresa(s) que ainda não tinham notas.")
    except Exception as e:
        print(f"Erro ao corrigir avaliações: {e}")

if __name__ == "__main__":
    fix_ratings()
