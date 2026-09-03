import re
import os

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1: Filter suspended businesses in api_businesses
content = content.replace("SELECT * FROM businesses", "SELECT * FROM businesses WHERE status != 'suspended'")

# Fix 2: Validate empty name in update_business
update_fix = """def update_business(id):
    data = request.json
    name = str(escape(data.get('name', ''))).strip()
    
    if not name:
        return jsonify({'success': False, 'message': 'O nome da empresa não pode ser vazio.'}), 400
        
    category = str(escape(data.get('category', '')))"""
content = re.sub(r"def update_business\(id\):\s+data = request\.json\s+name = str\(escape\(data\.get\('name', ''\)\)\)", update_fix, content)

# Fix 3: Handle potential int conversion errors in add_review
add_review_fix = """def add_review(id):
    data = request.json
    author = str(escape(data.get('author_name', 'Anônimo')))
    
    try:
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        rating = 5
        
    comment = str(escape(data.get('comment', '')))"""
content = re.sub(r"def add_review\(id\):\s+data = request\.json\s+author = str\(escape\(data\.get\('author_name', 'Anônimo'\)\)\)\s+rating = int\(data\.get\('rating', 5\)\)\s+comment = str\(escape\(data\.get\('comment', ''\)\)\)", add_review_fix, content)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Auditoria e correções aplicadas no backend.")
