import re

filepath = 'app.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

new_endpoint = """
@app.route('/api/businesses/<int:id>/update', methods=['POST'])
def update_business(id):
    data = request.json
    conn = get_db_connection()
    
    # Atualizar os campos básicos da empresa
    conn.execute('''
        UPDATE businesses 
        SET name = ?, category = ?, short_description = ?, about_text = ?, whatsapp = ?, instagram = ?, address = ?
        WHERE id = ?
    ''', (
        data.get('name'), 
        data.get('category'), 
        data.get('short_description'), 
        data.get('about_text'), 
        data.get('whatsapp'), 
        data.get('instagram'), 
        data.get('address'), 
        id
    ))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Perfil atualizado com sucesso!'})

# Rotas para renderizar as páginas HTML
"""

content = content.replace('# Rotas para renderizar as páginas HTML', new_endpoint)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py updated with update endpoint!")
