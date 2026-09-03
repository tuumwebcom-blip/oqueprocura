import re

filepath = 'templates/cadastro.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace inputs with IDs
content = content.replace('<input type="text" class="form-control" placeholder="Nome do seu negócio" required>', '<input type="text" id="cad-name" class="form-control" placeholder="Nome do seu negócio" required>')
content = content.replace('<input type="email" class="form-control" placeholder="seu@email.com" required>', '<input type="email" id="cad-email" class="form-control" placeholder="seu@email.com" required>')
content = content.replace('<input type="password" class="form-control" placeholder="Crie uma senha segura" required>', '<input type="password" id="cad-password" class="form-control" placeholder="Crie uma senha segura" required>')

# Replace button
old_button = '<button type="submit" class="btn btn-primary w-full shadow-md" style="font-size: 1.1rem; padding: 1rem;">Criar minha conta e testar</button>'
new_button = '<button type="button" onclick="fazerCadastro()" class="btn btn-primary w-full shadow-md" style="font-size: 1.1rem; padding: 1rem;">Criar minha conta e testar</button>'
content = content.replace(old_button, new_button)

script_to_add = """
  <script src="js/app.js"></script>
  <script>
    lucide.createIcons();

    async function fazerCadastro() {
        const name = document.getElementById('cad-name').value;
        const email = document.getElementById('cad-email').value;
        const password = document.getElementById('cad-password').value;

        if(!name || !email || !password) {
            alert('Preencha todos os campos!');
            return;
        }

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({email, password, business_name: name})
            });
            const data = await res.json();

            if(data.success) {
                localStorage.setItem('business_id', data.business_id);
                window.location.href = '/admin.html';
            } else {
                alert(data.message);
            }
        } catch(e) {
            alert('Erro de comunicação com o servidor.');
        }
    }
  </script>
</body>
"""

content = content.replace("""  <script src="js/app.js"></script>
  <script>
    lucide.createIcons();
  </script>
</body>""", script_to_add)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("cadastro.html logic added!")
