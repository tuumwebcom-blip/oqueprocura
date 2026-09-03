import re

with open('templates/super_admin.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Atualizar o menu lateral para ter data-targets
nav_old = '''      <nav class="admin-nav px-2">
        <a href="#" class="admin-nav-item active">
          <i data-lucide="pie-chart" class="w-5 h-5"></i> Dashboard
        </a>
        <a href="#" class="admin-nav-item">
          <i data-lucide="users" class="w-5 h-5"></i> Empresas (142)
        </a>
        <a href="#" class="admin-nav-item">
          <i data-lucide="dollar-sign" class="w-5 h-5"></i> Assinaturas
        </a>
        <a href="#" class="admin-nav-item">
          <i data-lucide="tag" class="w-5 h-5"></i> Categorias
        </a>
        <a href="#" class="admin-nav-item">
          <i data-lucide="settings" class="w-5 h-5"></i> Configurações
        </a>
      </nav>'''

nav_new = '''      <nav class="admin-nav px-2">
        <a href="#" class="admin-nav-item active" data-target="dashboard">
          <i data-lucide="pie-chart" class="w-5 h-5"></i> Dashboard
        </a>
        <a href="#" class="admin-nav-item" data-target="empresas">
          <i data-lucide="users" class="w-5 h-5"></i> <span id="nav-empresas-count">Empresas</span>
        </a>
        <a href="#" class="admin-nav-item" data-target="assinaturas">
          <i data-lucide="dollar-sign" class="w-5 h-5"></i> Planos Ativos
        </a>
        <a href="#" class="admin-nav-item" data-target="categorias">
          <i data-lucide="tag" class="w-5 h-5"></i> Categorias
        </a>
        <a href="#" class="admin-nav-item" data-target="configuracoes">
          <i data-lucide="settings" class="w-5 h-5"></i> Configurações
        </a>
      </nav>'''
html = html.replace(nav_old, nav_new)

# 2. Envolver o conteúdo atual na aba Dashboard e criar as outras abas
# Encontrar onde o <main> começa
main_start = html.find('<main class="admin-content">') + len('<main class="admin-content">')
# Encontrar onde as modais começam
modal_start = html.find('<!-- Modal Nova Empresa -->')

content_inside_main = html[main_start:modal_start]

new_main_content = f'''
      <!-- ABA: DASHBOARD -->
      <section id="tab-dashboard" class="tab-section">
{content_inside_main}
      </section>

      <!-- ABA: EMPRESAS -->
      <section id="tab-empresas" class="tab-section" style="display:none;">
        <div class="flex justify-between items-center mb-6">
          <h1 class="text-3xl font-bold text-text-dark" style="font-family: 'Plus Jakarta Sans', sans-serif;">Diretório de Empresas</h1>
          <button class="btn btn-primary" onclick="document.getElementById('modal-add').style.display='flex'">+ Nova Empresa</button>
        </div>
        <div class="card">
          <table class="data-table w-full">
            <thead>
              <tr>
                <th class="text-left">Empresa</th>
                <th class="text-left">Email</th>
                <th class="text-left">Plano</th>
                <th class="text-left">Status</th>
              </tr>
            </thead>
            <tbody id="empresas-list-body">
            </tbody>
          </table>
        </div>
      </section>

      <!-- ABA: ASSINATURAS -->
      <section id="tab-assinaturas" class="tab-section" style="display:none;">
        <h1 class="text-3xl font-bold text-text-dark mb-6" style="font-family: 'Plus Jakarta Sans', sans-serif;">Planos da Plataforma</h1>
        <div class="grid grid-cols-3 gap-6">
          <div class="card">
            <h3 class="font-bold text-text-dark text-lg">Básico</h3>
            <p class="text-2xl font-bold text-secondary my-2">R$ 29,90</p>
            <p class="text-sm text-muted">Ideal para quem está começando.</p>
          </div>
          <div class="card" style="border: 2px solid var(--color-secondary);">
            <h3 class="font-bold text-text-dark text-lg">PRO</h3>
            <p class="text-2xl font-bold text-secondary my-2">R$ 49,90</p>
            <p class="text-sm text-muted">Destaque nas buscas e 20 fotos.</p>
          </div>
          <div class="card" style="background: #1e293b; color: white;">
            <h3 class="font-bold text-white text-lg">Elite</h3>
            <p class="text-2xl font-bold text-purple-400 my-2">R$ 99,90</p>
            <p class="text-sm text-slate-300">Máxima visibilidade e serviços ilimitados.</p>
          </div>
        </div>
      </section>

      <!-- ABA: CATEGORIAS -->
      <section id="tab-categorias" class="tab-section" style="display:none;">
        <h1 class="text-3xl font-bold text-text-dark mb-6" style="font-family: 'Plus Jakarta Sans', sans-serif;">Categorias Cadastradas</h1>
        <div class="card">
          <ul id="categorias-list" class="flex flex-col gap-3">
            <li class="text-muted">Carregando categorias...</li>
          </ul>
        </div>
      </section>

      <!-- ABA: CONFIGURAÇÕES -->
      <section id="tab-configuracoes" class="tab-section" style="display:none;">
        <h1 class="text-3xl font-bold text-text-dark mb-6" style="font-family: 'Plus Jakarta Sans', sans-serif;">Configurações Globais</h1>
        <div class="card max-w-lg">
          <p class="text-muted mb-4">Em breve, configurações avançadas de SEO, nome da plataforma e chaves de pagamento estarão disponíveis aqui.</p>
          <button class="btn btn-outline" onclick="alert('Funcionalidade em desenvolvimento!')">Exportar Banco de Dados</button>
        </div>
      </section>
'''

html = html[:main_start] + new_main_content + html[modal_start:]

# 3. Adicionar lógica JS de navegação das abas e renderização extra
js_nav = '''
    // Lógica de Abas
    document.querySelectorAll('.admin-nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        if(item.getAttribute('href') !== '#') return; // ignora logout
        e.preventDefault();
        
        // Remove active class de todos
        document.querySelectorAll('.admin-nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        
        // Esconde todas as sections
        document.querySelectorAll('.tab-section').forEach(s => s.style.display = 'none');
        
        // Mostra a selecionada
        const target = item.getAttribute('data-target');
        document.getElementById('tab-' + target).style.display = 'block';
      });
    });
'''

# Procura o lucide.createIcons(); e insere a lógica depois
html = html.replace('lucide.createIcons();', 'lucide.createIcons();\n' + js_nav)

# Atualizar as contagens e novas abas dentro do carregarDashboard
js_render = '''
        // Preencher Aba Empresas
        document.getElementById('nav-empresas-count').textContent = `Empresas (${data.total_businesses})`;
        const empBody = document.getElementById('empresas-list-body');
        if (empBody) {
          empBody.innerHTML = data.subscriptions.map(sub => `
            <tr class="border-b border-slate-100">
              <td class="py-3 font-bold text-text-dark">${sub.business_name}</td>
              <td class="py-3 text-muted">${sub.email}</td>
              <td class="py-3"><span class="badge" style="background:#eff6ff; color:var(--color-secondary);">${sub.plan}</span></td>
              <td class="py-3"><span class="status-badge ${sub.status === 'suspended' ? 'status-pending' : 'status-active'}">${sub.status === 'suspended' ? 'Suspensa' : 'Ativa'}</span></td>
            </tr>
          `).join('');
        }

        // Preencher Aba Categorias
        const categoriasList = document.getElementById('categorias-list');
        if (categoriasList) {
          const categorias = [...new Set(data.subscriptions.map(s => s.category))];
          categoriasList.innerHTML = categorias.map(c => `
            <li class="p-3 border border-slate-200 rounded-lg font-medium text-text-dark flex items-center gap-2">
              <i data-lucide="tag" class="w-4 h-4 text-secondary"></i> ${c}
            </li>
          `).join('');
        }
'''

# Inserir no final do carregarDashboard
html = html.replace('} catch (e) {', js_render + '\n      } catch (e) {')

with open('templates/super_admin.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Super Admin atualizado com abas!")
