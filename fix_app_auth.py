import re

filepath = 'app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

auth_endpoints = """
@app.route('/api/auth/login', methods=['POST'])
def login_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
    conn.close()
    
    if user:
        return jsonify({'success': True, 'business_id': user['business_id']})
    else:
        return jsonify({'success': False, 'message': 'Email ou senha incorretos.'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    business_name = data.get('business_name')
    
    conn = get_db_connection()
    
    # Check if email exists
    existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Email já cadastrado.'}), 400
        
    # Create empty business
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO businesses (name, category, rating, distance, image, featured, about_text)
        VALUES (?, 'Não Definida', 0.0, '0 km', 'https://via.placeholder.com/600', False, '')
    ''', (business_name,))
    
    business_id = cursor.lastrowid
    
    # Create user
    cursor.execute('''
        INSERT INTO users (email, password, business_id)
        VALUES (?, ?, ?)
    ''', (email, password, business_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'business_id': business_id})

# Rotas para renderizar as páginas HTML
"""

content = content.replace('# Rotas para renderizar as páginas HTML', auth_endpoints)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py updated with auth endpoints!")
