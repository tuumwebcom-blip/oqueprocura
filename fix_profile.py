import re

filepath = 'templates/profile.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_script = """    // Lógica para carregar os dados dinâmicos baseados no ID da URL
    document.addEventListener('DOMContentLoaded', () => {
      const urlParams = new URLSearchParams(window.location.search);
      const id = parseInt(urlParams.get('id'));
      
      if (id && typeof mockBusinesses !== 'undefined') {
        const business = mockBusinesses.find(b => b.id === id);
        if (business) {
          // Atualizar Título e Title da aba
          const titleEl = document.querySelector('.profile-title');
          if (titleEl) titleEl.textContent = business.name;
          document.title = business.name + " - O Que Procura?";
          
          // Atualizar Imagem Principal
          const imgEl = document.querySelector('.gallery-main');
          if (imgEl) {
            imgEl.src = business.image;
            imgEl.alt = business.name;
          }
          
          // Atualizar Meta Informações (Avaliação, Distância e Categoria)
          const metaContainer = document.querySelector('.profile-meta');
          if (metaContainer) {
            metaContainer.innerHTML = `
              <span class="flex items-center gap-1 font-medium"><i data-lucide="star" class="w-4 h-4 text-warning fill-warning"></i> ${business.rating}</span>
              <span>•</span>
              <span class="flex items-center gap-1"><i data-lucide="map-pin" class="w-4 h-4"></i> ${business.distance}</span>
              <span>•</span>
              <span class="badge badge-featured">${business.category}</span>
            `;
            // Recriar os ícones que acabaram de ser injetados
            lucide.createIcons(); 
          }
        }
      }
    });"""

new_script = """    // Lógica para carregar os dados dinâmicos da API baseados no ID da URL
    document.addEventListener('DOMContentLoaded', async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const id = parseInt(urlParams.get('id'));
      
      if (id) {
        try {
          const response = await fetch('/api/businesses/' + id);
          if (!response.ok) return;
          const business = await response.json();
          
          // Atualizar Título e Title da aba
          const titleEl = document.querySelector('.profile-title');
          if (titleEl) titleEl.textContent = business.name;
          document.title = business.name + " - O Que Procura?";
          
          // Atualizar Imagem Principal
          const imgEl = document.querySelector('.gallery-main');
          if (imgEl) {
            imgEl.src = business.image;
            imgEl.alt = business.name;
          }
          
          // Atualizar Meta Informações (Avaliação, Distância e Categoria)
          const metaContainer = document.querySelector('.profile-meta');
          if (metaContainer) {
            metaContainer.innerHTML = `
              <span class="flex items-center gap-1 font-medium"><i data-lucide="star" class="w-4 h-4 text-warning fill-warning"></i> ${business.rating}</span>
              <span>•</span>
              <span class="flex items-center gap-1"><i data-lucide="map-pin" class="w-4 h-4"></i> ${business.distance}</span>
              <span>•</span>
              <span class="badge badge-featured">${business.category}</span>
            `;
            // Recriar os ícones que acabaram de ser injetados
            lucide.createIcons(); 
          }
        } catch (e) {
          console.error(e);
        }
      }
    });"""

content = content.replace(old_script, new_script)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Profile.html updated!")
