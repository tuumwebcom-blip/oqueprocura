function escapeHtml(unsafe) {
  return (unsafe || '').toString()
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Variável global para armazenar os dados carregados (útil para uso síncrono legado se precisar, mas preferimos fetch direto)
let mockBusinesses = [];

async function loadBusinesses(query = '', category = '', local = '', attendance = '') {
  try {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category) params.append('category', category);
    if (local) params.append('local', local);
    if (attendance) params.append('attendance', attendance);
    
    // Sempre usamos o search porque ele junta a tabela de usuários
    // e já ordena por prioridade (Elite > Pro > Basico > Gratuito)
    const url = `/api/search?${params.toString()}`;

    const response = await fetch(url);
    const data = await response.json();
    mockBusinesses = data;
    return data;
  } catch (error) {
    console.error('Erro ao buscar empresas:', error);
    return [];
  }
}

async function renderBusinessCards(containerId, limit = null, query = '', category = '', local = '', attendance = '') {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '<p class="text-muted col-span-3 text-center">Buscando...</p>';

  // Sempre carrega dados frescos se tiver query/categoria
  await loadBusinesses(query, category, local, attendance);

  const businessesToRender = limit ? mockBusinesses.slice(0, limit) : mockBusinesses;
  
  if (businessesToRender.length === 0) {
    const isHome = containerId === 'featured-businesses';
    container.innerHTML = `
      <div style="grid-column: 1 / -1; background: var(--color-surface); border-radius: var(--radius-xl); border: 1.5px dashed var(--color-border); padding: 3rem 1.5rem; text-align: center; box-shadow: var(--shadow-sm);">
        <div style="width: 60px; height: 60px; border-radius: 50%; background: #eff6ff; color: var(--color-secondary); display: flex; align-items: center; justify-content: center; margin: 0 auto 1.25rem;">
          <i data-lucide="${isHome ? 'store' : 'search-x'}" style="width: 28px; height: 28px;"></i>
        </div>
        <h3 class="text-xl font-bold text-text-dark mb-2" style="font-family: 'Plus Jakarta Sans', sans-serif;">
          ${isHome ? 'Cadastre sua empresa e seja o primeiro em destaque!' : 'Nenhuma empresa encontrada'}
        </h3>
        <p class="text-muted text-sm max-w-md mx-auto mb-6">
          ${isHome ? 'A plataforma está pronta para receber novos negócios da sua região. Destaque sua empresa e seja encontrado por milhares de clientes.' : 'Tente buscar por termos mais amplos ou explore outras categorias disponíveis na plataforma.'}
        </p>
        <a href="${isHome ? 'anuncie.html' : 'search.html'}" class="btn btn-primary text-sm shadow-md inline-flex items-center gap-2" style="border-radius: var(--radius-full); padding: 0.65rem 1.5rem;">
          <i data-lucide="${isHome ? 'rocket' : 'rotate-ccw'}" class="w-4 h-4"></i>
          ${isHome ? 'Cadastrar Minha Empresa' : 'Ver Todas as Empresas'}
        </a>
      </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();

    // Atualizar subtitle com contagem (0)
    const subtitle = document.getElementById('query-subtitle');
    if (subtitle) subtitle.textContent = 'Nenhum resultado encontrado.';
    return;
  }
  
  container.innerHTML = businessesToRender.map(biz => {
    let attendanceTag = '';
    if (biz.attendance_type === 'online') {
      attendanceTag = '<span class="badge" style="background:#e0f2fe; color:#0369a1; font-size:11px; padding:2px 7px; border-radius:999px; font-weight:600; display:inline-flex; align-items:center; gap:3px;"><i data-lucide="laptop" class="w-3 h-3"></i> Online</span>';
    } else if (biz.attendance_type === 'presencial') {
      attendanceTag = '<span class="badge" style="background:#fef3c7; color:#92400e; font-size:11px; padding:2px 7px; border-radius:999px; font-weight:600; display:inline-flex; align-items:center; gap:3px;"><i data-lucide="map-pin" class="w-3 h-3"></i> Presencial</span>';
    } else {
      attendanceTag = '<span class="badge" style="background:#f1f5f9; color:#475569; font-size:11px; padding:2px 7px; border-radius:999px; font-weight:600; display:inline-flex; align-items:center; gap:3px;"><i data-lucide="globe" class="w-3 h-3"></i> Ambos</span>';
    }

    const cardLink = biz.slug ? `/p/${biz.slug}` : `profile.html?id=${biz.id}`;

    return `
    <a href="${cardLink}" class="card">
      <div class="card-img-wrapper">
        ${biz.featured ? '<div class="card-badge-container"><span class="badge badge-featured">Destaque</span></div>' : ''}
        <img src="${biz.image}" alt="${escapeHtml(biz.name)}" class="card-img">
      </div>
      <div class="card-body">
        <div class="flex items-center justify-between gap-1 mb-1">
          <span class="card-category">${escapeHtml(biz.category)}</span>
          ${attendanceTag}
        </div>
        <h3 class="card-title">${escapeHtml(biz.name)}</h3>
        <div class="card-info">
          <i data-lucide="${biz.attendance_type === 'online' ? 'wifi' : 'map-pin'}" class="w-4 h-4"></i>
          ${biz.attendance_type === 'online' ? 'Atendimento Online (Brasil)' : escapeHtml(biz.address || (biz.distance && biz.distance !== 'Centro' && biz.distance !== '0 km' ? biz.distance : 'Local'))}
        </div>
        <div class="card-footer">
          <div class="rating">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            ${biz.rating > 0 ? parseFloat(biz.rating).toFixed(1) : 'Novo'}
          </div>
          <span class="text-secondary font-medium text-sm flex items-center gap-2">Ver perfil <i data-lucide="arrow-right" class="w-4 h-4"></i></span>
        </div>
      </div>
    </a>
  `;}).join('');
  
  // Re-renderizar icones recém injetados
  if (typeof lucide !== 'undefined') {
      lucide.createIcons();
  }

  // Atualizar subtitle com contagem real (após fetch completar — BUG 7 fix)
  const subtitle = document.getElementById('query-subtitle');
  if (subtitle) subtitle.textContent = `Mostrando ${mockBusinesses.length} resultado(s) encontrados.`;
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  verificarHeaderAuth();

  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q') || '';
  const cat = urlParams.get('category') || '';
  const loc = urlParams.get('local') || '';
  const att = urlParams.get('attendance') || '';

  renderBusinessCards('featured-businesses', 4); // Homepage
  renderBusinessCards('search-results', null, q, cat, loc, att); // Search page

  // Update query display text in search.html if exists
  const display = document.getElementById('query-display');
  if (display) {
    if (q) display.textContent = `"${q}"`;
    else if (cat) display.textContent = `Categoria: ${cat}`;
    else display.textContent = "Todas as empresas";
  }

  // Search button logic
  const searchBtn = document.getElementById('search-btn');
  if (searchBtn) {
    searchBtn.addEventListener('click', executarBusca);
  }

  // Suporte a Enter nos campos de busca
  document.getElementById('search-input')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') executarBusca();
  });
  document.getElementById('location-input')?.addEventListener('keypress', function(e) {
    if (e.key === 'Enter') executarBusca();
  });
});


function executarBusca() {
  const query = document.getElementById('search-input')?.value.trim() || '';
  const location = document.getElementById('location-input')?.value.trim() || '';
  const params = new URLSearchParams();
  if (query) params.append('q', query);
  if (location) params.append('local', location);
  
  const queryStr = params.toString();
  window.location.href = queryStr ? 'search.html?' + queryStr : 'search.html';
}

// Geolocalização do usuário
function usarLocalizacao() {
  if (!navigator.geolocation) {
    alert('Seu navegador não suporta geolocalização.');
    return;
  }
  const locationInput = document.getElementById('location-input');
  const btn = document.querySelector('button[onclick="usarLocalizacao()"]');
  if (btn) btn.title = 'Buscando localização...';

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const { latitude, longitude } = position.coords;
      if (locationInput) locationInput.value = 'Localização atual (' + latitude.toFixed(2) + ', ' + longitude.toFixed(2) + ')';
      if (btn) btn.title = 'Localização obtida!';
    },
    () => {
      alert('Não foi possível obter sua localização. Verifique as permissões do navegador.');
      if (btn) btn.title = 'Usar minha localização atual';
    }
  );
}

// ============================================================
// Header — Perfil do Usuário Autenticado & Foto
// ============================================================
async function verificarHeaderAuth() {
  const headerNavs = document.querySelectorAll('.header-nav');
  if (!headerNavs.length) return;

  try {
    const res = await fetch('/api/auth/me');
    if (!res.ok) return;
    const data = await res.json();
    if (!data.logged_in) return;

    const isSuperAdmin = data.role === 'superadmin';
    const panelUrl = isSuperAdmin ? '/super_admin.html' : `/admin.html${data.business_id ? '?business_id=' + data.business_id : ''}`;
    const name = data.business_name || (isSuperAdmin ? 'Super Admin' : 'Minha Empresa');
    const email = data.email || '';
    
    // Foto de perfil do usuário / logo da empresa
    let avatarUrl = data.business_image;
    if (!avatarUrl || avatarUrl.includes('placehold.co')) {
      const bg = isSuperAdmin ? '4f46e5' : '2563eb';
      avatarUrl = `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=${bg}&color=fff&bold=true`;
    }

    const publicProfileHtml = (data.business_id && !isSuperAdmin) ? `
      <a href="${data.business_slug ? '/p/' + data.business_slug : '/profile.html?id=' + data.business_id}" class="user-dropdown-item">
        <i data-lucide="store" class="w-4 h-4 text-emerald-600"></i> Ver Perfil Público
      </a>
    ` : '';

    const isAnunciePage = window.location.pathname.includes('anuncie') || window.location.pathname.includes('planos');
    const extraLinks = isAnunciePage ? `
      <a href="/" class="btn btn-ghost text-sm font-medium">Início</a>
      <a href="/search.html" class="btn btn-ghost text-sm font-medium">Buscar</a>
    ` : '';

    const navHtml = `
      ${extraLinks}
      <div class="user-header-profile" style="position: relative; display: flex; align-items: center; gap: 0.75rem;">
        <a href="${panelUrl}" class="btn btn-primary text-sm shadow-sm flex items-center gap-1.5" style="padding: 0.5rem 1rem; font-weight: 600; text-decoration: none;">
          <i data-lucide="layout-dashboard" class="w-4 h-4"></i> Meu Painel
        </a>

        <!-- Botão com a Foto do Perfil e Menu Dropdown -->
        <div class="user-dropdown-wrapper" style="position: relative;">
          <button type="button" class="user-avatar-trigger" style="display: flex; align-items: center; gap: 8px; background: white; border: 1.5px solid var(--color-border); padding: 3px 10px 3px 4px; border-radius: 9999px; cursor: pointer; transition: all 0.2s; outline: none;" title="Minha Conta">
            <img src="${avatarUrl}" alt="${escapeHtml(name)}" style="width: 34px; height: 34px; border-radius: 50%; object-fit: cover; border: 1.5px solid var(--color-secondary); background: #f1f5f9;">
            <span style="font-size: 0.85rem; font-weight: 600; color: var(--color-text-dark); max-width: 120px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(name)}</span>
            <i data-lucide="chevron-down" class="w-4 h-4 text-muted"></i>
          </button>

          <!-- Dropdown Flutuante -->
          <div class="user-dropdown-menu" style="display: none; position: absolute; right: 0; top: calc(100% + 8px); width: 230px; background: white; border-radius: 12px; box-shadow: 0 10px 25px -5px rgba(0,0,0,0.12), 0 8px 10px -6px rgba(0,0,0,0.08); border: 1px solid #e2e8f0; z-index: 9999; overflow: hidden; padding: 6px 0;">
            <div style="padding: 10px 16px; border-bottom: 1px solid #f1f5f9; background: #fafafa;">
              <p style="font-size: 0.85rem; font-weight: 700; color: #0f172a; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(name)}</p>
              <p style="font-size: 0.75rem; color: #64748b; margin: 2px 0 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${escapeHtml(email)}</p>
            </div>
            
            <a href="${panelUrl}" class="user-dropdown-item">
              <i data-lucide="layout-dashboard" class="w-4 h-4 text-blue-600"></i> Meu Painel
            </a>
            ${publicProfileHtml}
            <a href="/anuncie.html" class="user-dropdown-item">
              <i data-lucide="credit-card" class="w-4 h-4 text-amber-500"></i> Planos & Preços
            </a>
            
            <div style="border-top: 1px solid #f1f5f9; margin: 4px 0;"></div>
            
            <a href="#" onclick="logoutHeader(event)" class="user-dropdown-item" style="color: #ef4444;">
              <i data-lucide="log-out" class="w-4 h-4 text-red-500"></i> Sair da conta
            </a>
          </div>
        </div>
      </div>
    `;

    headerNavs.forEach(nav => {
      nav.innerHTML = navHtml;
    });

    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }

    // Configura cliques no botão avatar para abrir/fechar menu
    document.querySelectorAll('.user-dropdown-wrapper').forEach(wrapper => {
      const btn = wrapper.querySelector('.user-avatar-trigger');
      const dropdown = wrapper.querySelector('.user-dropdown-menu');

      if (btn && dropdown) {
        btn.addEventListener('click', (e) => {
          e.stopPropagation();
          const isOpen = dropdown.style.display === 'block';
          document.querySelectorAll('.user-dropdown-menu').forEach(d => d.style.display = 'none');
          dropdown.style.display = isOpen ? 'none' : 'block';
        });
      }
    });

    // Fecha ao clicar fora
    document.addEventListener('click', () => {
      document.querySelectorAll('.user-dropdown-menu').forEach(d => d.style.display = 'none');
    });

  } catch (err) {
    console.error('Erro ao verificar header auth:', err);
  }
}

async function logoutHeader(e) {
  if (e) e.preventDefault();
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    localStorage.removeItem('business_id');
    window.location.href = '/';
  } catch(err) {
    window.location.href = '/';
  }
}
