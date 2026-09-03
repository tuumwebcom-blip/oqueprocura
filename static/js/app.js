// Variável global para armazenar os dados carregados (útil para uso síncrono legado se precisar, mas preferimos fetch direto)
let mockBusinesses = [];

async function loadBusinesses(query = '', category = '', local = '') {
  try {
    const params = new URLSearchParams();
    if (query) params.append('q', query);
    if (category) params.append('category', category);
    if (local) params.append('local', local);
    
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

async function renderBusinessCards(containerId, limit = null, query = '', category = '', local = '') {
  const container = document.getElementById(containerId);
  if (!container) return;

  container.innerHTML = '<p class="text-muted col-span-3 text-center">Buscando...</p>';

  // Sempre carrega dados frescos se tiver query/categoria
  await loadBusinesses(query, category, local);

  const businessesToRender = limit ? mockBusinesses.slice(0, limit) : mockBusinesses;
  
  if (businessesToRender.length === 0) {
    container.innerHTML = `
      <div class="col-span-3 text-center py-12" style="background:var(--color-surface); border-radius:var(--radius-lg); border:1px solid var(--color-border);">
        <i data-lucide="search-x" class="w-12 h-12 text-muted mx-auto mb-4"></i>
        <h3 class="text-xl font-bold text-text-dark mb-2">Nenhum resultado encontrado</h3>
        <p class="text-muted">Tente buscar por termos mais genéricos ou mude a categoria.</p>
        <button class="btn btn-outline mt-6" onclick="window.location.href='search.html'">Ver todas as empresas</button>
      </div>
    `;
    if (typeof lucide !== 'undefined') lucide.createIcons();
    return;
  }
  
  container.innerHTML = businessesToRender.map(biz => `
    <a href="profile.html?id=${biz.id}" class="card">
      <div class="card-img-wrapper">
        ${biz.featured ? '<div class="card-badge-container"><span class="badge badge-featured">Destaque</span></div>' : ''}
        <img src="${biz.image}" alt="${biz.name}" class="card-img">
      </div>
      <div class="card-body">
        <span class="card-category">${biz.category}</span>
        <h3 class="card-title">${biz.name}</h3>
        <div class="card-info">
          <i data-lucide="map-pin" class="w-4 h-4"></i>
          ${biz.distance}
        </div>
        <div class="card-footer">
          <div class="rating">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
            ${biz.rating}
          </div>
          <span class="text-secondary font-medium text-sm flex items-center gap-2">Ver perfil <i data-lucide="arrow-right" class="w-4 h-4"></i></span>
        </div>
      </div>
    </a>
  `).join('');
  
  // Re-renderizar icones recém injetados
  if (typeof lucide !== 'undefined') {
      lucide.createIcons();
  }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  const urlParams = new URLSearchParams(window.location.search);
  const q = urlParams.get('q') || '';
  const cat = urlParams.get('category') || '';
  const loc = urlParams.get('local') || '';

  renderBusinessCards('featured-businesses', 4); // Homepage
  renderBusinessCards('search-results', null, q, cat, loc); // Search page

  // Update query display count and text in search.html if exists
  setTimeout(() => {
    const display = document.getElementById('query-display');
    const subtitle = document.getElementById('query-subtitle');
    if (display) {
      if (q) display.textContent = `"${q}"`;
      else if (cat) display.textContent = `Categoria: ${cat}`;
      else display.textContent = "Todas as empresas";
    }
    if (subtitle) {
      subtitle.textContent = `Mostrando ${mockBusinesses.length} resultado(s) encontrados.`;
    }
  }, 500);

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
