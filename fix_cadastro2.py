filepath = 'templates/cadastro.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix button
old_button = '<button type="submit" class="btn btn-primary w-full" style="padding: 0.875rem;">Criar minha conta</button>'
new_button = '<button type="button" onclick="fazerCadastro()" class="btn btn-primary w-full" style="padding: 0.875rem;">Criar minha conta</button>'
content = content.replace(old_button, new_button)

# Fix script IDs
content = content.replace("document.getElementById('cad-name')", "document.getElementById('company')")
content = content.replace("document.getElementById('cad-email')", "document.getElementById('email')")
content = content.replace("document.getElementById('cad-password')", "document.getElementById('password')")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("cadastro.html fixed!")
