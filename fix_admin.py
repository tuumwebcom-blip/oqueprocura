import re

filepath = 'templates/admin.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Add IDs to inputs
replacements = {
    '<input type="text" class="form-control" value="Estúdio Lente Clara">': '<input type="text" class="form-control" id="input-name" value="Carregando...">',
    '<select class="form-control">': '<select class="form-control" id="input-category">',
    '<textarea class="form-control" rows="2">Especialistas em capturar momentos únicos.</textarea>': '<textarea class="form-control" id="input-short" rows="2"></textarea>',
    '<textarea class="form-control" rows="4">Somos um estúdio de fotografia especializado em capturar os melhores momentos da sua vida...</textarea>': '<textarea class="form-control" id="input-about" rows="4"></textarea>',
    '<input type="text" class="form-control" value="(11) 99999-9999">': '<input type="text" class="form-control" id="input-whatsapp" value="">',
    '<input type="text" class="form-control" value="@estudiolenteclara">': '<input type="text" class="form-control" id="input-instagram" value="">',
    '<input type="text" class="form-control" value="Rua das Flores, 123 - Centro, São Paulo - SP">': '<input type="text" class="form-control" id="input-address" value="">',
    '''<button class="btn btn-primary shadow-sm" onclick="alert('Salvo com sucesso!')"><i data-lucide="save" class="w-4 h-4"></i> Salvar Alterações</button>''': '''<button class="btn btn-primary shadow-sm" onclick="salvarAlteracoes()"><i data-lucide="save" class="w-4 h-4"></i> Salvar Alterações</button>'''
}

for old, new in replacements.items():
    content = content.replace(old, new)

# Add script at the bottom
script_to_add = """
  <script>
    // ID da empresa mockado para o Painel (fingindo que o id=1 fez login)
    const BUSINESS_ID = 1;

    document.addEventListener('DOMContentLoaded', async () => {
      try {
        const response = await fetch('/api/businesses/' + BUSINESS_ID);
        const data = await response.json();
        
        document.getElementById('input-name').value = data.name || '';
        document.getElementById('input-category').value = data.category || '';
        document.getElementById('input-short').value = data.short_description || '';
        document.getElementById('input-about').value = data.about_text || '';
        document.getElementById('input-whatsapp').value = data.whatsapp || '';
        document.getElementById('input-instagram').value = data.instagram || '';
        document.getElementById('input-address').value = data.address || '';
        
      } catch(e) {
        console.error("Erro ao carregar dados", e);
      }
    });

    async function salvarAlteracoes() {
      const data = {
        name: document.getElementById('input-name').value,
        category: document.getElementById('input-category').value,
        short_description: document.getElementById('input-short').value,
        about_text: document.getElementById('input-about').value,
        whatsapp: document.getElementById('input-whatsapp').value,
        instagram: document.getElementById('input-instagram').value,
        address: document.getElementById('input-address').value
      };

      try {
        const response = await fetch('/api/businesses/' + BUSINESS_ID + '/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
        
        const result = await response.json();
        if (result.success) {
          alert('Salvo com sucesso! Abra seu perfil público para ver as mudanças.');
        }
      } catch(e) {
        alert('Erro ao salvar. Verifique o console.');
        console.error(e);
      }
    }
  </script>
</body>
"""

content = content.replace('</body>', script_to_add)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Admin.html dynamic!")
