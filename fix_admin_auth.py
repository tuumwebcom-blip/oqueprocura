import re

filepath = 'templates/admin.html'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

old_script = """    // ID da empresa mockado para o Painel (fingindo que o id=1 fez login)
    const BUSINESS_ID = 1;"""

new_script = """    // Pega o ID da empresa logada no LocalStorage
    const BUSINESS_ID = localStorage.getItem('business_id');
    
    // Se não estiver logado, manda pro login
    if (!BUSINESS_ID) {
        window.location.href = '/login.html';
    }

    function fazerLogout() {
        localStorage.removeItem('business_id');
        window.location.href = '/login.html';
    }"""

content = content.replace(old_script, new_script)

# Adicionar função logout no menu
old_logout = """<a href="login.html" class="flex items-center gap-2 text-sm font-medium text-muted hover:text-danger transition-colors">"""
new_logout = """<a href="#" onclick="fazerLogout()" class="flex items-center gap-2 text-sm font-medium text-muted hover:text-danger transition-colors">"""
content = content.replace(old_logout, new_logout)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("admin.html auth linked!")
