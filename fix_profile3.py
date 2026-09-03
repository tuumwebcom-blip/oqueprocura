import re

filepath = 'templates/profile.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I need to replace the sticky contact card hardcoded data with dynamic IDs so JS can inject them.
# Replacing WhatsApp
old_whatsapp = '<button class="btn btn-whatsapp w-full flex items-center justify-center gap-2" style="padding: 1rem;">'
new_whatsapp = '<button class="btn btn-whatsapp w-full flex items-center justify-center gap-2" style="padding: 1rem;" id="btn-whatsapp">'
content = content.replace(old_whatsapp, new_whatsapp)

# Replacing Instagram
old_insta = '<button class="btn btn-instagram w-full flex items-center justify-center gap-2 mt-3" style="padding: 1rem;">'
new_insta = '<button class="btn btn-instagram w-full flex items-center justify-center gap-2 mt-3" style="padding: 1rem;" id="btn-instagram">'
content = content.replace(old_insta, new_insta)

# Replacing Address
old_address = '<li class="flex items-center gap-2 text-text"><i data-lucide="map-pin" class="w-4 h-4 text-muted"></i> Rua das Flores, 123 - Centro</li>'
new_address = '<li class="flex items-center gap-2 text-text" id="contact-address"><i data-lucide="map-pin" class="w-4 h-4 text-muted"></i> Endereço</li>'
content = content.replace(old_address, new_address)


old_script_bottom = """          // Atualizar Serviços"""
new_script_bottom = """
          // Atualizar Contatos
          const btnWhatsapp = document.getElementById('btn-whatsapp');
          if (btnWhatsapp) btnWhatsapp.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg> ` + (business.whatsapp || 'Conversar no WhatsApp');
          
          const btnInsta = document.getElementById('btn-instagram');
          if (btnInsta) btnInsta.innerHTML = `<i data-lucide="instagram" class="w-5 h-5"></i> ` + (business.instagram || 'Ver Instagram');
          
          const addressEl = document.getElementById('contact-address');
          if (addressEl) addressEl.innerHTML = `<i data-lucide="map-pin" class="w-4 h-4 text-muted"></i> ` + (business.address || business.distance);

          // Atualizar Serviços"""

content = content.replace(old_script_bottom, new_script_bottom)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Profile.html contact info fully dynamic!")
