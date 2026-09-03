import re

filepath = 'templates/profile.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I need to find the element containing the about text and give it an id
about_text_html = '<div class="about-text">'
new_about_text_html = '<div class="about-text" id="about-text-container">'
content = content.replace(about_text_html, new_about_text_html)

# I need to find the element containing the services and give it an id, and clear it or just target it
services_container = '<div class="mb-8">'
new_services_container = '<div class="mb-8" id="services-container">'
content = content.replace(services_container, new_services_container)

# Now I'll replace the script at the bottom to also render the description and services.
old_script = """          // Atualizar Meta Informações (Avaliação, Distância e Categoria)
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
        } catch (e) {"""

new_script = """          // Atualizar Meta Informações (Avaliação, Distância e Categoria)
          const metaContainer = document.querySelector('.profile-meta');
          if (metaContainer) {
            metaContainer.innerHTML = `
              <span class="flex items-center gap-1 font-medium"><i data-lucide="star" class="w-4 h-4 text-warning fill-warning"></i> ${business.rating}</span>
              <span>•</span>
              <span class="flex items-center gap-1"><i data-lucide="map-pin" class="w-4 h-4"></i> ${business.distance}</span>
              <span>•</span>
              <span class="badge badge-featured">${business.category}</span>
            `;
          }

          // Atualizar Sobre Nós
          const aboutEl = document.getElementById('about-text-container');
          if (aboutEl) {
              aboutEl.innerHTML = `<p>${business.about_text}</p>`;
          }

          // Atualizar Serviços
          const servicesEl = document.getElementById('services-container');
          if (servicesEl && business.services) {
              servicesEl.innerHTML = business.services.map(s => `
                <div class="service-item">
                  <div>
                    <h4 class="font-bold text-text-dark">${s.name}</h4>
                    <p class="text-sm text-muted">${s.description}</p>
                  </div>
                  <div class="font-bold text-text-dark">${s.price}</div>
                </div>
              `).join('');
          }
          
          // Recriar os ícones
          lucide.createIcons(); 
          
        } catch (e) {"""

content = content.replace(old_script, new_script)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Profile.html fully dynamic!")
