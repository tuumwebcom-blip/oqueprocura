import sqlite3

def force_fix_ratings():
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # O usuário confirmou que NÃO há avaliações reais. 
        # Portanto, vamos apagar qualquer avaliação de teste que possa estar travando a nota em 5.0
        cursor.execute('DELETE FROM reviews')
        
        # Agora, forçamos TODAS as empresas a terem nota 0.0
        cursor.execute('UPDATE businesses SET rating = 0.0')
        
        rows = cursor.rowcount
        conn.commit()
        conn.close()
        print(f"✅ Força Bruta: Foram zeradas as avaliações de {rows} empresa(s)!")
    except Exception as e:
        print(f"Erro ao corrigir avaliações: {e}")

if __name__ == "__main__":
    force_fix_ratings()
