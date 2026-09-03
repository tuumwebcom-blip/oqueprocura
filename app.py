from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from functools import wraps
import uuid

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Decorators de Segurança
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') == 'superadmin':
            return f(*args, **kwargs)
        req_id = kwargs.get('id')
        if req_id is not None:
            if session.get('business_id') != req_id:
                return jsonify({'success': False, 'message': 'Acesso negado (IDOR).'}), 403
        elif not session.get('user_id'):
            return jsonify({'success': False, 'message': 'Não autenticado.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('role') != 'superadmin':
            return jsonify({'success': False, 'message': 'Acesso restrito ao Super Admin.'}), 403
        return f(*args, **kwargs)
    return decorated_function


# Configurações de Upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024 # Máximo de 10MB por foto

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Limites por plano
PLAN_LIMITS = {
    'gratuito': {
        'photos': 1,
        'services': 1,
        'maps': False,
        'verified': False,
        'featured_home': False,
        'analytics': False,
    },
    'basico': {
        'photos': 5,
        'services': 5,
        'maps': False,
        'verified': False,
        'featured_home': False,
        'analytics': False,
    },
    'pro': {
        'photos': 20,
        'services': 20,
        'maps': True,
        'verified': False,
        'featured_home': False,
        'analytics': False,
    },
    'elite': {
        'photos': 100,
        'services': None,  # None = ilimitado
        'maps': True,
        'verified': True,
        'featured_home': True,
        'analytics': True,
    }
}

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_user_plan(business_id):
    conn = get_db_connection()
    user = conn.execute('SELECT plan FROM users WHERE business_id = ?', (business_id,)).fetchone()
    conn.close()
    return user['plan'] if user else 'basico'

# ============================================================
# API — Listagem e Detalhe de Empresas
# ============================================================

@app.route('/api/businesses')
def api_businesses():
    conn = get_db_connection()
    businesses = conn.execute('SELECT * FROM businesses WHERE status != 'suspended'').fetchall()
    conn.close()
    return jsonify([dict(b) for b in businesses])

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip().lower()
    category = request.args.get('category', '').strip().lower()
    local = request.args.get('local', '').strip().lower()
    
    conn = get_db_connection()
    
    sql = '''
        SELECT b.*, u.plan 
        FROM businesses b
        LEFT JOIN users u ON b.id = u.business_id
        WHERE b.status != 'suspended'
    '''
    params = []
    
    if query:
        sql += ' AND (LOWER(b.name) LIKE ? OR LOWER(b.category) LIKE ? OR LOWER(b.short_description) LIKE ? OR LOWER(b.about_text) LIKE ?)'
        val = f'%{query}%'
        params.extend([val, val, val, val])
        
    if category:
        sql += ' AND LOWER(b.category) = ?'
        params.append(category)

    if local:
        sql += ' AND LOWER(b.address) LIKE ?'
        params.append(f'%{local}%')
        
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    
    # Sistema de Prioridade de Busca
    # 3 = Elite (Topo) | 2 = PRO | 1 = Básico | 0 = Gratuito
    plan_priority = {'elite': 3, 'pro': 2, 'basico': 1, 'gratuito': 0}
    
    results = []
    for row in rows:
        b = dict(row)
        plan = (b.get('plan') or 'basico').lower()
        b['priority'] = plan_priority.get(plan, 1)
        
        # Colocamos o badge de destaque automaticamente se for elite
        if plan == 'elite':
            b['featured'] = True
            
        results.append(b)
        
    # Ordena: Maior prioridade primeiro. Em caso de empate, ordena por nome
    results.sort(key=lambda x: (x['priority'], x['name']), reverse=True)
    
    return jsonify(results)

@app.route('/api/businesses/<int:id>')
def api_business(id):
    conn = get_db_connection()
    
    # Incrementa views
    conn.execute('UPDATE businesses SET views = COALESCE(views, 0) + 1 WHERE id = ?', (id,))
    conn.commit()

    business_row = conn.execute('SELECT * FROM businesses WHERE status != 'suspended' WHERE id = ?', (id,)).fetchone()
    if not business_row:
        conn.close()
        return jsonify({'error': 'Business not found'}), 404

    services_rows = conn.execute('SELECT * FROM services WHERE business_id = ?', (id,)).fetchall()
    gallery_rows = conn.execute('SELECT * FROM gallery WHERE business_id = ?', (id,)).fetchall()
    reviews_rows = conn.execute('SELECT * FROM reviews WHERE business_id = ? ORDER BY created_at DESC', (id,)).fetchall()
    
    conn.close()

    business = dict(business_row)
    business['services'] = [dict(s) for s in services_rows]
    business['gallery'] = [dict(g) for g in gallery_rows]
    business['reviews'] = [dict(r) for r in reviews_rows]

    plan = get_user_plan(id)
    business['plan'] = plan
    business['plan_limits'] = PLAN_LIMITS.get(plan, PLAN_LIMITS['basico'])

    return jsonify(business)

# ============================================================
# API — Upload de Imagens
# ============================================================

@app.route('/api/businesses/<int:id>/upload-main', methods=['POST'])
@login_required
def upload_main_image(id):
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhuma imagem enviada'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"main_{id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_url = f"/static/uploads/{filename}"
        
        conn = get_db_connection()
        conn.execute('UPDATE businesses SET image = ? WHERE id = ?', (file_url, id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'url': file_url})
    
    return jsonify({'success': False, 'message': 'Formato não permitido'}), 400

@app.route('/api/businesses/<int:id>/gallery/add', methods=['POST'])
@login_required
def add_gallery_image(id):
    plan = get_user_plan(id)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['basico'])
    max_photos = limits['photos']
    
    conn = get_db_connection()
    current_count = conn.execute('SELECT COUNT(*) FROM gallery WHERE business_id = ?', (id,)).fetchone()[0]
    
    if max_photos is not None and current_count >= max_photos:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Seu plano permite até {max_photos} fotos na galeria.'
        }), 403

    if 'image' not in request.files:
        conn.close()
        return jsonify({'success': False, 'message': 'Nenhuma imagem enviada'}), 400
        
    file = request.files['image']
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"gal_{id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_url = f"/static/uploads/{filename}"
        
        conn.execute('INSERT INTO gallery (business_id, image_url) VALUES (?, ?)', (id, file_url))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'url': file_url})
        
    conn.close()
    return jsonify({'success': False, 'message': 'Erro no upload'}), 400

