from flask import Flask, render_template, request, jsonify, session, redirect
import sqlite3
import requests
import uuid
import os
import re
import html
import random
import time
import unicodedata
import json
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from functools import wraps

try:
    from dotenv import load_dotenv
    basedir = os.path.dirname(os.path.abspath(__file__))
    load_dotenv(os.path.join(basedir, '.env'))
    if os.path.exists('/home/Tuumweb/.env'):
        load_dotenv('/home/Tuumweb/.env')
except Exception:
    pass

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'tuumweb-production-secret-key-2026')

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
        'photos': 2,
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

def slugify(text):
    if not text:
        return ''
    text = html.unescape(str(text))
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    text = re.sub(r'[-\s]+', '-', text)
    return text.strip('-')

def get_unique_slug(conn, base_text, business_id=None):
    base_slug = slugify(base_text)
    if not base_slug:
        base_slug = f"empresa-{business_id or random.randint(1000, 9999)}"
    slug = base_slug
    counter = 1
    while True:
        query = "SELECT id FROM businesses WHERE slug = ? COLLATE NOCASE"
        params = [slug]
        if business_id:
            query += " AND id != ?"
            params.append(business_id)
        existing = conn.execute(query, params).fetchone()
        if not existing:
            return slug
        counter += 1
        slug = f"{base_slug}-{counter}"

def check_db_schema():
    try:
        conn = get_db_connection()
        cols = [c[1] for c in conn.execute('PRAGMA table_info(businesses)').fetchall()]
        if 'website' not in cols:
            conn.execute('ALTER TABLE businesses ADD COLUMN website TEXT')
        if 'business_hours' not in cols:
            conn.execute('ALTER TABLE businesses ADD COLUMN business_hours TEXT')
        if 'whatsapp_clicks' not in cols:
            conn.execute('ALTER TABLE businesses ADD COLUMN whatsapp_clicks INTEGER DEFAULT 0')
        if 'color_primary' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN color_primary TEXT DEFAULT '#2563eb'")
        if 'whatsapp_cta' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN whatsapp_cta TEXT DEFAULT 'Conversar no WhatsApp'")
        if 'whatsapp_message' not in cols:
            conn.execute('ALTER TABLE businesses ADD COLUMN whatsapp_message TEXT')
        if 'amenities' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN amenities TEXT DEFAULT '[]'")
        if 'facebook' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN facebook TEXT DEFAULT ''")
        if 'tiktok' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN tiktok TEXT DEFAULT ''")
        if 'linkedin' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN linkedin TEXT DEFAULT ''")
        if 'youtube' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN youtube TEXT DEFAULT ''")
        if 'catalog_url' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN catalog_url TEXT DEFAULT ''")
        if 'slug' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN slug TEXT DEFAULT ''")
        if 'color_bg' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN color_bg TEXT DEFAULT '#f8fafc'")
        if 'color_text' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN color_text TEXT DEFAULT '#0f172a'")
        if 'bg_image' not in cols:
            conn.execute("ALTER TABLE businesses ADD COLUMN bg_image TEXT DEFAULT ''")

        # Garante slug para todas as empresas existentes
        rows_without_slug = conn.execute("SELECT id, name FROM businesses WHERE slug IS NULL OR slug = ''").fetchall()
        for r in rows_without_slug:
            s = get_unique_slug(conn, r['name'] or f"empresa-{r['id']}", business_id=r['id'])
            conn.execute("UPDATE businesses SET slug = ? WHERE id = ?", (s, r['id']))

        try:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_businesses_slug ON businesses(slug)")
        except Exception:
            pass

        cols_rev = [c[1] for c in conn.execute('PRAGMA table_info(reviews)').fetchall()]
        if 'author_email' not in cols_rev:
            conn.execute('ALTER TABLE reviews ADD COLUMN author_email TEXT')

        cols_users = [c[1] for c in conn.execute('PRAGMA table_info(users)').fetchall()]
        if 'is_verified' not in cols_users:
            conn.execute('ALTER TABLE users ADD COLUMN is_verified INTEGER DEFAULT 1')
        if 'verification_code' not in cols_users:
            conn.execute('ALTER TABLE users ADD COLUMN verification_code TEXT')
        if 'verification_code_expires' not in cols_users:
            conn.execute('ALTER TABLE users ADD COLUMN verification_code_expires INTEGER')

        # Limpa entidades HTML duplicadas no banco
        conn.execute("UPDATE businesses SET category = REPLACE(category, '&amp;amp;', '&') WHERE category LIKE '%&amp;amp;%'")
        conn.execute("UPDATE businesses SET category = REPLACE(category, '&amp;', '&') WHERE category LIKE '%&amp;%'")
        conn.execute("UPDATE businesses SET name = REPLACE(name, '&amp;amp;', '&') WHERE name LIKE '%&amp;amp;%'")
        conn.execute("UPDATE businesses SET name = REPLACE(name, '&amp;', '&') WHERE name LIKE '%&amp;%'")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Erro no check_db_schema: {e}")

