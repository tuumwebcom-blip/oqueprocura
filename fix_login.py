import re

filepath = 'templates/login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace inputs with IDs
content = content.replace('<input type="email" class="form-control" placeholder="seu@email.com" required>', '<input type="email" id="login-email" class="form-control" placeholder="seu@email.com" required>')
content = content.replace('<input type="password" class="form-control" placeholder="••••••••" required>', '<input type="password" id="login-password" class="form-control" placeholder="••••••••" required>')

# Replace button
old_button = '<button type="submit" class="btn btn-primary w-full shadow-md">Entrar no Painel</button>'
new_button = '<button type="button" onclick="fazerLogin()" class="btn btn-primary w-full shadow-md">Entrar no Painel</button>'
content = content.replace(old_button, new_button)

script_to_add = """
  <script src="js/app.js"></script>
  <script>
    lucide.createIcons();

    async function fazerLogin() {
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        if(!email || !password) {
            alert('Preencha email e senha!');
            return;
        }

        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({email, password})
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

print("login.html logic added!")