@app.route('/api/businesses/<int:id>/gallery/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_gallery_image(id, photo_id):
    conn = get_db_connection()
    
    # Optional: We could delete the physical file too, but removing from DB is enough for now
    conn.execute('DELETE FROM gallery WHERE id = ? AND business_id = ?', (photo_id, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ============================================================
# API — Atualizar Perfil
# ============================================================


@app.route('/api/businesses/<int:id>/update', methods=['POST'])
@login_required
def update_business(id):
    data = request.json
    name = str(escape(data.get('name', ''))).strip()
    
    if not name:
        return jsonify({'success': False, 'message': 'O nome da empresa não pode ser vazio.'}), 400
        
    category = str(escape(data.get('category', '')))
    category = str(escape(data.get('category', '')))
    short_description = str(escape(data.get('short_description', '')))
    about_text = str(escape(data.get('about_text', '')))
    whatsapp = str(escape(data.get('whatsapp', '')))
    instagram = str(escape(data.get('instagram', '')))
    address = str(escape(data.get('address', '')))
    maps_url = data.get('maps_url', '') # Maps URL must be kept intact but we trust admin input here, could sanitize differently

    conn = get_db_connection()
    conn.execute('''
        UPDATE businesses 
        SET name = ?, category = ?, short_description = ?, about_text = ?, 
            whatsapp = ?, instagram = ?, address = ?, maps_url = ?
        WHERE id = ?
    ''', (name, category, short_description, about_text, whatsapp, instagram, address, maps_url, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ============================================================
# API — Serviços
# ============================================================

@app.route('/api/businesses/<int:id>/services/add', methods=['POST'])
@login_required
def add_service(id):
    data = request.json
    name = str(escape(data.get('name', '')))
    description = str(escape(data.get('description', '')))
    price = str(escape(data.get('price', '')))
    
    plan = get_user_plan(id)
    limits = PLAN_LIMITS.get(plan, PLAN_LIMITS['basico'])
    max_services = limits['services']
    
    conn = get_db_connection()
    current_count = conn.execute('SELECT COUNT(*) FROM services WHERE business_id = ?', (id,)).fetchone()[0]
    
    if max_services is not None and current_count >= max_services:
        conn.close()
        return jsonify({
            'success': False,
            'message': f'Limite de serviços atingido. Seu plano permite até {max_services} serviços.'
        }), 403
        
    conn.execute('INSERT INTO services (business_id, name, description, price) VALUES (?, ?, ?, ?)',
                 (id, name, description, price))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/businesses/<int:id>/services/<int:service_id>/delete', methods=['POST'])
@login_required
def delete_service(id, service_id):
    conn = get_db_connection()
    # Verifica business_id por segurança (evita apagar serviço de outra pessoa)
    conn.execute('DELETE FROM services WHERE id = ? AND business_id = ?', (service_id, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ============================================================
# API — Reviews
# ============================================================
@app.route('/api/businesses/<int:id>/reviews/add', methods=['POST'])
def add_review(id):
    data = request.json
    author = str(escape(data.get('author_name', 'Anônimo')))
    
    try:
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        rating = 5
        
    comment = str(escape(data.get('comment', '')))
    
    if rating < 1 or rating > 5: rating = 5
    
    conn = get_db_connection()
    conn.execute('INSERT INTO reviews (business_id, author_name, rating, comment) VALUES (?, ?, ?, ?)',
                 (id, author, rating, comment))
    
    # Atualiza a nota média da empresa
    avg_row = conn.execute('SELECT AVG(rating) as avg, COUNT(id) as count FROM reviews WHERE business_id = ?', (id,)).fetchone()
    new_avg = round(avg_row['avg'], 1) if avg_row['avg'] else 0.0
    
    conn.execute('UPDATE businesses SET rating = ? WHERE id = ?', (new_avg, id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'new_rating': new_avg})

@app.route('/api/businesses/<int:id>/reviews/<int:review_id>/reply', methods=['POST'])
@login_required
def reply_review(id, review_id):
    data = request.json
    reply_text = str(escape(data.get('reply', '')))
    
    conn = get_db_connection()
    # Verifica se a avaliação pertence a esta empresa para evitar IDOR
    review = conn.execute('SELECT * FROM reviews WHERE id = ? AND business_id = ?', (review_id, id)).fetchone()
    if not review:
        conn.close()
        return jsonify({'success': False, 'message': 'Avaliação não encontrada.'}), 404
        
    conn.execute('UPDATE reviews SET reply = ? WHERE id = ?', (reply_text, review_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})


# ============================================================
# API — Autenticação
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def login_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    if email == 'admin@tuumweb.com' and password == 'superadmin123':
        session['user_id'] = 0
        session['role'] = 'superadmin'
        return jsonify({'success': True, 'redirect': '/super_admin.html', 'role': 'superadmin'})
        
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    if user:
        is_valid = False
        if user['password'].startswith('scrypt:') or user['password'].startswith('pbkdf2:'):
            is_valid = check_password_hash(user['password'], password)
        else:
            if user['password'] == password:
                is_valid = True
                hashed = generate_password_hash(password)
                conn.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user['id']))
                conn.commit()
                
        if is_valid:
            session['user_id'] = user['id']
            session['business_id'] = user['business_id']
            session['role'] = 'business'
            conn.close()
            return jsonify({'success': True, 'business_id': user['business_id'], 'plan': user['plan']})
            
    conn.close()
    return jsonify({'success': False, 'message': 'Email ou senha incorretos'})

@app.route('/api/auth/register', methods=['POST'])
def register_api():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    business_name = str(escape(data.get('business_name', ''))).strip()
    
    # Valida e recebe o plano escolhido (default para basico se vier vazio)
    chosen_plan = data.get('plan', 'basico').lower()
    valid_plans = ['gratuito', 'basico', 'pro', 'elite']
    if chosen_plan not in valid_plans:
        chosen_plan = 'basico'
    
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Email já cadastrado.'}), 400

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO businesses (name, category, rating, distance, image, featured, about_text)
        VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '')
    ''', (business_name,))
    business_id = cursor.lastrowid

    hashed_pw = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (email, password, business_id, plan)
        VALUES (?, ?, ?, ?)
    ''', (email, hashed_pw, business_id, chosen_plan))
    
    user_id = cursor.lastrowid
    
    # Loga o usuário automaticamente no backend após o cadastro
    session['user_id'] = user_id
    session['business_id'] = business_id
    session['role'] = 'business'

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'business_id': business_id, 'plan': chosen_plan})

@app.route('/api/auth/logout', methods=['POST'])
def logout_api():
    session.clear()
    return jsonify({'success': True})

# ============================================================
# API — Super Admin
# ============================================================

@app.route('/api/superadmin/dashboard')
@superadmin_required
def superadmin_dashboard():
    conn = get_db_connection()
    users_businesses = conn.execute('''
        SELECT u.email, u.plan, b.id as business_id, b.name as business_name, b.category, b.views, b.status
        FROM users u
        JOIN businesses b ON u.business_id = b.id
        ORDER BY b.id DESC
    ''').fetchall()
    
    total_views = conn.execute('SELECT SUM(views) as total FROM businesses').fetchone()['total'] or 0
    conn.close()

    prices = {'gratuito': 0.00, 'basico': 29.90, 'pro': 49.90, 'elite': 99.90}
    mrr = sum(prices.get((row['plan'] or 'basico').lower(), 29.90) for row in users_businesses if row['status'] != 'suspended')

    subscriptions = []
    for row in users_businesses:
        plan = (row['plan'] or 'basico').lower()
        price_val = prices.get(plan, 29.90)
        price_str = "R$ 0,00 (Grátis)" if price_val == 0 else f"R$ {price_val:.2f}".replace('.', ',')
        subscriptions.append({
            'business_id': row['business_id'],
            'business_name': row['business_name'],
            'category': row['category'] or 'Sem categoria',
            'plan': plan.upper(),
            'price': price_str,
            'email': row['email'],
            'views': row['views'] or 0,
            'status': row['status'] or 'active'
        })

    return jsonify({
        'mrr': f"R$ {mrr:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
        'total_businesses': len(users_businesses),
        'total_views': total_views,
        'subscriptions': subscriptions
    }), 400

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO businesses (name, category, rating, distance, image, featured, about_text)
        VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '')
    ''', (business_name,))
    business_id = cursor.lastrowid

    hashed_pw = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (email, password, business_id, plan)
        VALUES (?, ?, ?, ?)
    ''', (email, hashed_pw, business_id, plan))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'business_id': business_id})

# ============================================================

@app.route('/api/superadmin/businesses/<int:id>/status', methods=['POST'])
@superadmin_required
def toggle_status(id):
    conn = get_db_connection()
    current = conn.execute('SELECT status FROM businesses WHERE id = ?', (id,)).fetchone()
    if not current:
        conn.close()
        return jsonify({'success': False}), 404
        
    new_status = 'suspended' if current['status'] == 'active' else 'active'
    conn.execute('UPDATE businesses SET status = ? WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'status': new_status})

# ============================================================
# Rotas HTML

# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search.html')
def search():
    return render_template('search.html')

@app.route('/profile.html')
def profile():
    return render_template('profile.html')

@app.route('/anuncie.html')
def anuncie():
    return render_template('anuncie.html')

@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/cadastro.html')
def cadastro():
    return render_template('cadastro.html')

@app.route('/admin.html')
def admin():
    return render_template('admin.html')

@app.route('/super_admin.html')
def super_admin():
    return render_template('super_admin.html')

@app.route('/como-funciona.html')
def como_funciona():
    return render_template('como-funciona.html')

@app.route('/checkout.html')
def checkout():
    return render_template('checkout.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