check_db_schema()

def send_verification_email(to_email, code):
    """
    Envia o código de verificação para o e-mail informado.
    Prioridades de envio:
    1. Resend API (se RESEND_API_KEY estiver configurado no .env)
    2. SendGrid API (se SENDGRID_API_KEY estiver configurado no .env)
    3. SMTP padrão (se SMTP_HOST e SMTP_USER estiverem configurados no .env)
    Fallback: Exibe o código no log do servidor.
    """
    subject = f"{code} é o seu código de verificação - O Que Procura?"
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head><meta charset="UTF-8"></head>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 30px 10px;">
      <div style="max-width: 500px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
        <div style="background: #2563eb; padding: 24px; text-align: center;">
          <h1 style="color: #ffffff; margin: 0; font-size: 22px; font-weight: 700; letter-spacing: -0.5px;">O Que Procura?</h1>
        </div>
        <div style="padding: 32px 28px; text-align: center;">
          <h2 style="color: #0f172a; font-size: 20px; font-weight: 700; margin: 0 0 12px;">Confirme seu endereço de e-mail</h2>
          <p style="color: #475569; font-size: 15px; line-height: 1.5; margin: 0 0 24px;">
            Obrigado por se cadastrar! Para ativar sua conta e garantir que seu e-mail seja autêntico, informe o código de verificação abaixo:
          </p>
          <div style="background: #eff6ff; border: 2px dashed #3b82f6; border-radius: 10px; padding: 18px 24px; display: inline-block; margin-bottom: 24px;">
            <span style="font-family: monospace, Courier, monospace; font-size: 34px; font-weight: 800; color: #1d4ed8; letter-spacing: 8px;">{code}</span>
          </div>
          <p style="color: #64748b; font-size: 13px; line-height: 1.5; margin: 0 0 12px;">
            Este código é válido por <strong>15 minutos</strong>. Se você não solicitou este cadastro, desconsidere esta mensagem.
          </p>
        </div>
        <div style="background: #f1f5f9; padding: 16px; text-align: center; border-top: 1px solid #e2e8f0;">
          <p style="color: #94a3b8; font-size: 12px; margin: 0;">© 2026 O Que Procura? · TUUMWEB.COM</p>
        </div>
      </div>
    </body>
    </html>
    """

    resend_api_key = os.environ.get('RESEND_API_KEY', '').strip()
    resend_from = os.environ.get('RESEND_FROM', 'O Que Procura? <onboarding@resend.dev>').strip()
    sendgrid_api_key = os.environ.get('SENDGRID_API_KEY', '').strip()
    sendgrid_from = os.environ.get('SENDGRID_FROM', 'contato@tuumweb.com').strip()
    smtp_host = os.environ.get('SMTP_HOST', '').strip()

    # 1. Tentativa via Resend (HTTPS 443)
    if resend_api_key:
        try:
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": resend_from,
                    "to": [to_email],
                    "subject": subject,
                    "html": html_content
                },
                timeout=10
            )
            print(f"[RESEND] Status {resp.status_code}: {resp.text}")
            if resp.status_code in [200, 201]:
                return True, "Enviado via Resend"
        except Exception as e:
            print(f"[RESEND ERROR] {e}")

    # 2. Tentativa via SendGrid (HTTPS 443)
    if sendgrid_api_key:
        try:
            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {sendgrid_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {"email": sendgrid_from, "name": "O Que Procura?"},
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html_content}]
                },
                timeout=10
            )
            print(f"[SENDGRID] Status {resp.status_code}")
            if resp.status_code in [200, 202]:
                return True, "Enviado via SendGrid"
        except Exception as e:
            print(f"[SENDGRID ERROR] {e}")

    # 3. Tentativa via SMTP padrão
    if smtp_host:
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_user = os.environ.get('SMTP_USER', '').strip()
            smtp_pass = os.environ.get('SMTP_PASSWORD', '').strip()
            smtp_port = int(os.environ.get('SMTP_PORT', 587))

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_user
            msg["To"] = to_email
            msg.attach(MIMEText(html_content, "html"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to_email], msg.as_string())
            print(f"[SMTP] Enviado para {to_email}")
            return True, "Enviado via SMTP"
        except Exception as e:
            print(f"[SMTP ERROR] {e}")

    # Log de fallback quando nenhuma chave estiver no .env
    print(f"==================================================")
    print(f"[EMAIL FALLBACK] Para: {to_email}")
    print(f"[EMAIL FALLBACK] CÓDIGO DE VERIFICAÇÃO: {code}")
    print(f"==================================================")
    return False, "Código registrado no console"

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
    businesses = conn.execute("SELECT * FROM businesses WHERE status != 'suspended'").fetchall()
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
        # Permite busca flexível com ou sem acentuação (ex: alimentacao vs alimentação)
        cat_clean = category.replace('ç', 'c').replace('ã', 'a').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        sql += ' AND (LOWER(b.category) LIKE ? OR LOWER(b.category) LIKE ?)'
        params.extend([f'%{category}%', f'%{cat_clean[:4]}%'])

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

    business_row = conn.execute("SELECT * FROM businesses WHERE status != 'suspended' AND id = ?", (id,)).fetchone()
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

    # Parsing de amenities para lista
    try:
        if isinstance(business.get('amenities'), str):
            business['amenities'] = json.loads(business['amenities'] or '[]')
        elif not business.get('amenities'):
            business['amenities'] = []
    except Exception:
        business['amenities'] = []

    plan = get_user_plan(id)
    business['plan'] = plan
    business['plan_limits'] = PLAN_LIMITS.get(plan, PLAN_LIMITS['basico'])

    return jsonify(business)

@app.route('/api/businesses/slug/<slug>')
def api_business_by_slug(slug):
    conn = get_db_connection()
    clean_slug = slug.strip().lower()
    biz = conn.execute("SELECT id FROM businesses WHERE status != 'suspended' AND slug = ? COLLATE NOCASE", (clean_slug,)).fetchone()
    conn.close()
    if biz:
        return api_business(biz['id'])
    return jsonify({'error': 'Business not found'}), 404

@app.route('/api/businesses/<int:id>/click-whatsapp', methods=['POST'])
def track_whatsapp_click(id):
    conn = get_db_connection()
    conn.execute('UPDATE businesses SET whatsapp_clicks = COALESCE(whatsapp_clicks, 0) + 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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

@app.route('/api/businesses/<int:id>/upload-bg', methods=['POST'])
@login_required
def upload_bg_image(id):
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'Nenhuma imagem enviada'}), 400
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Nenhum arquivo selecionado'}), 400
        
    if file and allowed_file(file.filename):
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"bg_{id}_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        file_url = f"/static/uploads/{filename}"
        
        conn = get_db_connection()
        conn.execute('UPDATE businesses SET bg_image = ? WHERE id = ?', (file_url, id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'url': file_url})
    
    return jsonify({'success': False, 'message': 'Formato não permitido'}), 400

@app.route('/api/businesses/<int:id>/remove-bg', methods=['POST'])
@login_required
def remove_bg_image(id):
    conn = get_db_connection()
    conn.execute('UPDATE businesses SET bg_image = "" WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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
    
    def clean(val):
        if not val:
            return ''
        return html.unescape(str(val).strip())

    name = clean(data.get('name', ''))
    if not name:
        return jsonify({'success': False, 'message': 'O nome da empresa não pode ser vazio.'}), 400
        
    category = clean(data.get('category', ''))
    short_description = clean(data.get('short_description', ''))
    about_text = clean(data.get('about_text', ''))
    whatsapp = clean(data.get('whatsapp', ''))
    instagram = clean(data.get('instagram', ''))
    address = clean(data.get('address', ''))
    website = clean(data.get('website', ''))
    business_hours = clean(data.get('business_hours', ''))
    color_primary = clean(data.get('color_primary', '#2563eb'))
    if not color_primary.startswith('#') or len(color_primary) not in (4, 7):
        color_primary = '#2563eb'
    whatsapp_cta = clean(data.get('whatsapp_cta', 'Conversar no WhatsApp')) or 'Conversar no WhatsApp'
    whatsapp_message = clean(data.get('whatsapp_message', ''))
    maps_url = data.get('maps_url', '').strip()

    facebook = clean(data.get('facebook', ''))
    tiktok = clean(data.get('tiktok', ''))
    linkedin = clean(data.get('linkedin', ''))
    youtube = clean(data.get('youtube', ''))
    catalog_url = clean(data.get('catalog_url', ''))
    color_bg = clean(data.get('color_bg', '#f8fafc'))
    if not color_bg.startswith('#') or len(color_bg) not in (4, 7):
        color_bg = '#f8fafc'
    color_text = clean(data.get('color_text', '#0f172a'))
    if not color_text.startswith('#') or len(color_text) not in (4, 7):
        color_text = '#0f172a'
    bg_image = clean(data.get('bg_image', ''))

    # Amenities (lista de strings)
    raw_amenities = data.get('amenities', [])
    if isinstance(raw_amenities, str):
        try:
            raw_amenities = json.loads(raw_amenities)
        except Exception:
            raw_amenities = []
    if not isinstance(raw_amenities, list):
        raw_amenities = []
    valid_amenities = [clean(item) for item in raw_amenities if item]
    amenities_json = json.dumps(valid_amenities)

    # Slug
    conn = get_db_connection()
    custom_slug = slugify(data.get('slug', ''))
    if not custom_slug:
        custom_slug = get_unique_slug(conn, name, business_id=id)
    else:
        existing = conn.execute("SELECT id FROM businesses WHERE slug = ? COLLATE NOCASE AND id != ?", (custom_slug, id)).fetchone()
        if existing:
            conn.close()
            return jsonify({'success': False, 'message': f'O link "{custom_slug}" já está em uso por outra empresa. Por favor, escolha outro.'}), 400

    conn.execute('''
        UPDATE businesses 
        SET name = ?, category = ?, short_description = ?, about_text = ?, 
            whatsapp = ?, instagram = ?, address = ?, maps_url = ?,
            website = ?, business_hours = ?, color_primary = ?,
            whatsapp_cta = ?, whatsapp_message = ?,
            facebook = ?, tiktok = ?, linkedin = ?, youtube = ?, catalog_url = ?,
            amenities = ?, slug = ?, color_bg = ?, color_text = ?, bg_image = ?
        WHERE id = ?
    ''', (name, category, short_description, about_text, whatsapp, instagram, address, maps_url, 
          website, business_hours, color_primary, whatsapp_cta, whatsapp_message,
          facebook, tiktok, linkedin, youtube, catalog_url, amenities_json, custom_slug,
          color_bg, color_text, bg_image, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'slug': custom_slug})

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
    data = request.json or {}
    author = str(escape(data.get('author_name', ''))).strip()
    email = str(escape(data.get('author_email', ''))).strip().lower()
    comment = str(escape(data.get('comment', ''))).strip()

    if not author:
        return jsonify({'success': False, 'message': 'Por favor, informe seu nome completo.'}), 400

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w{2,}$'
    if not email or not re.match(email_regex, email):
        return jsonify({'success': False, 'message': 'Por favor, informe um e-mail válido para registrar sua avaliação.'}), 400

    if not comment:
        return jsonify({'success': False, 'message': 'Por favor, escreva um comentário sobre sua experiência.'}), 400

    try:
        rating = int(data.get('rating', 5))
    except (ValueError, TypeError):
        rating = 5

    if rating < 1 or rating > 5:
        rating = 5

    conn = get_db_connection()
    # Anti-spam: verificar se esse mesmo e-mail já enviou uma avaliação para essa empresa nos últimos 10 minutos
    recent = conn.execute('''
        SELECT id FROM reviews 
        WHERE business_id = ? AND author_email = ? AND created_at >= datetime('now', '-10 minutes')
    ''', (id, email)).fetchone()
    if recent:
        conn.close()
        return jsonify({'success': False, 'message': 'Você já enviou uma avaliação recentemente para esta empresa. Obrigado!'}), 429

    conn.execute('INSERT INTO reviews (business_id, author_name, author_email, rating, comment) VALUES (?, ?, ?, ?, ?)',
                 (id, author, email, rating, comment))

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
# API — Google OAuth
# ============================================================
GOOGLE_REDIRECT_URI = 'https://tuumweb.pythonanywhere.com/api/auth/google/callback'

def get_google_credentials():
    cid = (os.environ.get('GOOGLE_CLIENT_ID') or '').strip()
    csecret = (os.environ.get('GOOGLE_CLIENT_SECRET') or '').strip()
    if not cid or not csecret:
        try:
            from dotenv import load_dotenv
            basedir = os.path.dirname(os.path.abspath(__file__))
            load_dotenv(os.path.join(basedir, '.env'))
            if os.path.exists('/home/Tuumweb/.env'):
                load_dotenv('/home/Tuumweb/.env')
            cid = (os.environ.get('GOOGLE_CLIENT_ID') or '').strip()
            csecret = (os.environ.get('GOOGLE_CLIENT_SECRET') or '').strip()
        except Exception:
            pass
    return cid, csecret

@app.route('/api/auth/google/login')
def google_login():
    cid, _ = get_google_credentials()
    if not cid:
        return "Erro: GOOGLE_CLIENT_ID não encontrado no arquivo .env do servidor.", 500

    auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={cid}&"
        f"redirect_uri={GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=email%20profile"
    )
    return redirect(auth_url)

@app.route('/api/auth/google/callback')
def google_callback():
    try:
        code = request.args.get('code')
        if not code:
            err = request.args.get('error', 'Autorização negada')
            return f"Erro ao autorizar com Google: {err}", 400
            
        cid, csecret = get_google_credentials()
        if not cid or not csecret:
            return "Erro: Credenciais do Google OAuth não configuradas no servidor.", 500

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': cid,
            'client_secret': csecret,
            'redirect_uri': GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code'
        }
        
        token_res = requests.post(token_url, data=token_data, timeout=10)
        if token_res.status_code != 200:
            return f"Erro ao comunicar com Google ({token_res.status_code}): {token_res.text}", 400
            
        access_token = token_res.json().get('access_token')
        if not access_token:
            return "Erro: Token de acesso não retornado pelo Google.", 400
        
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        user_info_res = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'}, timeout=10)
        if user_info_res.status_code != 200:
            return "Erro ao obter informações do seu perfil no Google.", 400
            
        user_info = user_info_res.json()
        email = (user_info.get('email') or '').strip()
        name = user_info.get('name') or (email.split('@')[0] if email else 'Minha Empresa')
        
        if not email:
            return "Erro: O Google não forneceu um e-mail válido para a sua conta.", 400
        
        # Super Admin Bypass
        if email.lower() == 'admin@tuumweb.com':
            session['user_id'] = 0
            session['role'] = 'superadmin'
            return redirect('/super_admin.html')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            business_id = user['business_id']
            biz = None
            if business_id:
                biz = conn.execute('SELECT id FROM businesses WHERE id = ?', (business_id,)).fetchone()
            
            # Auto-recuperação: se o usuário ficou sem empresa associada, cria uma agora
            if not biz:
                biz_slug = get_unique_slug(conn, name)
                cursor = conn.execute('''
                    INSERT INTO businesses (name, category, rating, distance, image, featured, about_text, slug)
                    VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '', ?)
                ''', (name, biz_slug))
                business_id = cursor.lastrowid
                conn.execute('UPDATE users SET business_id = ? WHERE id = ?', (business_id, user['id']))
                conn.commit()

            session['user_id'] = user['id']
            session['business_id'] = business_id
            session['role'] = 'business'
            conn.close()
            # Passa o business_id na URL para o frontend salvar no localStorage
            return redirect(f'/admin.html?business_id={business_id}')
        else:
            biz_slug = get_unique_slug(conn, name)
            cursor = conn.execute('''
                INSERT INTO businesses (name, category, rating, distance, image, featured, about_text, slug)
                VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '', ?)
            ''', (name, biz_slug))
            business_id = cursor.lastrowid
            
            random_pass = str(uuid.uuid4())
            hashed = generate_password_hash(random_pass)
            
            cursor = conn.execute(
                'INSERT INTO users (email, password, business_id, plan, is_verified) VALUES (?, ?, ?, ?, 1)',
                (email, hashed, business_id, 'gratuito')
            )
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            session['user_id'] = user_id
            session['business_id'] = business_id
            session['role'] = 'business'
            return redirect(f'/anuncie.html?onboarding=1&business_id={business_id}')
    except Exception as e:
        import traceback
        return f"<h1>Erro interno ao processar login:</h1><pre>{traceback.format_exc()}</pre>", 500

# ============================================================
# API — Autenticação

# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def login_api():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
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
            if user['is_verified'] is not None and user['is_verified'] == 0:
                code = f"{random.randint(100000, 999999)}"
                expires = int(time.time()) + 900
                conn.execute('UPDATE users SET verification_code = ?, verification_code_expires = ? WHERE id = ?', (code, expires, user['id']))
                conn.commit()
                conn.close()
                send_verification_email(email, code)
                return jsonify({
                    'success': False,
                    'need_verification': True,
                    'email': email,
                    'message': 'Seu e-mail ainda não foi verificado. Enviamos um novo código de 6 dígitos para o seu e-mail.'
                })

            session['user_id'] = user['id']
            session['business_id'] = user['business_id']
            session['role'] = 'business'
            conn.close()
            return jsonify({'success': True, 'business_id': user['business_id'], 'plan': user['plan']})
            
    conn.close()
    return jsonify({'success': False, 'message': 'Email ou senha incorretos'})

@app.route('/api/auth/register', methods=['POST'])
def register_api():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    password = (data.get('password') or '').strip()
    business_name = str(escape(data.get('business_name', ''))).strip()
    
    if not email or not password or not business_name:
        return jsonify({'success': False, 'message': 'Preencha todos os campos obrigatórios.'}), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return jsonify({'success': False, 'message': 'Digite um e-mail válido.'}), 400

    chosen_plan = (data.get('plan') or 'gratuito').lower().strip()
    valid_plans = ['gratuito', 'basico', 'pro', 'elite']
    if chosen_plan not in valid_plans:
        chosen_plan = 'gratuito'
    
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    
    code = f"{random.randint(100000, 999999)}"
    expires = int(time.time()) + 900  # 15 minutos

    if existing:
        if existing['is_verified'] == 1:
            conn.close()
            return jsonify({'success': False, 'message': 'Este e-mail já possui cadastro. Faça login para acessar.'}), 400
        else:
            # Reenvia código para conta não verificada
            hashed_pw = generate_password_hash(password)
            conn.execute('''
                UPDATE users 
                SET password = ?, verification_code = ?, verification_code_expires = ?, plan = ?
                WHERE id = ?
            ''', (hashed_pw, code, expires, chosen_plan, existing['id']))
            business_id = existing['business_id']
            conn.commit()
            conn.close()
            
            send_verification_email(email, code)
            return jsonify({
                'success': True,
                'need_verification': True,
                'email': email,
                'business_id': business_id,
                'message': 'Código de verificação reenviado para o seu e-mail.'
            })

    cursor = conn.cursor()
    biz_slug = get_unique_slug(conn, business_name)
    cursor.execute('''
        INSERT INTO businesses (name, category, rating, distance, image, featured, about_text, slug)
        VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '', ?)
    ''', (business_name, biz_slug))
    business_id = cursor.lastrowid

    hashed_pw = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (email, password, business_id, plan, is_verified, verification_code, verification_code_expires)
        VALUES (?, ?, ?, ?, 0, ?, ?)
    ''', (email, hashed_pw, business_id, chosen_plan, code, expires))
    
    conn.commit()
    conn.close()

    send_verification_email(email, code)

    return jsonify({
        'success': True,
        'need_verification': True,
        'email': email,
        'business_id': business_id,
        'message': f'Código de confirmação enviado para {email}.'
    })

@app.route('/api/auth/verify-code', methods=['POST'])
def verify_code_api():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()
    code = (data.get('code') or '').strip()

    if not email or not code:
        return jsonify({'success': False, 'message': 'Informe o e-mail e o código.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'Conta não encontrada.'}), 404

    if user['is_verified'] == 1:
        session['user_id'] = user['id']
        session['business_id'] = user['business_id']
        session['role'] = 'business'
        conn.close()
        return jsonify({
            'success': True,
            'business_id': user['business_id'],
            'redirect': f'/anuncie.html?onboarding=1&business_id={user["business_id"]}'
        })

    stored_code = (user['verification_code'] or '').strip()
    expires = user['verification_code_expires'] or 0

    if not stored_code or stored_code != code:
        conn.close()
        return jsonify({'success': False, 'message': 'Código incorreto. Confira os 6 dígitos digitados.'}), 400

    if int(time.time()) > expires:
        conn.close()
        return jsonify({'success': False, 'message': 'O código expirou. Clique em "Reenviar código".'}), 400

    conn.execute('''
        UPDATE users 
        SET is_verified = 1, verification_code = NULL, verification_code_expires = NULL 
        WHERE id = ?
    ''', (user['id'],))
    conn.commit()
    conn.close()

    session['user_id'] = user['id']
    session['business_id'] = user['business_id']
    session['role'] = 'business'

    return jsonify({
        'success': True,
        'business_id': user['business_id'],
        'redirect': f'/anuncie.html?onboarding=1&business_id={user["business_id"]}'
    })

@app.route('/api/auth/resend-code', methods=['POST'])
def resend_code_api():
    data = request.json or {}
    email = (data.get('email') or '').strip().lower()

    if not email:
        return jsonify({'success': False, 'message': 'Informe o e-mail.'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if not user:
        conn.close()
        return jsonify({'success': False, 'message': 'E-mail não cadastrado.'}), 404

    if user['is_verified'] == 1:
        conn.close()
        return jsonify({'success': False, 'message': 'Este e-mail já foi verificado.'}), 400

    code = f"{random.randint(100000, 999999)}"
    expires = int(time.time()) + 900
    conn.execute('UPDATE users SET verification_code = ?, verification_code_expires = ? WHERE id = ?', (code, expires, user['id']))
    conn.commit()
    conn.close()

    send_verification_email(email, code)
    return jsonify({'success': True, 'message': f'Novo código de 6 dígitos enviado para {email}.'})

@app.route('/api/user/choose-plan', methods=['POST'])
def choose_plan_api():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
    
    data = request.json or {}
    plan = (data.get('plan') or 'gratuito').lower().strip()
    valid_plans = ['gratuito', 'basico', 'pro', 'elite']
    if plan not in valid_plans:
        return jsonify({'success': False, 'message': 'Plano inválido'}), 400
    
    conn = get_db_connection()
    conn.execute('UPDATE users SET plan = ? WHERE id = ?', (plan, user_id))
    
    business_id = session.get('business_id')
    if business_id:
        if plan == 'elite':
            conn.execute('UPDATE businesses SET featured = 1 WHERE id = ?', (business_id,))
        else:
            conn.execute('UPDATE businesses SET featured = 0 WHERE id = ?', (business_id,))
            
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'plan': plan,
        'business_id': business_id,
        'message': f'Plano {plan.capitalize()} ativado com sucesso!'
    })

@app.route('/api/account/delete', methods=['POST'])
def delete_account():
    user_id = session.get('user_id')
    if user_id is None:
        return jsonify({'success': False, 'message': 'Não autenticado'}), 401
        
    if session.get('role') == 'superadmin' or user_id == 0:
        return jsonify({'success': False, 'message': 'A conta SuperAdmin não pode ser excluída.'}), 403

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if not user:
        conn.close()
        session.clear()
        return jsonify({'success': False, 'message': 'Usuário não encontrado.'}), 404

    business_id = user['business_id'] or session.get('business_id')

    if business_id:
        conn.execute('DELETE FROM reviews WHERE business_id = ?', (business_id,))
        conn.execute('DELETE FROM services WHERE business_id = ?', (business_id,))
        conn.execute('DELETE FROM gallery WHERE business_id = ?', (business_id,))
        conn.execute('DELETE FROM businesses WHERE id = ?', (business_id,))

    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

    session.clear()
    return jsonify({'success': True, 'message': 'Conta e dados excluídos com sucesso.'})

@app.route('/api/auth/me')
def auth_me():
    if session.get('user_id') is not None:
        user_id = session.get('user_id')
        business_id = session.get('business_id')
        role = session.get('role')
        email = ''
        plan = 'gratuito'
        business_name = ''
        
        business_image = ''
        
        try:
            conn = get_db_connection()
            if user_id == 0:
                email = 'admin@tuumweb.com'
                plan = 'elite'
                business_name = 'Super Admin'
            else:
                user = conn.execute('SELECT email, plan, business_id FROM users WHERE id = ?', (user_id,)).fetchone()
                if user:
                    email = user['email'] or ''
                    plan = user['plan'] or 'gratuito'
                    if not business_id and user['business_id']:
                        business_id = user['business_id']
                        session['business_id'] = business_id
                        
            if business_id:
                biz = conn.execute('SELECT name, image FROM businesses WHERE id = ?', (business_id,)).fetchone()
                if biz:
                    business_name = biz['name'] or ''
                    business_image = biz['image'] or ''
            conn.close()
        except Exception:
            pass

        return jsonify({
            'logged_in': True,
            'user_id': user_id,
            'business_id': business_id,
            'role': role,
            'email': email,
            'plan': plan,
            'business_name': business_name,
            'business_image': business_image
        })
    return jsonify({'logged_in': False}), 401

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
    })

@app.route('/api/superadmin/businesses/add', methods=['POST'])
@superadmin_required
def superadmin_add_business():
    data = request.json
    business_name = str(escape(data.get('business_name', ''))).strip()
    email = str(escape(data.get('email', ''))).strip()
    password = data.get('password', '')
    plan = data.get('plan', 'basico').lower()
    
    if not business_name or not email or not password:
        return jsonify({'success': False, 'message': 'Preencha todos os campos obrigatórios.'}), 400
        
    conn = get_db_connection()
    existing = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'message': 'Email já cadastrado.'}), 400
        
    cursor = conn.cursor()
    biz_slug = get_unique_slug(conn, business_name)
    cursor.execute('''
        INSERT INTO businesses (name, category, rating, distance, image, featured, about_text, slug)
        VALUES (?, 'Não Definida', 0.0, '0 km', 'https://placehold.co/600x400?text=Sem+Foto', False, '', ?)
    ''', (business_name, biz_slug))
    business_id = cursor.lastrowid

    hashed_pw = generate_password_hash(password)
    cursor.execute('''
        INSERT INTO users (email, password, business_id, plan)
        VALUES (?, ?, ?, ?)
    ''', (email, hashed_pw, business_id, plan))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'business_id': business_id})


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

@app.route('/p/<slug>')
def profile_slug(slug):
    conn = get_db_connection()
    clean_slug = slug.strip().lower()
    biz = conn.execute("SELECT id FROM businesses WHERE status != 'suspended' AND slug = ? COLLATE NOCASE", (clean_slug,)).fetchone()
    if not biz and clean_slug.isdigit():
        biz = conn.execute("SELECT id FROM businesses WHERE status != 'suspended' AND id = ?", (int(clean_slug),)).fetchone()
    conn.close()
    if biz:
        return render_template('profile.html', current_business_id=biz['id'])
    return redirect(f'/search.html?q={slug}')

@app.route('/anuncie.html')
@app.route('/planos.html')
@app.route('/planos')
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
    param_bid = request.args.get('business_id', '').strip()
    if param_bid and param_bid.isdigit():
        session['business_id'] = int(param_bid)
        session['role'] = 'business'
    
    current_bid = session.get('business_id') or param_bid or ''
    return render_template('admin.html', current_business_id=current_bid)

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
