filepath = 'templates/login.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix button
old_button = '<button type="submit" class="btn btn-primary w-full mt-4" style="padding: 0.875rem;">Entrar na minha conta</button>'
new_button = '<button type="button" onclick="fazerLogin()" class="btn btn-primary w-full mt-4" style="padding: 0.875rem;">Entrar na minha conta</button>'
content = content.replace(old_button, new_button)

# Fix script IDs
content = content.replace("document.getElementById('login-email')", "document.getElementById('email')")
content = content.replace("document.getElementById('login-password')", "document.getElementById('password')")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("login.html fixed!")
